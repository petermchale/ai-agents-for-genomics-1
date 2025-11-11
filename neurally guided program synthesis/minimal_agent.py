#!/usr/bin/env python3
"""
Ultra-Minimal Adaptive Agent (~40 lines)
Shows: agent explores based on what it finds (can't be hardcoded)
"""
from openai import OpenAI
import json

client = OpenAI()
context = []

# Toy genomics database
DATA = {
    'genes': {'SCN1A': 'epilepsy', 'KCNQ2': 'epilepsy', 'TSC1': 'autism'},
    'variants': {'SCN1A': 'chr2:166245425:T:C (rare, missense)', 'TSC1': 'chr9:135768983:G:T (rare, frameshift)'},
    'related': {'epilepsy': ['SCN1A', 'KCNQ2'], 'autism': ['TSC1', 'MECP2']}
}

tools = [
    {"type": "function", "function": {
        "name": "search_disease_genes", 
        "description": "Find genes associated with a disease",
        "parameters": {"type": "object", "properties": {"disease": {"type": "string"}}, "required": ["disease"]}
    }},
    {"type": "function", "function": {
        "name": "check_variant",
        "description": "Check if patient has variants in a gene", 
        "parameters": {"type": "object", "properties": {"gene": {"type": "string"}}, "required": ["gene"]}
    }}
]

def search_disease_genes(disease): 
    return json.dumps({"genes": DATA['related'].get(disease, [])})

def check_variant(gene): 
    return json.dumps({"variant": DATA['variants'].get(gene, "none found")})

def tool_call(name, args):
    return {"search_disease_genes": search_disease_genes, "check_variant": check_variant}[name](**args)

def process(query):
    print(f"\n> {query}\n")
    context.append({"role": "user", "content": query})
    response = client.chat.completions.create(model="gpt-4", messages=context, tools=tools)
    
    n = 0
    while response.choices[0].message.tool_calls:
        context.append(response.choices[0].message.model_dump())
        for tc in response.choices[0].message.tool_calls:
            n += 1
            print(f"call {n}: {tc.function.name}({tc.function.arguments})")
            context.append({"role": "tool", "tool_call_id": tc.id, 
                          "content": tool_call(tc.function.name, json.loads(tc.function.arguments))})
        response = client.chat.completions.create(model="gpt-4", messages=context, tools=tools)
    
    answer = response.choices[0].message.content
    context.append({"role": "assistant", "content": answer})
    print(f"\n>>> {answer}\n")


# The magic: agent decides how many calls, which tools, when to stop

# process("Patient has epilepsy. Find the genetic cause.")
# pretty_string = json.dumps(context, indent=4)
# print(pretty_string)

process("Now check for autism-related variants too.")
pretty_string = json.dumps(context, indent=4)
print(pretty_string)

# print(f"Agent made its own investigation plan across {len(context)} messages")
