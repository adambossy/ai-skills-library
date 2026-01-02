---
name: agent-builder
description: Design and build AI agents that work reliably. Use when creating agents, debugging agent behavior, designing agent architectures, or reviewing agent code. Helps avoid common pitfalls engineers face when building probabilistic systems.
---

# Agent Builder

A guide for building reliable AI agents. This skill helps you avoid the common mistakes engineers make when transitioning from deterministic to probabilistic systems.

## Core Principle: Probabilistic Thinking

Traditional software engineering trains you to eliminate ambiguity. Agent engineering requires embracing uncertainty. The more experienced you are with deterministic systems, the harder this shift can be.

**Key insight**: You cannot "code away" probability—you must engineer systems resilient enough to handle it.

## The Five Principles

### 1. Text is the New State

**Problem**: Engineers instinctively convert natural language to structured types.

```python
# DON'T: Forcing semantic content into rigid structures
user_feedback = get_feedback()
approval = {
    "is_approved": True,  # Lost: "focus on the US market"
    "timestamp": now()
}
```

```python
# DO: Preserve the full semantic content
user_feedback = get_feedback()
context = {
    "feedback_text": user_feedback,  # "This plan looks good, but please focus on the US market"
    "timestamp": now()
}
# Let downstream agents extract nuanced intent from the text
```

**Why it matters**: Structured data loses semantic nuance. "Looks good but focus on US market" becomes `is_approved: true` and you've lost critical context. Store natural language alongside any structured data you need.

### 2. Hand Over Control

**Problem**: Engineers want to hard-code every interaction path.

```python
# DON'T: Rigid routing based on keywords
def route_request(user_input):
    if "schedule" in user_input:
        return calendar_agent()
    elif "email" in user_input:
        return email_agent()
    else:
        return default_agent()
```

```python
# DO: Let the LLM decide control flow
def handle_request(user_input, available_tools):
    return agent.run(
        prompt=user_input,
        tools=available_tools,
        # Agent decides which tools to use and in what order
    )
```

**Why it matters**: User intent evolves during conversations. Hard-coding paths defeats the purpose of having an agent. Trust the LLM to navigate non-linear interactions.

### 3. Errors are Just Inputs

**Problem**: Traditional software crashes on failures. Agents running for minutes and costing money cannot afford mid-execution crashes.

```python
# DON'T: Fail fast and crash
def process_data(data):
    result = external_api.call(data)  # Crashes on failure
    return result
```

```python
# DO: Feed errors back as context for recovery
def process_data(data, agent_context):
    try:
        result = external_api.call(data)
        return result
    except Exception as e:
        # Give the agent the error as additional context
        agent_context.add_message(
            role="system",
            content=f"API call failed with: {str(e)}. Consider alternative approaches or retry with modified parameters."
        )
        return agent.continue_with_context(agent_context)
```

**Why it matters**: A 5-minute agent run costing $0.50 shouldn't crash halfway through. Errors become information the agent can use to adapt its approach.

### 4. From Unit Tests to Evals

**Problem**: You cannot unit test reasoning with binary assertions. "Write a summary" has infinite valid outputs.

```python
# DON'T: Traditional unit tests for agent outputs
def test_summary():
    result = agent.summarize(document)
    assert result == "The document discusses..."  # Fragile, will break
```

```python
# DO: Evaluation frameworks measuring quality
def eval_summary():
    result = agent.summarize(document)

    # Reliability: Does it work consistently?
    pass_rate = run_n_times(agent.summarize, document, n=10)

    # Quality: LLM-as-judge assessment
    quality_score = judge_llm.evaluate(
        criteria=["accuracy", "completeness", "conciseness"],
        output=result,
        reference=document
    )

    # Tracing: Verify intermediate steps
    trace = agent.get_trace()
    assert "read_document" in trace.tool_calls

    return {"pass_rate": pass_rate, "quality": quality_score}
```

**What to measure**:
- **Reliability (Pass^k)**: How consistently does it produce acceptable results?
- **Quality**: Use LLM judges to assess helpfulness, accuracy, tone
- **Tracing**: Verify intermediate steps, not just final output

### 5. Design Agent-Friendly Interfaces

**Problem**: Agents are literal interpreters—they lack implicit human context.

```python
# DON'T: Ambiguous parameter names
def send(e, s, b):
    """Send a message."""
    pass
```

```python
# DO: Verbose, self-documenting interfaces
def send_email_message(
    recipient_email_address: str,
    email_subject_line: str,
    email_body_content: str
) -> dict:
    """
    Send an email message to a single recipient.

    Args:
        recipient_email_address: The full email address of the recipient (e.g., "user@example.com")
        email_subject_line: The subject line that will appear in the recipient's inbox
        email_body_content: The main text content of the email (plain text, not HTML)

    Returns:
        dict with keys:
            - success (bool): Whether the email was sent successfully
            - message_id (str): Unique identifier for the sent message
            - error (str | None): Error message if sending failed
    """
    pass
```

**Key advantage**: Agents read tool definitions and adapt automatically. Well-documented tools work immediately; poorly documented ones cause confusion and errors.

## Agent Architecture Checklist

When designing an agent, verify each component:

### State Management
- [ ] Natural language context preserved (not just structured data)
- [ ] Conversation history accessible to the agent
- [ ] Intermediate results stored for recovery

### Control Flow
- [ ] Single entry point with LLM-driven routing
- [ ] Tools/capabilities clearly defined and documented
- [ ] No hard-coded intent matching (unless absolutely necessary)

### Error Handling
- [ ] Errors caught and fed back as context
- [ ] Retry logic with adaptive parameters
- [ ] Graceful degradation paths

### Evaluation
- [ ] Eval suite measuring reliability and quality
- [ ] LLM-as-judge for subjective outputs
- [ ] Tracing for intermediate step verification

### Tool Design
- [ ] Verbose, descriptive parameter names
- [ ] Comprehensive docstrings with examples
- [ ] Clear return type documentation

## Common Anti-Patterns

### Over-Engineering Control Flow
**Symptom**: Complex routing logic, state machines, intent classifiers
**Fix**: Trust the LLM to route. Provide clear tool descriptions.

### Structured Data Obsession
**Symptom**: Converting every LLM output to JSON/Pydantic immediately
**Fix**: Keep text as text when semantic meaning matters.

### Crash-Happy Error Handling
**Symptom**: Exceptions that halt the entire agent run
**Fix**: Catch errors, add them to context, let the agent adapt.

### Binary Test Assertions
**Symptom**: `assert output == expected` for free-form text
**Fix**: Use evals with LLM judges and reliability metrics.

### Cryptic Tool Interfaces
**Symptom**: Short parameter names, missing docstrings
**Fix**: Write tools as if explaining to a literal-minded new hire.

## When NOT to Use an Agent

Agents are not always the answer. Use traditional code when:

- The task is fully deterministic with known inputs/outputs
- Latency requirements are sub-second
- Cost per operation must be near-zero
- Auditability requires exact reproducibility
- The domain has no ambiguity to resolve

## Additional Resources

For detailed guidance on specific topics:
- [EVALS.md](EVALS.md) - Building evaluation frameworks
- [TOOLS.md](TOOLS.md) - Designing agent-friendly tools
- [PATTERNS.md](PATTERNS.md) - Common agent architecture patterns
