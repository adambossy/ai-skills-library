# OpenAI Agents SDK Integration

Guide for integrating custom tools with the OpenAI Agents SDK for ChatKit backends.

## FunctionTool Schema Issue

### The Problem

When using `@function_tool` decorator with generic signatures like `**kwargs: Any`, the decorator infers a schema that includes `additionalProperties: true`, which fails strict schema validation.

**Error message:**
```
additionalProperties should not be set for object types. This could be because
you're using an older version of Pydantic, or because you configured additional
properties to be allowed.
```

### The Solution

Create `FunctionTool` instances directly with explicit JSON schemas instead of using the `@function_tool` decorator.

## Tool Adapter Pattern

When you have existing tools with their own schema definitions, use an adapter to convert them to `FunctionTool` format:

```python
"""OpenAI Agents SDK adapter for custom tools."""
import json
from typing import Any

from agents.tool import FunctionTool
from agents.tool_context import ToolContext


class OpenAIAdapter:
    """Convert custom tools to OpenAI Agents SDK FunctionTool format."""

    def __init__(self, registry):
        self._registry = registry

    def adapt_tool(self, tool) -> FunctionTool:
        """
        Convert a tool with input_schema to FunctionTool.

        The tool must have:
        - name: str
        - description: str
        - input_schema: dict (JSON Schema format)
        - execute(**kwargs) -> dict
        """
        # Closure captures the specific tool instance
        async def on_invoke(ctx: ToolContext[Any], args_json: str) -> str:
            kwargs: dict[str, Any] = json.loads(args_json) if args_json else {}
            result = tool.execute(**kwargs)
            return json.dumps(result)

        return FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=dict(tool.input_schema),
            on_invoke_tool=on_invoke,
            strict_json_schema=True,
        )

    def adapt_all(self) -> list[FunctionTool]:
        """Convert all registered tools."""
        return [self.adapt_tool(tool) for tool in self._registry.all()]
```

## Tool Input Schema Format

Your tools should provide schemas in JSON Schema format:

```python
class MyTool:
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Does something useful"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The query to process",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs) -> dict:
        query = kwargs["query"]
        limit = kwargs.get("limit", 10)
        # ... implementation
        return {"status": "success", "results": [...]}
```

**Important:** Don't include `additionalProperties` in your schema. The strict schema validator will add `additionalProperties: false` automatically.

## Using Tools with ChatKit

```python
from agents import Agent, ModelSettings, Runner
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response


async def respond(self, thread, input_user_message, context):
    # Create adapter for your tools
    adapter = OpenAIAdapter(self._registry)
    tools = adapter.adapt_all()

    # Create agent with tools
    agent = Agent(
        name="MyAgent",
        instructions="You are a helpful assistant.",
        model="gpt-4o",
        tools=tools,
    )

    # Load and convert conversation history
    history_page = await self.store.load_thread_items(
        thread.id, after=None, limit=100, order="asc", context=context
    )
    history_items = list(history_page.data)
    history_items.append(input_user_message)

    agent_input = await simple_to_agent_input(history_items)

    # Run with streaming
    result = Runner.run_streamed(
        starting_agent=agent,
        input=agent_input,
    )

    # Stream response through ChatKit
    agent_context = AgentContext(
        thread=thread,
        store=self.store,
        request_context=context,
    )

    async for event in stream_agent_response(agent_context, result):
        yield event
```

## Conversation History

ChatKit provides `simple_to_agent_input()` to convert thread items to the format expected by `Runner.run_streamed()`:

```python
from chatkit.agents import simple_to_agent_input
from chatkit.types import ThreadItem

# Load history from store
history_page = await store.load_thread_items(
    thread_id=thread.id,
    after=None,
    limit=100,
    order="asc",      # Oldest first
    context=context,
)

# Convert to list and add current message
history_items: list[ThreadItem] = list(history_page.data)
history_items.append(input_user_message)

# Convert to agent input format
agent_input = await simple_to_agent_input(history_items)

# Pass to runner
result = Runner.run_streamed(
    starting_agent=agent,
    input=agent_input,  # Full history, not just current message
)
```

**Without this**, the agent sees only the current message and has no memory of the conversation.

## Model Settings

Configure model behavior with `ModelSettings`:

```python
from agents import Agent, ModelSettings
from openai.types.shared import Reasoning

agent = Agent(
    name="MyAgent",
    instructions="...",
    model="gpt-4o",
    tools=tools,
    model_settings=ModelSettings(
        reasoning=Reasoning(effort="medium"),
        verbosity="high",
    ),
)
```

## Common Agent Models

- `gpt-4o` - Good balance of capability and speed
- `gpt-4o-mini` - Faster, more economical
- `gpt-5.1` - Latest capabilities (if available)

## JSON Serialization in Tool Results

Tool results are serialized with `json.dumps()` before being passed back to the agent. **All values must be JSON-serializable.**

Common non-serializable types from database queries:

| Type | Fix |
|------|-----|
| `Decimal` | Convert to `float(value)` |
| `datetime` | Convert to `value.isoformat()` |
| `date` | Convert to `value.isoformat()` |
| `bytes` | Convert to `base64.b64encode(value).decode()` |
| `UUID` | Convert to `str(value)` |

**Example: SQL query tool with proper serialization:**

```python
from decimal import Decimal

def execute(self, **kwargs) -> dict:
    result = db.execute_raw_sql(kwargs["query"])
    rows = [dict(row._mapping) for row in result.fetchall()]

    # Convert non-JSON-serializable types
    for row in rows:
        for key, value in row.items():
            if hasattr(value, "isoformat"):
                row[key] = value.isoformat()
            elif isinstance(value, Decimal):
                row[key] = float(value)

    return {"status": "success", "rows": rows}
```

**Symptom if you miss this:**
```
Error running tool run_sql: Object of type Decimal is not JSON serializable
```

## Error Handling in Tools

Return error information in the result dict rather than raising exceptions:

```python
def execute(self, **kwargs) -> dict:
    try:
        # ... implementation
        return {"status": "success", "result": data}
    except SomeError as e:
        return {"status": "error", "error": str(e)}
```

This allows the agent to handle errors gracefully and potentially retry or take alternative actions.

## Debugging Tool Calls

Add logging to your tool adapter:

```python
async def on_invoke(ctx: ToolContext[Any], args_json: str) -> str:
    print(f"Tool called: {tool.name}")
    print(f"Arguments: {args_json}")

    kwargs = json.loads(args_json) if args_json else {}
    result = tool.execute(**kwargs)

    print(f"Result: {result}")
    return json.dumps(result)
```
