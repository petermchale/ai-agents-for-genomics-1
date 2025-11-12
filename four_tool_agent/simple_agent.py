#!/usr/bin/env python3
"""
Simple Working Agent with OpenAI API
Demonstrates an agent choosing a path through tool calls

Usage:
    export OPENAI_API_KEY="your-key-here"
    python simple_agent.py
"""

from openai import OpenAI
import json
import os

# Check for API key
if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Please set OPENAI_API_KEY environment variable")
    print("Example: export OPENAI_API_KEY='sk-...'")
    exit(1)

# Initialize OpenAI client
client = OpenAI()

# Simulated data
DATA = {
    'genes': {'epilepsy': ['SCN1A', 'KCNQ2']},
    'variants': {'SCN1A': 'chr2:166245425:T:C'},
    'frequency': {'chr2:166245425:T:C': 0.00001},
    'clinvar': {'chr2:166245425:T:C': 'Pathogenic'},
}

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_disease_genes",
            "description": "Search for genes associated with a disease",
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
            "description": "Check if patient has variant in a gene",
            "parameters": {
                "type": "object",
                "properties": {
                    "gene": {"type": "string", "description": "Gene symbol"}
                },
                "required": ["gene"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_population_frequency",
            "description": "Check allele frequency in gnomAD",
            "parameters": {
                "type": "object",
                "properties": {
                    "variant": {"type": "string", "description": "Variant ID"}
                },
                "required": ["variant"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_clinvar",
            "description": "Check clinical significance in ClinVar",
            "parameters": {
                "type": "object",
                "properties": {
                    "variant": {"type": "string", "description": "Variant ID"}
                },
                "required": ["variant"]
            }
        }
    },
]

def execute_tool(name: str, args: dict) -> str:
    """Execute the requested tool"""
    if name == "search_disease_genes":
        genes = DATA['genes'].get(args['disease'], [])
        return json.dumps({"genes": genes})
    
    elif name == "check_variant":
        variant = DATA['variants'].get(args['gene'])
        return json.dumps({"variant": variant if variant else "none found"})
    
    elif name == "check_population_frequency":
        freq = DATA['frequency'].get(args['variant'], 0.0)
        return json.dumps({"frequency": freq, "classification": "rare" if freq < 0.01 else "common"})
    
    elif name == "query_clinvar":
        sig = DATA['clinvar'].get(args['variant'], "Not in ClinVar")
        return json.dumps({"significance": sig})
    
    return "{}"

def run_agent(query: str):
    """Run agent and show the path it takes"""
    print(f"\n{'='*70}")
    print(f"QUERY: {query}")
    print(f"{'='*70}\n")
    
    # Initialize conversation
    messages = [{"role": "user", "content": query}]
    
    # Track the path
    path_taken = []
    iteration = 0
    max_iterations = 10
    
    while iteration < max_iterations:
        iteration += 1
        
        # Call OpenAI API
        print(f"Calling OpenAI API (iteration {iteration})...")
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            temperature=0  # Deterministic for demo
        )
        
        message = response.choices[0].message
        
        # Check if there are tool calls
        if not message.tool_calls:
            # No more tool calls - agent is done
            messages.append(message)
            print(f"\nAgent completed in {iteration} iteration(s)\n")
            break
        
        # Agent wants to call tools
        messages.append(message)
        
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Track the path
            path_taken.append(function_name)
            
            print(f"\nTool call {len(path_taken)}: {function_name}({json.dumps(function_args)})")
            
            # Execute the tool
            result = execute_tool(function_name, function_args)
            print(f"  → Result: {result}")
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
    
    # Get final answer
    final_answer = None
    for msg in reversed(messages):
        if hasattr(msg, 'content') and msg.content:
            final_answer = msg.content
            break
        elif isinstance(msg, dict) and msg.get('content'):
            final_answer = msg['content']
            break
    
    # Display results
    print(f"\n{'='*70}")
    print("PATH TAKEN BY AGENT:")
    print(f"{'='*70}")
    for i, tool in enumerate(path_taken, 1):
        print(f"  {i}. {tool}")
    
    print(f"\n{'='*70}")
    print("FINAL ANSWER:")
    print(f"{'='*70}")
    print(f"{final_answer}\n")
    
    print(f"{'='*70}")
    print(f"SUMMARY:")
    print(f"{'='*70}")
    print(f"Total tool calls: {len(path_taken)}")
    print(f"Total API calls to OpenAI: {iteration}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║          SIMPLE GENOMICS AGENT WITH OPENAI API               ║
║          Demonstrates agent choosing a path                  ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Run the agent
    query = "Patient has epilepsy. Find the genetic cause."
    
    try:
        run_agent(query)
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nMake sure:")
        print("  1. You have set OPENAI_API_KEY environment variable")
        print("  2. You have installed openai library: pip install openai")
        print("  3. You have API credits available")
        exit(1)
    
    print("\nAgent successfully completed!")
    print("The path it chose was based on its training and the tools available.")
    print("With 4 tools and typical depth, there were hundreds of possible paths.")
    print("The agent chose ONE path using heuristics, not exhaustive search.\n")