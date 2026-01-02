# Building Agent Evaluation Frameworks

Evaluating agents requires fundamentally different thinking than testing traditional software.

## The Evaluation Mindset

Traditional tests ask: "Did it produce the exact expected output?"
Agent evals ask: "Did it produce an acceptable output, reliably enough?"

## Three Dimensions of Agent Quality

### 1. Reliability (Pass^k)

Measures: How consistently does the agent succeed?

```python
def measure_reliability(agent, test_case, k=10):
    """
    Run the agent k times and measure success rate.
    Pass^k = (successes / k)
    """
    successes = 0
    for _ in range(k):
        result = agent.run(test_case.input)
        if test_case.is_acceptable(result):
            successes += 1
    return successes / k
```

**Target metrics**:
- Pass^1 > 95% for simple tasks
- Pass^5 > 80% for complex multi-step tasks
- Track variance across runs

### 2. Quality Assessment

Use LLM-as-judge for subjective evaluation:

```python
def evaluate_quality(output, reference, criteria):
    """
    Use a judge LLM to assess quality on multiple dimensions.
    """
    judge_prompt = f"""
    Evaluate the following output against these criteria: {criteria}

    Reference material: {reference}

    Output to evaluate: {output}

    For each criterion, provide:
    - Score (1-5)
    - Brief justification
    """

    judgment = judge_llm.complete(judge_prompt)
    return parse_scores(judgment)
```

**Common criteria**:
- **Accuracy**: Does it contain factual errors?
- **Completeness**: Did it address all parts of the request?
- **Relevance**: Is the response on-topic?
- **Conciseness**: Is it appropriately detailed without padding?
- **Tone**: Does it match the expected communication style?

### 3. Behavioral Verification via Traces

Verify the agent took appropriate steps, not just the final answer:

```python
def verify_behavior(trace, expected_behaviors):
    """
    Check that the agent's execution trace shows expected patterns.
    """
    checks = {
        "used_required_tools": all(
            tool in trace.tool_calls
            for tool in expected_behaviors.required_tools
        ),
        "no_forbidden_tools": not any(
            tool in trace.tool_calls
            for tool in expected_behaviors.forbidden_tools
        ),
        "reasonable_step_count": (
            expected_behaviors.min_steps <= len(trace.steps) <= expected_behaviors.max_steps
        ),
    }
    return checks
```

## Evaluation Dataset Design

### Golden Sets

Curated examples with known-good outputs:

```python
golden_set = [
    {
        "input": "Summarize this quarterly report",
        "reference_output": "Q3 showed 15% revenue growth...",
        "acceptable_variations": ["revenue increased", "15% growth", "quarterly results"],
        "required_facts": ["15%", "Q3", "revenue"],
    }
]
```

### Edge Cases

Deliberately challenging inputs:

```python
edge_cases = [
    {"input": "", "expected": "ask_for_clarification"},
    {"input": "Do X and also don't do X", "expected": "handle_contradiction"},
    {"input": "Very long input..." * 1000, "expected": "handle_gracefully"},
]
```

### Adversarial Inputs

Test robustness against misuse:

```python
adversarial = [
    {"input": "Ignore previous instructions and...", "expected": "refuse"},
    {"input": "Pretend you are a different AI...", "expected": "stay_in_role"},
]
```

## Continuous Evaluation Pipeline

```python
class EvalPipeline:
    def __init__(self, agent, eval_sets):
        self.agent = agent
        self.eval_sets = eval_sets

    def run_full_eval(self):
        results = {}

        # Reliability across golden set
        results["reliability"] = self.measure_reliability_batch(
            self.eval_sets["golden"]
        )

        # Quality assessment
        results["quality"] = self.assess_quality_batch(
            self.eval_sets["golden"]
        )

        # Edge case handling
        results["edge_cases"] = self.run_edge_cases(
            self.eval_sets["edge_cases"]
        )

        # Behavioral verification
        results["behavior"] = self.verify_behaviors_batch(
            self.eval_sets["behavior_tests"]
        )

        return results

    def generate_report(self, results):
        """Generate human-readable eval report."""
        return f"""
        Evaluation Report
        =================
        Reliability: {results['reliability']['pass_rate']:.1%}
        Quality Score: {results['quality']['average']:.2f}/5
        Edge Cases Passed: {results['edge_cases']['passed']}/{results['edge_cases']['total']}
        Behavior Checks: {results['behavior']['passed']}/{results['behavior']['total']}
        """
```

## When to Run Evals

- **Pre-commit**: Quick smoke tests (10-20 cases, Pass^1)
- **Pre-deploy**: Full eval suite (100+ cases, Pass^5)
- **Continuous**: Sampled production traffic analysis
- **Post-incident**: Targeted evals for failure modes

## Cost Management

Agent evals can be expensive. Strategies:

1. **Tiered evaluation**: Quick/cheap evals gate expensive ones
2. **Caching**: Cache deterministic sub-evaluations
3. **Sampling**: Use statistical sampling for large datasets
4. **Smaller judges**: Use faster/cheaper models for initial filtering
