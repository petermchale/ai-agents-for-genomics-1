from openai import OpenAI
import json

def translate_dna(sequence="", reading_frame=0):
    try:
        codon_table = {
            'ATA':'I', 'ATC':'I', 'ATT':'I', 'ATG':'M',
            'ACA':'T', 'ACC':'T', 'ACG':'T', 'ACT':'T',
            'AGA':'R', 'AGG':'R', 'AGA':'R', 'AGG':'R',
            'CTA':'L', 'CTC':'L', 'CTG':'L', 'CTT':'L',
            'CCA':'P', 'CCC':'P', 'CCG':'P', 'CCT':'P',
            'CAA':'Q', 'CAG':'Q', 'CAC':'H', 'CAT':'H',
            'CGA':'R', 'CGC':'R', 'CGG':'R', 'CGT':'R',
            'GTA':'V', 'GTC':'V', 'GTG':'V', 'GTT':'V',
            'GCA':'A', 'GCC':'A', 'GCG':'A', 'GCT':'A',
            'GAA':'E', 'GAG':'E', 'GAC':'D', 'GAT':'D',
            'GGA':'G', 'GGC':'G', 'GGG':'G', 'GGT':'G',
            'TCA':'S', 'TCC':'S', 'TCG':'S', 'TCT':'S',
            'TTC':'F', 'TTT':'F', 'TTA':'L', 'TTG':'L',
            'TAC':'Y', 'TAT':'Y', 'TGC':'C', 'TGT':'C',
            'TGG':'W', 'TAA':'*', 'TAG':'*', 'TGA':'*'
        }
        sequence = sequence.upper()[reading_frame:]
        protein = ""
        for i in range(0, len(sequence)-2, 3):
            codon = sequence[i:i+3]
            protein += codon_table.get(codon, 'X')
        return protein
    except Exception as e:
        return f"error: {e}"

def call_llm(tools, context, client):
    return client.responses.create(model="gpt-5", tools=tools, input=context)

def call_tool(item):
    # Execute the actual function
    result = translate_dna(**json.loads(item.arguments))
    # Return both the call and the output
    return [item, {
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": result
    }]

def handle_tools(tools, context, response):
    if response.output[0].type == "reasoning":
        context.append(response.output[0])
    
    osz = len(context)
    for item in response.output:
        if item.type == "function_call":
            context.extend(call_tool(item))
    return len(context) != osz  # Did we add tool calls?

def process(query, tools, context, client):
    context.append({"role": "user", "content": query})
    response = call_llm(tools, context, client)
    
    # Keep calling until no more tools are needed
    while handle_tools(tools, context, response):
        response = call_llm(tools, context, client)
    
    context.append({"role": "assistant", "content": response.output_text})
    return response.output_text

def main():
    # Initialize OpenAI client
    client = OpenAI()
    
    # Define available tools
    tools = [{
        "type": "function", 
        "name": "translate_dna",
        "description": "translate a DNA sequence to amino acid sequence",
        "parameters": {
            "type": "object", 
            "properties": {
                "sequence": {
                    "type": "string", 
                    "description": "DNA sequence (A, T, G, C)",
                },
                "reading_frame": {
                    "type": "integer",
                    "description": "reading frame (0, 1, or 2)",
                    "default": 0
                }
            },
            "required": ["sequence"],
        },
    }]
    
    # Initialize conversation context
    context = [{
        "role": "system", 
        "content": "You are a helpful genomics assistant."
    }]
    
    # Main loop
    while True:
        query = input("> ")
        if query.lower() in ['exit', 'quit']:
            break
        result = process(query, tools, context, client)
        print(f">>> {result}\n")
        
        # Pretty print the full context using model_dump()
        print("=" * 80)
        print("FULL CONTEXT:")
        print("=" * 80)
        context_dicts = []
        for item in context:
            if hasattr(item, 'model_dump'):
                context_dicts.append(item.model_dump())
            else:
                context_dicts.append(item)
        print(json.dumps(context_dicts, indent=2))
        print("=" * 80)
        print()

if __name__ == "__main__":
    main()