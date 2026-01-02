---
name: chatkit-integration
description: Integrate OpenAI ChatKit with Python backends using FastAPI and the OpenAI Agents SDK. Use when setting up ChatKit servers, fixing CORS issues, handling conversation history, or connecting React frontends to ChatKit backends.
---

# ChatKit Integration Guide

This skill provides patterns for integrating OpenAI ChatKit with Python backends (FastAPI) and React frontends.

## Quick Reference

For detailed guidance on specific topics:
- [BACKEND.md](BACKEND.md) - FastAPI server setup and common issues
- [FRONTEND.md](FRONTEND.md) - React/Next.js ChatKit client configuration
- [AGENTS.md](AGENTS.md) - OpenAI Agents SDK integration patterns

## Architecture Overview

```
┌─────────────────────┐     POST /chatkit      ┌─────────────────────┐
│   React Frontend    │ ────────────────────▶  │   FastAPI Backend   │
│  @openai/chatkit-   │                        │                     │
│       react         │  ◀──────────────────   │  chatkit (Python)   │
│                     │   SSE stream events    │  + agents SDK       │
└─────────────────────┘                        └─────────────────────┘
```

## Critical Issues and Solutions

### 1. FastAPI Type Annotations Issue

**Symptom**: 422 Unprocessable Entity with `"loc":["query","request"]`

**Cause**: `from __future__ import annotations` makes type annotations lazy strings, breaking FastAPI's parameter detection.

**Fix**: Remove the import from server files or use explicit type evaluation:

```python
# BAD - breaks FastAPI request detection
from __future__ import annotations

@app.post("/chatkit")
async def endpoint(req: Request):  # FastAPI sees "Request" string
    ...

# GOOD - works correctly
@app.post("/chatkit")
async def endpoint(req: Request):  # FastAPI sees actual Request type
    ...
```

### 2. CORS Configuration

**Symptom**: OPTIONS 405 or CORS blocked errors

**Fix**: Add CORSMiddleware with all local development origins:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. OpenAI Agents SDK Schema Error

**Symptom**: `additionalProperties should not be set for object types`

**Cause**: `@function_tool` decorator with `**kwargs: Any` generates invalid strict schema.

**Fix**: Create `FunctionTool` instances directly with explicit schemas. See [AGENTS.md](AGENTS.md).

### 4. Conversation History Not Persisting

**Symptom**: Agent doesn't remember previous messages

**Fix**: Load history from store and pass to agent. See [AGENTS.md](AGENTS.md).

### 5. Tool Results Not JSON-Serializable

**Symptom**: `Object of type Decimal is not JSON serializable`

**Cause**: Database queries return `Decimal`, `datetime`, etc. which `json.dumps()` can't serialize.

**Fix**: Convert non-serializable types before returning from tool. See [AGENTS.md](AGENTS.md).

### 6. No Hot Reloading in Development

**Symptom**: Must restart server manually after every code change

**Fix**: Use factory function pattern with uvicorn. See [BACKEND.md](BACKEND.md).

## Minimal Working Server

```python
"""Minimal ChatKit server."""
from collections.abc import AsyncIterator
from typing import Any

from agents import Agent, Runner
from chatkit.agents import AgentContext, simple_to_agent_input, stream_agent_response
from chatkit.server import ChatKitServer
from chatkit.types import ThreadItem, ThreadMetadata, ThreadStreamEvent, UserMessageItem


class MyChatKitServer(ChatKitServer[Any]):
    def __init__(self) -> None:
        from my_store import MyStore
        super().__init__(MyStore())

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: Any,
    ) -> AsyncIterator[ThreadStreamEvent]:
        if input_user_message is None:
            return

        agent = Agent(
            name="MyAgent",
            instructions="You are a helpful assistant.",
            model="gpt-4o",
            tools=[],  # Add your tools here
        )

        # Load conversation history
        history_page = await self.store.load_thread_items(
            thread.id, after=None, limit=100, order="asc", context=context
        )
        history_items: list[ThreadItem] = list(history_page.data)
        history_items.append(input_user_message)

        agent_input = await simple_to_agent_input(history_items)

        result = Runner.run_streamed(
            starting_agent=agent,
            input=agent_input,
        )

        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event
```

## Dependencies

```
openai-chatkit>=0.1.0
agents>=0.1.0
fastapi>=0.100.0
uvicorn>=0.23.0
```
