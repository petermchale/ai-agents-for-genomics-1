# Simple Agent with OpenAI API

This is a **complete, working example** that actually calls the OpenAI API and demonstrates an agent choosing a path through tool calls.

## Quick Start

### 1. Install OpenAI library
```bash
pip install openai
```

### 2. Set your API key
```bash
export OPENAI_API_KEY="sk-your-actual-key-here"
```

### 3. Run the script
```bash
python simple_agent.py
```

## What It Does

The script:
1. Calls the OpenAI API with 4 genomics tools
2. The LLM decides which tools to call and in what order
3. Executes each tool call
4. Shows you the path the agent took

## Example Output

```
╔══════════════════════════════════════════════════════════════╗
║          SIMPLE GENOMICS AGENT WITH OPENAI API               ║
║          Demonstrates agent choosing a path                  ║
╚══════════════════════════════════════════════════════════════╝

======================================================================
QUERY: Patient has epilepsy. Find the genetic cause.
======================================================================

Calling OpenAI API (iteration 1)...

Tool call 1: search_disease_genes({"disease": "epilepsy"})
  → Result: {"genes": ["SCN1A", "KCNQ2"]}

Tool call 2: check_variant({"gene": "SCN1A"})
  → Result: {"variant": "chr2:166245425:T:C"}

Calling OpenAI API (iteration 2)...

Tool call 3: check_population_frequency({"variant": "chr2:166245425:T:C"})
  → Result: {"frequency": 1e-05, "classification": "rare"}

Tool call 4: query_clinvar({"variant": "chr2:166245425:T:C"})
  → Result: {"significance": "Pathogenic"}

Calling OpenAI API (iteration 3)...

Agent completed in 3 iteration(s)

======================================================================
PATH TAKEN BY AGENT:
======================================================================
  1. search_disease_genes
  2. check_variant
  3. check_population_frequency
  4. query_clinvar

======================================================================
FINAL ANSWER:
======================================================================
The patient has a pathogenic variant in the SCN1A gene (chr2:166245425:T:C). 
This variant is rare (frequency: 0.00001) and classified as Pathogenic in 
ClinVar. SCN1A mutations are a known cause of epilepsy, particularly Dravet 
syndrome. This variant likely explains the patient's epilepsy.

======================================================================
SUMMARY:
======================================================================
Total tool calls: 4
Total API calls to OpenAI: 3
======================================================================
```

## How It Works

### 1. Tools Definition
The script defines 4 tools in OpenAI's function calling format:
- `search_disease_genes` - Find genes for a disease
- `check_variant` - Check if patient has variant
- `check_population_frequency` - Check if rare
- `query_clinvar` - Check clinical significance

### 2. Agent Loop
```python
while not done:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools
    )
    
    if response has tool_calls:
        for each tool_call:
            result = execute_tool(tool_call)
            add result to messages
    else:
        done = True
```

### 3. The LLM Decides
The LLM (GPT-4) decides:
- Which tool to call first
- What arguments to pass
- Which tool to call next
- When to stop and give final answer

**You didn't hardcode this sequence** - the LLM figured it out!

## Key Points

### The Path is Autonomous
The script doesn't specify:
- ❌ "First search genes, then check variants, then..."
- ❌ The order of tool calls
- ❌ How many times to call each tool

The LLM decides all of this based on:
- ✅ The query
- ✅ Available tools
- ✅ Results from previous calls

### This is Real
This script makes **actual API calls** to OpenAI. You'll see:
- Real network requests
- Real token usage
- Real costs (small, but real)
- Real LLM decision-making

### It's Minimal
Only ~200 lines of code to demonstrate:
- Tool calling
- Agent loop
- Path tracking
- Result display

## Modifying It

### Add More Tools
```python
tools.append({
    "type": "function",
    "function": {
        "name": "your_new_tool",
        "description": "What it does",
        "parameters": {...}
    }
})

# Then implement it
def execute_tool(name, args):
    if name == "your_new_tool":
        return json.dumps({"result": "..."})
```

### Try Different Queries
```python
# More specific
query = "Does this patient have a variant in SCN1A?"

# More exploratory  
query = "What genetic factors might explain this patient's condition?"

# Different disease
query = "Patient has autism. Find genetic cause."
```

### Add Real Data
Replace the simulated `DATA` dict with real:
- Database queries (MySQL, PostgreSQL)
- API calls (gnomAD, ClinVar)
- File reading (VCF, BAM)
- Web scraping (PubMed)

## Troubleshooting

### "No module named 'openai'"
```bash
pip install openai
```

### "AuthenticationError"
Your API key is wrong or missing:
```bash
export OPENAI_API_KEY="sk-your-actual-key"
```

Check it's set:
```bash
echo $OPENAI_API_KEY
```

### "RateLimitError"
You're out of API credits. Add credits to your OpenAI account.

### "Invalid request"
Check that your tools JSON is properly formatted. Copy from this working example.

## API Costs

This script typically uses:
- ~1000-2000 tokens per run
- GPT-4: ~$0.03 per 1K tokens
- **Cost per run: ~$0.03-$0.06**

Very cheap for demonstration!

## Comparison with Demo Script

| Feature | simple_agent.py | path_explosion_demo.py |
|---------|----------------|------------------------|
| **API calls** | YES (real) | NO (simulated) |
| **Cost** | ~$0.03/run | $0 (free) |
| **Shows path** | YES | YES |
| **Shows alternatives** | NO | YES |
| **Shows exponential space** | NO | YES |
| **Requires API key** | YES | NO |

Use `simple_agent.py` to see **real LLM decision-making**.
Use `path_explosion_demo.py` to see **the exponential search space**.

Both together give the complete picture!

## What This Proves

1. **Agents are real** - This actually calls GPT-4 and it actually uses tools
2. **Path is chosen, not coded** - You didn't specify the sequence
3. **It's simple** - ~200 lines does the whole agent loop
4. **It works** - Run it and see!

This is the same pattern used by:
- Claude Code
- ChatGPT function calling
- Production agentic systems
- The examples in the tutorial

Just with real API calls instead of simulation.

## Next Steps

1. **Run this** to see real agent behavior
2. **Run path_explosion_demo.py** to see the search space
3. **Read path_optimality.md** to understand why the path isn't provably optimal
4. **Modify this** to add your own tools and queries

The code is short enough to understand completely, but powerful enough to demonstrate the key concepts.

## Complete File

The complete working script is: `simple_agent.py`

Just set your API key and run it!
