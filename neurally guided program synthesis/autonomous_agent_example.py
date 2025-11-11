#!/usr/bin/env python3
"""
Autonomous Genomics Agent Example
Demonstrates multi-tool orchestration for variant prioritization
"""

import json
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()
context = []

# Sample variant data
variants = pd.DataFrame({
    'CHROM': ['chr1', 'chr1', 'chr2', 'chr7', 'chr17', 'chr19'],
    'POS': [100, 43094500, 215632255, 55249071, 41244748, 11234567],
    'REF': ['A', 'G', 'G', 'C', 'C', 'T'],
    'ALT': ['T', 'A', 'T', 'T', 'T', 'C'],
    'QUAL': [35, 42, 18, 45, 38, 20],
    'GENE': ['TEST1', 'TP53', 'BRAF', 'EGFR', 'BRCA1', 'APOE']
})

# Tool definitions
tools = [
    {
        "type": "function",
        "function": {
            "name": "filter_variants_by_quality",
            "description": "Filter variants by minimum quality score. Returns variants that pass the quality threshold.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_qual": {
                        "type": "number", 
                        "description": "Minimum QUAL score threshold"
                    }
                },
                "required": ["min_qual"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_population_frequency",
            "description": "Check allele frequency in gnomAD database for a specific variant. Lower frequencies suggest rarer, potentially more significant variants.",
            "parameters": {
                "type": "object",
                "properties": {
                    "chrom": {"type": "string", "description": "Chromosome (e.g., 'chr1')"},
                    "pos": {"type": "integer", "description": "Genomic position"},
                    "ref": {"type": "string", "description": "Reference allele"},
                    "alt": {"type": "string", "description": "Alternate allele"}
                },
                "required": ["chrom", "pos", "ref", "alt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "predict_variant_impact",
            "description": "Predict functional impact of a variant using in silico tools. Returns impact severity and type (missense, frameshift, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "chrom": {"type": "string"},
                    "pos": {"type": "integer"},
                    "ref": {"type": "string"},
                    "alt": {"type": "string"},
                    "gene": {"type": "string", "description": "Gene symbol"}
                },
                "required": ["chrom", "pos", "ref", "alt", "gene"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_clinvar",
            "description": "Check ClinVar database for known clinical significance. Returns classification like Pathogenic, Benign, VUS, etc.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_gene_info",
            "description": "Get information about a gene including its function and disease associations from OMIM/GeneCards.",
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

# Tool implementations
def filter_variants_by_quality(min_qual: float) -> str:
    """Filter variants by quality score"""
    filtered = variants[variants['QUAL'] >= min_qual]
    result = filtered[['CHROM', 'POS', 'REF', 'ALT', 'QUAL', 'GENE']].to_dict('records')
    return json.dumps({"variants": result, "count": len(filtered)})

def check_population_frequency(chrom: str, pos: int, ref: str, alt: str) -> str:
    """Simulate gnomAD population frequency lookup"""
    # Simulated frequencies (in real app, would query gnomAD API)
    frequencies = {
        ('chr1', 43094500): 0.00012,   # TP53 - rare
        ('chr2', 215632255): 0.00008,  # BRAF - rare
        ('chr7', 55249071): 0.00095,   # EGFR - rare but less so
        ('chr17', 41244748): 0.00003,  # BRCA1 - very rare
        ('chr19', 11234567): 0.15,     # APOE - common
    }
    af = frequencies.get((chrom, pos), 0.25)  # Default to common if not in our DB
    rarity = "very rare" if af < 0.0001 else "rare" if af < 0.01 else "common"
    return json.dumps({
        "variant": f"{chrom}:{pos}:{ref}>{alt}",
        "allele_frequency": af,
        "population": "gnomAD v3.1",
        "classification": rarity
    })

def predict_variant_impact(chrom: str, pos: int, ref: str, alt: str, gene: str) -> str:
    """Simulate variant effect prediction"""
    # Simulated predictions (in real app, would use VEP/SnpEff)
    impacts = {
        'TP53': {
            'impact': 'missense_variant',
            'severity': 'moderate',
            'prediction': 'deleterious',
            'scores': {'SIFT': 0.01, 'PolyPhen': 0.95}
        },
        'BRAF': {
            'impact': 'missense_variant',
            'severity': 'moderate',
            'prediction': 'deleterious',
            'scores': {'SIFT': 0.02, 'PolyPhen': 0.89}
        },
        'EGFR': {
            'impact': 'missense_variant',
            'severity': 'moderate',
            'prediction': 'possibly_damaging',
            'scores': {'SIFT': 0.05, 'PolyPhen': 0.72}
        },
        'BRCA1': {
            'impact': 'frameshift_variant',
            'severity': 'high',
            'prediction': 'loss_of_function',
            'scores': {}
        },
        'APOE': {
            'impact': 'synonymous_variant',
            'severity': 'low',
            'prediction': 'benign',
            'scores': {'SIFT': 0.8, 'PolyPhen': 0.1}
        }
    }
    result = impacts.get(gene, {
        'impact': 'unknown',
        'severity': 'modifier',
        'prediction': 'uncertain'
    })
    result['gene'] = gene
    result['variant'] = f"{chrom}:{pos}:{ref}>{alt}"
    return json.dumps(result)

def query_clinvar(chrom: str, pos: int, ref: str, alt: str) -> str:
    """Simulate ClinVar database lookup"""
    # Simulated ClinVar data
    clinvar_data = {
        ('chr1', 43094500): {
            'classification': 'Pathogenic',
            'review_status': '★★★',
            'conditions': ['Li-Fraumeni syndrome'],
            'submissions': 15
        },
        ('chr2', 215632255): {
            'classification': 'Likely Pathogenic',
            'review_status': '★★',
            'conditions': ['Colorectal cancer'],
            'submissions': 3
        },
        ('chr7', 55249071): {
            'classification': 'Uncertain Significance',
            'review_status': '★',
            'conditions': ['Lung cancer'],
            'submissions': 2
        },
        ('chr17', 41244748): {
            'classification': 'Pathogenic',
            'review_status': '★★★★',
            'conditions': ['Hereditary breast and ovarian cancer'],
            'submissions': 42
        },
    }
    data = clinvar_data.get((chrom, pos), {
        'classification': 'Not in ClinVar',
        'review_status': 'N/A'
    })
    data['variant'] = f"{chrom}:{pos}:{ref}>{alt}"
    return json.dumps(data)

def get_gene_info(gene: str) -> str:
    """Get gene information"""
    gene_info = {
        'TP53': {
            'name': 'Tumor Protein P53',
            'function': 'Tumor suppressor, cell cycle regulation',
            'diseases': ['Li-Fraumeni syndrome', 'Various cancers'],
            'inheritance': 'Autosomal dominant',
            'penetrance': 'High'
        },
        'BRAF': {
            'name': 'B-Raf Proto-Oncogene',
            'function': 'Serine/threonine kinase in MAPK pathway',
            'diseases': ['Melanoma', 'Colorectal cancer'],
            'inheritance': 'Somatic mutations common',
            'penetrance': 'Variable'
        },
        'EGFR': {
            'name': 'Epidermal Growth Factor Receptor',
            'function': 'Receptor tyrosine kinase',
            'diseases': ['Lung cancer', 'Glioblastoma'],
            'inheritance': 'Somatic mutations common',
            'penetrance': 'N/A'
        },
        'BRCA1': {
            'name': 'Breast Cancer Type 1',
            'function': 'DNA repair, tumor suppression',
            'diseases': ['Hereditary breast and ovarian cancer'],
            'inheritance': 'Autosomal dominant',
            'penetrance': 'High (70-80% lifetime risk)'
        },
        'APOE': {
            'name': 'Apolipoprotein E',
            'function': 'Lipid metabolism',
            'diseases': ['Alzheimer disease', 'Cardiovascular disease'],
            'inheritance': 'Complex',
            'penetrance': 'Variable'
        }
    }
    info = gene_info.get(gene, {
        'name': gene,
        'function': 'Unknown',
        'diseases': 'Not in database'
    })
    info['gene'] = gene
    return json.dumps(info)

# Tool dispatcher
def tool_call(function_name: str, arguments: dict) -> str:
    """Execute the requested tool"""
    if function_name == "filter_variants_by_quality":
        return filter_variants_by_quality(**arguments)
    elif function_name == "check_population_frequency":
        return check_population_frequency(**arguments)
    elif function_name == "predict_variant_impact":
        return predict_variant_impact(**arguments)
    elif function_name == "query_clinvar":
        return query_clinvar(**arguments)
    elif function_name == "get_gene_info":
        return get_gene_info(**arguments)
    else:
        return json.dumps({"error": f"Unknown function: {function_name}"})

# Agent functions
def call():
    """Call the LLM with current context and tools"""
    return client.chat.completions.create(
        model="gpt-4",
        messages=context,
        tools=tools
    )

def process(line: str) -> str:
    """Process user input through the agent"""
    print(f"\n> {line}")
    
    context.append({"role": "user", "content": line})
    response = call()
    
    # Handle tool calls
    tool_call_count = 0
    while response.choices[0].message.tool_calls:
        tool_calls = response.choices[0].message.tool_calls
        context.append(response.choices[0].message)
        
        # Execute each tool call
        for tc in tool_calls:
            tool_call_count += 1
            print(f"tool call {tool_call_count}: {tc.function.name}({tc.function.arguments})")
            
            result = tool_call(tc.function.name, json.loads(tc.function.arguments))
            context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        
        # Call LLM again with tool results
        response = call()
    
    # Get final answer
    assistant_message = response.choices[0].message.content
    context.append({"role": "assistant", "content": assistant_message})
    
    print(f"\n>>> {assistant_message}\n")
    print(f"(Made {tool_call_count} tool calls)\n")
    return assistant_message

def main():
    """Run the agent"""
    print("=== Autonomous Genomics Agent ===")
    print("Demonstrating multi-tool orchestration\n")
    
    # Example 1: Pathogenic variant discovery
    print("\n" + "="*60)
    print("EXAMPLE 1: Find pathogenic variants in cancer genes")
    print("="*60)
    process("Find pathogenic variants in cancer genes")
    
    # Example 2: Follow-up question
    print("\n" + "="*60)
    print("EXAMPLE 2: Follow-up about specific variant")
    print("="*60)
    process("Tell me more about the BRCA1 variant - why is it so concerning?")
    
    # Example 3: Gene-specific query
    print("\n" + "="*60)
    print("EXAMPLE 3: What makes a good candidate variant?")
    print("="*60)
    process("What criteria make a variant a high-priority candidate for clinical follow-up?")
    
    print("\n" + "="*60)
    print("CONTEXT SUMMARY")
    print("="*60)
    print(f"Total messages in context: {len(context)}")
    print(f"User messages: {sum(1 for m in context if m.get('role') == 'user')}")
    print(f"Tool calls: {sum(1 for m in context if m.get('role') == 'tool')}")
    print(f"Assistant responses: {sum(1 for m in context if m.get('role') == 'assistant')}")

if __name__ == "__main__":
    main()
