# Common Agent Architecture Patterns

Proven patterns for structuring agents effectively.

## Pattern 1: Single-Agent with Tools

The simplest architecture. One agent with access to multiple tools.

```
┌─────────────────────────────────────────┐
│                 Agent                    │
│  ┌─────────────────────────────────┐    │
│  │         LLM Reasoning           │    │
│  └─────────────────────────────────┘    │
│              │                          │
│  ┌───────────┼───────────┐              │
│  ▼           ▼           ▼              │
│ Tool A    Tool B      Tool C            │
└─────────────────────────────────────────┘
```

**When to use**:
- Tasks that can be completed with a clear set of tools
- Single-domain problems
- Low complexity workflows

**Implementation**:

```python
agent = Agent(
    model="your-llm",
    tools=[
        search_documents,
        read_file,
        write_file,
        send_email
    ],
    system_prompt="You are a helpful assistant..."
)

response = agent.run(user_input)
```

## Pattern 2: Router Agent

One agent decides which specialized agent handles the task.

```
                    ┌─────────────┐
                    │   Router    │
                    │   Agent     │
                    └─────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Sales     │   │   Support   │   │   Billing   │
│   Agent     │   │   Agent     │   │   Agent     │
└─────────────┘   └─────────────┘   └─────────────┘
```

**When to use**:
- Multiple distinct domains
- Specialized knowledge per domain
- Need to contain context/tools per domain

**Implementation**:

```python
router = Agent(
    model="your-llm",
    tools=[route_to_sales, route_to_support, route_to_billing],
    system_prompt="""
    Analyze the user's request and route to the appropriate specialist:
    - Sales: Pricing, quotes, product inquiries
    - Support: Technical issues, bugs, how-to questions
    - Billing: Invoices, payments, subscription changes
    """
)

def route_to_sales(context: str) -> str:
    """Route to sales specialist with conversation context."""
    return sales_agent.run(context)
```

## Pattern 3: Pipeline Agent

Sequential agents, each handling one step.

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Extract │ -> │ Analyze │ -> │ Decide  │ -> │ Execute │
│  Agent  │    │  Agent  │    │  Agent  │    │  Agent  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
```

**When to use**:
- Well-defined sequential workflows
- Each step has distinct requirements
- Need checkpoints between steps

**Implementation**:

```python
def process_document(document):
    # Step 1: Extract key information
    extracted = extract_agent.run(
        f"Extract key entities and facts from: {document}"
    )

    # Step 2: Analyze the extracted information
    analysis = analyze_agent.run(
        f"Analyze these extracted facts: {extracted}"
    )

    # Step 3: Decide on action
    decision = decide_agent.run(
        f"Based on this analysis, recommend an action: {analysis}"
    )

    # Step 4: Execute the decision
    result = execute_agent.run(
        f"Execute this decision: {decision}"
    )

    return result
```

## Pattern 4: Supervisor Agent

One agent orchestrates others, maintaining overall context.

```
            ┌─────────────────┐
            │   Supervisor    │
            │     Agent       │
            │  (maintains     │
            │   context)      │
            └────────┬────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
    ▼                ▼                ▼
┌────────┐      ┌────────┐      ┌────────┐
│ Worker │      │ Worker │      │ Worker │
│   A    │      │   B    │      │   C    │
└────────┘      └────────┘      └────────┘
```

**When to use**:
- Complex tasks requiring coordination
- Need to synthesize results from multiple workers
- Iterative refinement required

**Implementation**:

```python
class Supervisor:
    def __init__(self):
        self.context = []
        self.workers = {
            "research": research_agent,
            "write": writing_agent,
            "review": review_agent
        }

    def run(self, task):
        # Plan the work
        plan = self.plan_agent.run(f"Create a plan for: {task}")

        for step in plan.steps:
            # Delegate to appropriate worker
            worker = self.workers[step.type]
            result = worker.run(step.instructions)

            # Maintain context
            self.context.append({
                "step": step,
                "result": result
            })

            # Check if we need to adjust the plan
            if self.needs_replanning(result):
                plan = self.replan(plan, result)

        # Synthesize final result
        return self.synthesize(self.context)
```

## Pattern 5: Critic-Actor

One agent acts, another critiques and requests improvements.

```
          ┌──────────────────────────────────┐
          │                                  │
          ▼                                  │
    ┌───────────┐        ┌───────────┐      │
    │   Actor   │ -----> │  Critic   │ ─────┘
    │   Agent   │        │   Agent   │   (feedback loop)
    └───────────┘        └───────────┘
         │
         ▼
    Final Output
    (when approved)
```

**When to use**:
- Quality is critical
- Self-improvement needed
- Tasks with clear quality criteria

**Implementation**:

```python
def actor_critic_loop(task, max_iterations=3):
    attempt = actor_agent.run(task)

    for i in range(max_iterations):
        critique = critic_agent.run(f"""
            Task: {task}
            Attempt: {attempt}

            Evaluate this attempt. If acceptable, respond with "APPROVED".
            Otherwise, provide specific feedback for improvement.
        """)

        if "APPROVED" in critique:
            return attempt

        # Incorporate feedback
        attempt = actor_agent.run(f"""
            Original task: {task}
            Previous attempt: {attempt}
            Feedback: {critique}

            Improve your response based on the feedback.
        """)

    return attempt  # Return best effort after max iterations
```

## Pattern 6: Tool-Making Agent

Agent creates new tools as needed.

```
┌─────────────────────────────────────────┐
│              Meta Agent                  │
│  ┌─────────────────────────────────┐    │
│  │       Tool Generator            │    │
│  └─────────────────────────────────┘    │
│              │                          │
│              ▼                          │
│  ┌─────────────────────────────────┐    │
│  │       Dynamic Tool Pool         │    │
│  │  [Tool A] [Tool B] [New Tool]   │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**When to use**:
- Highly variable tasks
- Need for custom data transformations
- Can't anticipate all required tools

**Implementation**:

```python
def create_tool(agent, tool_spec):
    """Agent generates a new tool based on specification."""
    code = agent.run(f"""
        Create a Python function that:
        {tool_spec}

        Return only the function code, properly formatted.
    """)

    # Safely execute and register the new tool
    tool_fn = safe_exec(code)
    agent.register_tool(tool_fn)
    return tool_fn
```

## Choosing a Pattern

| Pattern | Complexity | Best For |
|---------|------------|----------|
| Single-Agent | Low | Simple tasks, clear tool set |
| Router | Medium | Multi-domain, specialized knowledge |
| Pipeline | Medium | Sequential workflows, checkpoints |
| Supervisor | High | Complex coordination, synthesis |
| Critic-Actor | Medium | Quality-critical outputs |
| Tool-Making | High | Highly variable requirements |

## Combining Patterns

Patterns can be combined:

```
Router -> Pipeline of (Supervisor managing Critic-Actor loops)
```

Start simple. Add complexity only when simpler patterns fail.
