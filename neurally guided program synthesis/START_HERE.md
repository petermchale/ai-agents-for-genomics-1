# Getting Started

You asked for genomics examples showing **repeated tool calling that couldn't be achieved by standard workflows**. Here's what you got:

## The Core Insight

**Your original critique was spot-on:** The fly.io article's "ping Google 3 times" example could be hardcoded:

```python
for host in ["google.com", "www.google.com", "8.8.8.8"]:
    ping(host)
```

**The real power** is when you **can't** hardcode it:

```python
> "Patient has epilepsy. Find the genetic cause."

# Agent discovers genes from database → searches them → stops when found
# You cannot write this as a fixed loop
```

## Quick Start (5 minutes)

### 1. Read This
[`key_insight.md`](computer:///mnt/user-data/outputs/key_insight.md) - Shows the difference between workflows and adaptive exploration

### 2. Run This
```bash
pip install openai
export OPENAI_API_KEY="your-key"
python minimal_agent.py
```

Watch the agent:
- Search for disease genes (discovers what to check)
- Check each gene from results (adapts to findings)
- Stop when it finds an answer (not predetermined)

**You didn't write that logic. The agent did.**

### 3. Drop This In Your Tutorial
[`tutorial_section.md`](computer:///mnt/user-data/outputs/tutorial_section.md) - Complete section showing adaptive exploration with working code

## The Files

### 🎯 Core Examples
- **`minimal_agent.py`** - Ultra-minimal (40 lines), best for understanding
- **`adaptive_agent.py`** - More complete (~60 lines), 4 tools, better docs
- **`tutorial_section.md`** - Drop-in tutorial section with full explanation

### 📖 Explanations
- **`key_insight.md`** - 5-min read on exploration vs execution
- **`why_not_workflow.md`** - Deep dive on why this can't be hardcoded
- **`README.md`** - Overview and integration guide

### 📦 Original Files (Still Useful)
- **`improved_example.md`** - Multi-tool variant prioritization
- **`comparison.md`** - Before/after comparison  
- **`autonomous_agent_example.py`** - Full 5-tool implementation

## What Makes These Different

### ❌ Traditional Pipeline
```python
genes = ["SCN1A", "KCNQ2"]  # ← YOU hardcode this
for gene in genes:
    check_variants(gene)
```

### ✅ Adaptive Exploration
```python
> "Patient has epilepsy. Why?"

# Agent searches for epilepsy genes (discovers the list)
# Then checks each one (number of checks depends on results)
# Stops when it finds something (not after N steps)
```

## The Key Difference

| Can Hardcode | Can't Hardcode |
|-------------|----------------|
| "Ping these 3 hosts" | "Investigate this network issue" |
| "Check these genes" | "Why does patient have seizures?" |
| "Filter variants > 30" | "What's interesting in this exome?" |

**The agent explores. You can't write the loop in advance.**

## Real Examples

### Hardcodable (don't use agent):
```python
"Filter variants with QUAL > 30"
"Check coverage in BRCA1"
```
→ Just call the function

### Not hardcodable (use agent):
```python
"Patient has epilepsy. Find why."
→ Searches literature → checks genes → explores pathways

"Debug: Why is chr17 coverage low?"  
→ Checks mappability → GC → structure → adapts based on findings

"What variants might explain this phenotype?"
→ Searches phenotype terms → gets genes → checks variants → explores
```

→ Agent decides the investigation path

## Try It

```bash
python minimal_agent.py
```

Then modify the query and watch how the agent adapts:
- "Patient has autism. Find the genetic cause."
- "Check for both epilepsy and autism variants."
- "Why might this patient have neurological issues?"

Each query triggers a different investigation path.

## For Your Tutorial

**Option 1: Replace current example**
Use `tutorial_section.md` instead of the interval operations example

**Option 2: Add as progression**  
1. Basic: Single tool call
2. Orchestration: Multiple predetermined tools
3. **Exploration: Adaptive discovery** ← `tutorial_section.md`

**Option 3: Comparison chapter**
Show the difference between hardcoded and adaptive

## The Bottom Line

Your critique nailed it: **Most "agent" examples are just fancy function calls.**

**True agent power:** Exploration that adapts based on intermediate findings.

These examples show **when you genuinely can't hardcode the logic** because the decision tree depends on data discovered during execution.

That's when agents actually help.

---

**Start with `key_insight.md` → run `minimal_agent.py` → integrate `tutorial_section.md`**
