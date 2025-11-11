# A More Interesting Example: Adaptive Exploration

Here's where it gets fun. Let's see tool calling that **can't be achieved with traditional workflows**.

## The Problem with Basic Examples

Our previous examples showed the agent calling tools. But you could hardcode that:

```python
# This is just a fancy function call
variants = filter_variants(min_quality=30)
```

**The real power:** When the agent **explores** based on what it finds.

## Adaptive Investigation

```python
import json
from openai import OpenAI

client = OpenAI()
context = []

# Toy genomics database
DISEASE_GENES = {
    'epilepsy': ['SCN1A', 'KCNQ2', 'GABRA1'],
    'autism': ['TSC1', 'MECP2']
}

VARIANTS = {
    'SCN1A': 'chr2:166245425:T:C (rare, missense)',
    'TSC1': 'chr9:135768983:G:T (rare, frameshift)'
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_disease_genes",
            "description": "Find genes associated with a disease",
            "parameters": {
                "type": "object",
                "properties": {
                    "disease": {"type": "string", "description": "Disease name"}
                },
                "required": ["disease"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_variant",
            "description": "Check if patient has variants in a gene",
            "parameters": {
                "type": "object",
                "properties": {
                    "gene": {"type": "string", "description": "Gene symbol"}
                },
                "required": ["gene"]
            }
        }
    }
]

def search_disease_genes(disease):
    genes = DISEASE_GENES.get(disease, [])
    return json.dumps({"disease": disease, "genes": genes})

def check_variant(gene):
    variant = VARIANTS.get(gene, "none found")
    return json.dumps({"gene": gene, "variant": variant})
```

Wire it in (same pattern as before):

```python
def tool_call(name, args):
    funcs = {
        "search_disease_genes": search_disease_genes,
        "check_variant": check_variant
    }
    return funcs[name](**args)

def process(query):
    context.append({"role": "user", "content": query})
    response = client.chat.completions.create(
        model="gpt-4",
        messages=context,
        tools=tools
    )
    
    while response.choices[0].message.tool_calls:
        context.append(response.choices[0].message)
        for tc in response.choices[0].message.tool_calls:
            result = tool_call(tc.function.name, json.loads(tc.function.arguments))
            context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        response = client.chat.completions.create(
            model="gpt-4",
            messages=context,
            tools=tools
        )
    
    answer = response.choices[0].message.content
    context.append({"role": "assistant", "content": answer})
    return answer
```

Now try this:

```
> Patient has epilepsy. Find the genetic cause.
```

Watch what happens:

```
tool call 1: search_disease_genes({"disease": "epilepsy"})
tool call 2: check_variant({"gene": "SCN1A"})
tool call 3: check_variant({"gene": "KCNQ2"})
tool call 4: check_variant({"gene": "GABRA1"})

>>> Found causative variant in SCN1A: chr2:166245425:T:C (rare missense).
This is a known Dravet syndrome mutation. The other epilepsy genes (KCNQ2, 
GABRA1) show no variants in this patient.
```

## This is fucking nuts

Do you see how nuts this is?

**You didn't write code to:**
- Search for epilepsy genes first
- Check each gene from the search results  
- Stop after checking all of them

The agent figured out a **multi-step investigation workflow**:
1. "I need to find epilepsy-associated genes" → searches
2. "Got 3 genes back, let me check each one" → checks all 3
3. "Found a variant in SCN1A, that's the answer" → synthesizes

**Could you hardcode this?** No! Because:

```python
# This doesn't work:
def investigate_epilepsy():
    genes = ["SCN1A", "KCNQ2", "GABRA1"]  # ← Where did this list come from?
    for gene in genes:
        check_variant(gene)
```

The list of genes **comes from the search tool**. You don't know it in advance.

## Follow-Up Questions Work Too

```
> Now check for autism-related variants too.

tool call 5: search_disease_genes({"disease": "autism"})
tool call 6: check_variant({"gene": "TSC1"})
tool call 7: check_variant({"gene": "MECP2"})

>>> Also found TSC1 variant: chr9:135768983:G:T (rare frameshift).
Patient may have tuberous sclerosis complex, which causes both epilepsy 
and autism.
```

The agent:
- Remembered the context (we're investigating a patient)
- Searched for a different disease
- Checked those genes too
- Connected the findings

**This is exploration, not execution.**

## Why This Matters

From the fly.io article:

> "Did you notice where I wrote the loop to ping multiple Google properties? 
> Yeah, neither did I."

**In genomics:**

> "Did you notice where I wrote code to search literature, then check those 
> specific genes, then decide when to stop exploring? Yeah, neither did I."

This is the key insight of agents: **You're programming tools, not workflows.**

The agent decides:
- What to investigate
- How deep to go
- When it has an answer
- What to do next

## When This Actually Helps

### ❌ Don't need an agent:
```python
"Filter variants with QUAL > 30"
→ Just call filter_variants(30)
```

### ✅ Need an agent:
```python
"Why does this patient have seizures?"
→ Searches for seizure-related genes
→ Checks those genes  
→ Explores connections
→ Can't be predetermined
```

### ✅ Need an agent:
```python
"Debug: Why is coverage low in chr17:41244748?"
→ Checks mappability
→ Checks GC content
→ Looks for structural variants
→ Path depends on findings
```

## The Real Difference

**Traditional pipeline:**
```
Input → [Fixed Steps] → Output
```
You hardcode the workflow.

**Adaptive agent:**
```
Question → [Exploration] → [More Exploration] → Answer
                ↓               ↓
            Findings determine next steps
```
The agent discovers the workflow.

## Try It

See `minimal_agent.py` for a complete 40-line example, or `adaptive_agent.py` for a fuller implementation with more tools.

The pattern is always the same:
1. Give the agent tools
2. Ask an open-ended question
3. Watch it figure out the investigation

**This is the key insight**: You didn't write the loop. The LLM did that. It understood your question and mapped it to an adaptive sequence of tool calls.

When you start combining this with real genomics tools—`pysam`, gnomAD APIs, literature search—you get genuinely exploratory analysis that responds to what it finds in your data.

The dial between explicit programming and LLM autonomy is yours to turn. Make it too explicit and you've just written a script. Turn it to 11 and it'll surprise you (maybe to death).

But you won't really understand this technology until you've built something with it.
