# You Should Write a Genomics Agent

## Overview

This tutorial adapts the [Fly.io "Everyone Write an Agent"](https://fly.io/blog/everyone-write-an-agent/) blog post for genomics applications. You'll learn:

1. **Basic agent architecture** - Context arrays and LLM API calls
2. **Genomics tools** - Variant filtering and interval operations
3. **Tool autonomy** - How LLMs decide which tools to call
4. **Subagents** - Specialized agents with separate contexts
5. **Context engineering** - Token management strategies

The entire pattern is surprisingly simple: ~100 lines of code for a working multi-agent genomics system.

## It's Incredibly Easy

LLM agents are surprisingly simple. I'm not even going to bother explaining what an agent is—let's just jump into the code.

```python
from openai import OpenAI

client = OpenAI()
context = []

def call():
    return client.chat.completions.create(model="gpt-4", messages=context)

def process(line):
    context.append({"role": "user", "content": line})
    response = call()
    assistant_message = response.choices[0].message.content
    context.append({"role": "assistant", "content": assistant_message})
    return assistant_message
```

This implements ChatGPT in ~10 lines. The dreaded "context window" is just a list of dictionaries.

## Adding Genomics Tools

Tools are easy. Here's a tool to filter variants by quality score:

```python
import pandas as pd

tools = [{
    "type": "function",
    "function": {
        "name": "filter_variants",
        "description": "Filter variants by quality score from a VCF-like dataframe",
        "parameters": {
            "type": "object",
            "properties": {
                "min_quality": {
                    "type": "number",
                    "description": "Minimum QUAL score"
                },
            },
            "required": ["min_quality"],
        },
    }
}]

# Sample variant data
variants = pd.DataFrame({
    'CHROM': ['chr1', 'chr1', 'chr2', 'chr2'],
    'POS': [100, 200, 150, 300],
    'QUAL': [30, 15, 45, 20]
})

def filter_variants(min_quality):
    filtered = variants[variants['QUAL'] >= min_quality]
    return filtered.to_string()
```

Now let's wire it in:

```python
def call():
    return client.chat.completions.create(
        model="gpt-4",
        messages=context,
        tools=tools
    )

def tool_call(function_name, arguments):
    if function_name == "filter_variants":
        result = filter_variants(**arguments)
    return result

def process(line):
    context.append({"role": "user", "content": line})
    response = call()
    
    # Handle tool calls
    while response.choices[0].message.tool_calls:
        tool_calls = response.choices[0].message.tool_calls
        context.append(response.choices[0].message)
        
        for tc in tool_calls:
            result = tool_call(tc.function.name, json.loads(tc.function.arguments))
            context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        
        response = call()
    
    assistant_message = response.choices[0].message.content
    context.append({"role": "assistant", "content": assistant_message})
    return assistant_message
```

Try it:

```
> Show me high-quality variants
tool call: filter_variants(min_quality=30)
>>> Here are the high-quality variants (QUAL ≥ 30):
chr1:100 (QUAL=30)
chr2:150 (QUAL=45)
```

## A More Interesting Example: Interval Operations

Here's where it gets fun. Let's add bioframe for genomic interval operations:

```python
import bioframe as bf

tools.append({
    "type": "function",
    "function": {
        "name": "intersect_intervals",
        "description": "Find overlapping genomic intervals between two sets",
        "parameters": {
            "type": "object",
            "properties": {
                "set1_name": {"type": "string", "description": "Name of first interval set"},
                "set2_name": {"type": "string", "description": "Name of second interval set"}
            },
            "required": ["set1_name", "set2_name"],
        },
    }
})

# Sample genomic intervals
genes = pd.DataFrame({
    'chrom': ['chr1', 'chr1', 'chr2'],
    'start': [100, 500, 200],
    'end': [300, 700, 400],
    'name': ['GENE1', 'GENE2', 'GENE3']
})

peaks = pd.DataFrame({
    'chrom': ['chr1', 'chr1', 'chr2'],
    'start': [250, 600, 180],
    'end': [350, 650, 220],
    'name': ['PEAK1', 'PEAK2', 'PEAK3']
})

interval_sets = {'genes': genes, 'peaks': peaks}

def intersect_intervals(set1_name, set2_name):
    set1 = interval_sets[set1_name]
    set2 = interval_sets[set2_name]
    overlaps = bf.overlap(set1, set2, how='inner')
    return overlaps.to_string()
```

Try it:

```
> Which genes overlap with ChIP-seq peaks?
tool call: intersect_intervals("genes", "peaks")
>>> GENE1 overlaps with PEAK1 (chr1:250-300)
    GENE2 overlaps with PEAK2 (chr1:600-650)
    GENE3 overlaps with PEAK3 (chr2:200-220)
```

**This is the key insight**: You didn't write code to figure out which tool to call or how many times. The LLM did that. It understood your genomics question and mapped it to the available tools.

## Context Engineering Is Real

"Prompt Engineering" sounds silly. But "Context Engineering" is just programming.

You have a fixed token budget. Each message, tool, and output consumes tokens. Past a threshold, the system gets nondeterministically dumber.

Your options:
- **Sub-agents**: New context array, different tools for each. One agent finds variants, another annotates them.
- **Summarization**: Compress intermediate results through the LLM before continuing.
- **Selective context**: Keep only recent messages plus a summary of earlier ones.

## Subagents: Trivially Simple

A subagent is just a separate context array. That's it.

```python
# Main agent
main_context = []
main_tools = [{"function": {"name": "annotate_variant", ...}}]

# Subagent (separate context!)
annotation_context = [{
    "role": "system",
    "content": "You're a variant annotation expert. Be concise."
}]
annotation_tools = [{"function": {"name": "predict_impact", ...}}]

def annotate_variant(chrom, pos, ref, alt):
    """This is the subagent - just uses a different context array"""
    variant_id = f"{chrom}:{pos}:{ref}>{alt}"
    annotation_context.append({
        "role": "user",
        "content": f"What is the predicted impact of {variant_id}?"
    })
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=annotation_context,  # Different context!
        tools=annotation_tools         # Different tools!
    )
    
    # Handle subagent tool calls (same pattern as main agent)
    while response.choices[0].message.tool_calls:
        annotation_context.append(response.choices[0].message)
        for tc in response.choices[0].message.tool_calls:
            result = predict_impact(**json.loads(tc.function.arguments))
            annotation_context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        response = client.chat.completions.create(
            model="gpt-4",
            messages=annotation_context,
            tools=annotation_tools
        )
    
    result = response.choices[0].message.content
    annotation_context.append({"role": "assistant", "content": result})
    return result
```

Now add it to your main agent's tools:

```python
main_tools.append({
    "type": "function",
    "function": {
        "name": "annotate_variant",
        "description": "Get functional annotation from specialized subagent",
        "parameters": {
            "type": "object",
            "properties": {
                "chrom": {"type": "string"},
                "pos": {"type": "integer"},
                "ref": {"type": "string"},
                "alt": {"type": "string"}
            },
            "required": ["chrom", "pos", "ref", "alt"]
        }
    }
})
```

Try it:
```
> Tell me about the pathogenic variants
[Tool: filter_variants(min_quality=30)]
[Tool: annotate_variant(chrom='chr1', pos=100, ref='A', alt='T')]
  → Calling annotation subagent...
  → Subagent calls predict_impact
>>> Found 1 high-quality pathogenic variant:
chr1:100 A>T is a pathogenic missense mutation in BRCA1 (QUAL=30)

Final context sizes:
  Main agent: 5 messages
  Annotation subagent: 3 messages
```

### Why Use Subagents?

**1. Token Management**
```python
# Without subagent: Everything in one context
main_context = [
    # 10 messages about filtering
    # 20 messages about annotation details
    # 15 messages about interpretation
]  # Total: 45 messages → hits token limit!

# With subagents: Focused contexts
main_context = [...]        # 10 messages (coordination only)
annotation_context = [...]  # 20 messages (specialist work)
```

**2. Separation of Concerns**
```python
main_tools = ["filter_variants", "intersect_intervals", "call_annotator"]
annotator_tools = ["predict_impact", "query_clinvar", "check_conservation"]
reporter_tools = ["format_clinical_report", "cite_literature"]
```

**3. Security Boundaries**
```python
readonly_tools = ["read_vcf", "query_database"]
analysis_tools = ["write_report", "execute_pipeline"]  # Separate subagent!
```

### When to Use Subagents

**Use subagents when:**
- Different workflow stages need different tools
- Token limits become an issue
- You want to isolate complex/expensive operations
- Security separation matters (read-only vs write access)

**Don't use subagents when:**
- A single agent works fine
- You're just starting out (keep it simple!)
- The overhead isn't worth it

### Practical Example: Variant Analysis Pipeline

**Without subagents (everything in one context):**
```python
context = []
tools = [
    "filter_variants",
    "predict_impact",
    "query_clinvar",
    "check_conservation",
    "assess_pathogenicity",
    "format_report",
    "cite_literature"
]

> "Analyze these 100 variants"
# Agent must:
# 1. Filter (adds 10 tool results to context)
# 2. Annotate each (adds 100 × 3 tool results to context)
# 3. Generate report (context now has 310+ messages)
# → Hits token limit, loses context, fails
```

**With subagents (specialized contexts):**
```python
# Main agent: Orchestration only
main_context = []
main_tools = ["filter_variants", "call_annotator", "call_reporter"]

# Annotation subagent: Specialized for variant details
annotation_context = []
annotation_tools = ["predict_impact", "query_clinvar", "check_conservation"]

# Reporting subagent: Specialized for output formatting
report_context = []
report_tools = ["format_report", "cite_literature"]

> "Analyze these 100 variants"
# Main agent: 5 messages (coordination)
# Annotation subagent: Processes 100 variants, but only returns summaries
# Reporting subagent: 8 messages (formatting)
# → Total: Each context stays small, pipeline completes successfully
```

### The Key Insight

From the original article: "People make a huge deal out of Claude Code's sub-agents, but you can see now how trivial they are to implement: just a new context array."

It's literally:
```python
context_1 = []  # Main agent
context_2 = []  # Annotation subagent
context_3 = []  # Reporting subagent
```

Everything else is the same agent loop you already wrote.

### Subagent Flow Diagram

```
User: "Find pathogenic variants"
    ↓
┌─────────────────────────────────┐
│   MAIN AGENT (context_1)        │
│   Tools: [filter, call_subagent]│
└─────────────────────────────────┘
    ↓ calls tool: filter_variants
    ↓ result: chr1:100, chr2:150
    ↓ calls tool: annotate_variant(chr1:100)
    ↓
    ┌─────────────────────────────────┐
    │ ANNOTATION SUBAGENT (context_2) │
    │ Tools: [predict_impact, clinvar]│
    └─────────────────────────────────┘
        ↓ calls predict_impact
        ↓ result: "pathogenic"
        ↓ returns: "Pathogenic missense in BRCA1"
    ↓
    ← result added to main context
    ↓
    Main agent synthesizes final answer
    ↓
User: "chr1:100 is pathogenic (BRCA1)"

Key: Each agent maintains separate conversation history
```

See `genomics_agent_with_subagent.py` for a complete working example with integrated subagent.

## Open Problems in Genomics Agents

Agent design for genomics involves fascinating engineering tradeoffs:

- **Structured vs. exploratory**: Should your agent follow a fixed QC pipeline, or explore the data freely?
- **Ground truth**: How do you ensure your agent correctly identifies high-impact variants rather than just completing the task?
- **Multi-stage workflows**: What's the best way to chain variant calling → filtering → annotation → interpretation? Single agent or subagents?
- **Token allocation**: Do you load entire VCFs into context, or query them incrementally?
- **Subagent orchestration**: When should the main agent delegate to specialists? How do subagents communicate results back?

The beauty is these questions are approachable. Each productive iteration takes 30 minutes, not months. A solo researcher can compete with funded startups.

## Try It

You now understand agents at a fundamental level. The entire architecture is:
1. Context array (list of dicts)
2. LLM API call
3. Tool execution loop
4. Subagents (just more context arrays!)

Everything else—chain-of-thought, RAG, multi-agent systems—is just clever context management.

### Working Examples

**Basic agent:**
```bash
python genomics_agent.py
```

**With subagent:**
```bash
python genomics_agent_with_subagent.py
```

**Minimal subagent demo:**
```bash
python subagent_example.py
```

### Extend It

Build something. Give your agent access to:
- `pysam` for BAM/VCF files
- `scikit-allel` for population genetics
- `biopython` for sequence analysis

Create subagents for:
- Quality control (separate QC context and tools)
- Annotation (databases and prediction tools)
- Clinical reporting (interpretation and formatting)

See what happens when you ask:
- "Find interesting structural variants" (exploratory)
- "Check for deletions in BRCA1" (structured)
- "What are the pathogenic variants in these samples?" (requires coordination between subagents)

The dial between explicit programming and LLM autonomy is yours to turn. Make it too explicit and you've just written a script. Turn it to 11 and it'll surprise you (maybe to death).

But you won't really understand this technology until you've built something with it.
