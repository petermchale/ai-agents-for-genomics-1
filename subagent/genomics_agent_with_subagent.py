"""
Complete Genomics Agent with Subagent
Demonstrates main agent + specialized annotation subagent
"""

import json
import pandas as pd
import bioframe as bf
from openai import OpenAI

client = OpenAI()

# MAIN AGENT
context = []

variants = pd.DataFrame({
    'CHROM': ['chr1', 'chr1', 'chr2', 'chr2', 'chr3'],
    'POS': [100, 200, 150, 300, 500],
    'REF': ['A', 'G', 'C', 'T', 'A'],
    'ALT': ['T', 'A', 'G', 'C', 'G'],
    'QUAL': [30, 15, 45, 20, 55]
})

genes = pd.DataFrame({
    'chrom': ['chr1', 'chr1', 'chr2'],
    'start': [50, 500, 100],
    'end': [250, 700, 400],
    'name': ['BRCA1', 'TP53', 'EGFR']
})

peaks = pd.DataFrame({
    'chrom': ['chr1', 'chr2', 'chr2'],
    'start': [150, 120, 250],
    'end': [300, 200, 380],
    'name': ['PEAK1', 'PEAK2', 'PEAK3']
})

def filter_variants(min_quality):
    filtered = variants[variants['QUAL'] >= min_quality]
    return f"Found {len(filtered)} variants:\n{filtered.to_string(index=False)}"

def intersect_intervals(set1, set2):
    data = {'genes': genes, 'peaks': peaks}
    overlaps = bf.overlap(data[set1], data[set2], how='inner')
    return f"Found {len(overlaps)} overlaps:\n{overlaps.to_string(index=False)}"

# ANNOTATION SUBAGENT (separate context and tools!)
annotation_context = [{
    "role": "system",
    "content": "You're a variant annotation expert. Predict impacts concisely."
}]

annotation_tools = [{
    "type": "function",
    "function": {
        "name": "predict_impact",
        "description": "Predict functional impact of a variant",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Format: chrX:POS:REF>ALT"}
            },
            "required": ["variant"]
        }
    }
}]

def predict_impact(variant):
    """Simulate impact prediction database"""
    impacts = {
        "chr1:100:A>T": "Missense variant in BRCA1 - PATHOGENIC (PMID:12345678)",
        "chr2:150:C>G": "Synonymous variant in EGFR - BENIGN",
        "chr3:500:A>G": "Nonsense variant in TP53 - PATHOGENIC (stop gained)"
    }
    return impacts.get(variant, "Unknown variant - no annotation available")

def annotate_variant(chrom, pos, ref, alt):
    """Subagent with specialized annotation tools"""
    variant_id = f"{chrom}:{pos}:{ref}>{alt}"
    annotation_context.append({
        "role": "user",
        "content": f"What is the predicted impact of {variant_id}?"
    })
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=annotation_context,
        tools=annotation_tools
    )
    
    # Subagent tool loop
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

# MAIN AGENT TOOLS (includes subagent as a tool)
tools = [
    {
        "type": "function",
        "function": {
            "name": "filter_variants",
            "description": "Filter variants by quality",
            "parameters": {
                "type": "object",
                "properties": {"min_quality": {"type": "number"}},
                "required": ["min_quality"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "intersect_intervals",
            "description": "Find overlapping genomic intervals",
            "parameters": {
                "type": "object",
                "properties": {
                    "set1": {"type": "string", "enum": ["genes", "peaks"]},
                    "set2": {"type": "string", "enum": ["genes", "peaks"]}
                },
                "required": ["set1", "set2"]
            }
        }
    },
    {
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
    }
]

def call():
    return client.chat.completions.create(model="gpt-4", messages=context, tools=tools)

def execute_tool(function_name, arguments):
    if function_name == "filter_variants":
        return filter_variants(**arguments)
    elif function_name == "intersect_intervals":
        return intersect_intervals(**arguments)
    elif function_name == "annotate_variant":
        print(f"  → Calling annotation subagent...")
        return annotate_variant(**arguments)
    return "Unknown function"

def process(user_input):
    context.append({"role": "user", "content": user_input})
    response = call()
    
    while response.choices[0].message.tool_calls:
        tool_calls = response.choices[0].message.tool_calls
        context.append(response.choices[0].message)
        
        for tc in tool_calls:
            print(f"[Tool: {tc.function.name}({tc.function.arguments[:50]}...)]")
            result = execute_tool(tc.function.name, json.loads(tc.function.arguments))
            context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        
        response = call()
    
    assistant_message = response.choices[0].message.content
    context.append({"role": "assistant", "content": assistant_message})
    return assistant_message

def main():
    print("Genomics Agent with Subagent Demo\n")
    print("Try: 'Tell me about the variant at chr1:100'")
    print("     'What are the high-quality pathogenic variants?'\n")
    
    while True:
        user_input = input("> ")
        if user_input.lower() in ['exit', 'quit']:
            print(f"\nFinal context sizes:")
            print(f"  Main agent: {len(context)} messages")
            print(f"  Annotation subagent: {len(annotation_context)} messages")
            break
        
        try:
            result = process(user_input)
            print(f"\n{result}\n")
        except Exception as e:
            print(f"Error: {e}\n")

if __name__ == "__main__":
    main()
