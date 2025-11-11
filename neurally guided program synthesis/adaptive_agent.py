#!/usr/bin/env python3
"""
Adaptive Genomics Agent - Demonstrates tool calling that CAN'T be hardcoded

The key: The agent decides what to investigate based on what it finds.
You can't write this as a fixed pipeline because you don't know:
- How many iterations it will take
- Which tools to call next
- When to stop exploring
"""

from openai import OpenAI
import json

client = OpenAI()
context = []

# Simulated genomics knowledge base
GENE_PATHWAYS = {
    'SCN1A': ['sodium channel', 'neuronal excitability', 'epilepsy'],
    'KCNQ2': ['potassium channel', 'neuronal excitability', 'epilepsy'],
    'GABRA1': ['GABA receptor', 'inhibitory signaling', 'epilepsy'],
    'TSC1': ['mTOR pathway', 'cell growth', 'epilepsy', 'autism'],
    'MECP2': ['transcription regulation', 'Rett syndrome', 'autism'],
    'BRCA1': ['DNA repair', 'breast cancer', 'ovarian cancer'],
}

VARIANT_DATA = {
    'chr2:166245425:T:C': {'gene': 'SCN1A', 'impact': 'missense', 'af': 0.0001},
    'chr20:62063331:G:A': {'gene': 'KCNQ2', 'impact': 'missense', 'af': 0.0003},
    'chr5:161325899:C:T': {'gene': 'GABRA1', 'impact': 'synonymous', 'af': 0.15},
    'chr9:135768983:G:T': {'gene': 'TSC1', 'impact': 'frameshift', 'af': 0.00001},
}

LITERATURE = {
    'epilepsy': ['SCN1A mutations cause Dravet syndrome', 'KCNQ2 linked to neonatal seizures'],
    'autism': ['TSC1 mutations in tuberous sclerosis', 'MECP2 causes Rett syndrome'],
}

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_variants_in_gene",
            "description": "Search for variants in a specific gene",
            "parameters": {
                "type": "object",
                "properties": {"gene": {"type": "string"}},
                "required": ["gene"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_gene_pathways",
            "description": "Get biological pathways and functions for a gene",
            "parameters": {
                "type": "object",
                "properties": {"gene": {"type": "string"}},
                "required": ["gene"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_literature",
            "description": "Search literature for a phenotype or disease term",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pathway_genes",
            "description": "Get other genes in the same biological pathway",
            "parameters": {
                "type": "object",
                "properties": {"pathway": {"type": "string"}},
                "required": ["pathway"]
            }
        }
    },
]

def search_variants_in_gene(gene):
    variants = [k for k, v in VARIANT_DATA.items() if v['gene'] == gene]
    if not variants:
        return json.dumps({"variants": [], "message": f"No variants found in {gene}"})
    results = [{**{"variant": k}, **v} for k, v in VARIANT_DATA.items() if v['gene'] == gene]
    return json.dumps({"variants": results})

def get_gene_pathways(gene):
    pathways = GENE_PATHWAYS.get(gene, [])
    return json.dumps({"gene": gene, "pathways": pathways})

def search_literature(query):
    results = LITERATURE.get(query.lower(), [])
    return json.dumps({"query": query, "papers": results})

def get_pathway_genes(pathway):
    genes = [gene for gene, paths in GENE_PATHWAYS.items() if pathway.lower() in [p.lower() for p in paths]]
    return json.dumps({"pathway": pathway, "genes": genes})

def tool_call(name, args):
    funcs = {
        "search_variants_in_gene": search_variants_in_gene,
        "get_gene_pathways": get_gene_pathways,
        "search_literature": search_literature,
        "get_pathway_genes": get_pathway_genes,
    }
    return funcs[name](**args)

def call():
    return client.chat.completions.create(model="gpt-4", messages=context, tools=tools)

def process(query):
    print(f"\n{'='*60}\n> {query}\n{'='*60}")
    context.append({"role": "user", "content": query})
    response = call()
    
    call_num = 0
    while response.choices[0].message.tool_calls:
        context.append(response.choices[0].message)
        for tc in response.choices[0].message.tool_calls:
            call_num += 1
            print(f"tool call {call_num}: {tc.function.name}({tc.function.arguments})")
            result = tool_call(tc.function.name, json.loads(tc.function.arguments))
            context.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        response = call()
    
    answer = response.choices[0].message.content
    context.append({"role": "assistant", "content": answer})
    print(f"\n>>> {answer}\n")
    return answer

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║  ADAPTIVE GENOMICS AGENT                                     ║
║  Demonstrates exploratory tool calling that can't be coded   ║
╚══════════════════════════════════════════════════════════════╝

The key difference: The agent EXPLORES based on what it finds.
Traditional pipeline: filter → annotate → report (fixed)
Agent: investigate → follow leads → explore connections (adaptive)
""")
    
    # Example 1: Open-ended exploration
    process("This patient has epilepsy. Why might that be? Investigate the genomic data.")
    
    # Example 2: Following connections
    process("Are there other variants in related genes I should check?")
    
    print(f"\n{'='*60}")
    print(f"Total messages in context: {len(context)}")
    print(f"The agent decided its own investigation path - you couldn't hardcode this.")
