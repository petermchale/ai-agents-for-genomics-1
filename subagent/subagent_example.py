"""
Minimal Subagent Example
Shows how to use specialized subagents with separate contexts
"""

import json
from openai import OpenAI

client = OpenAI()

# Main agent context
main_context = []

# Annotation subagent context (separate!)
annotation_context = [{
    "role": "system",
    "content": "You're a variant annotation expert. Be concise."
}]

# Subagent tools (specialized for annotation)
annotation_tools = [{
    "type": "function",
    "function": {
        "name": "predict_impact",
        "description": "Predict functional impact of a variant",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Variant like chr1:100:A>T"}
            },
            "required": ["variant"]
        }
    }
}]

# Main agent tools
main_tools = [{
    "type": "function",
    "function": {
        "name": "annotate_variant",
        "description": "Get functional annotation for a variant using specialized subagent",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Variant to annotate"}
            },
            "required": ["variant"]
        }
    }
}]

# Subagent tool implementation
def predict_impact(variant):
    """Simulate impact prediction"""
    # In reality, this would query a database
    impacts = {
        "chr1:100:A>T": "missense (pathogenic)",
        "chr2:150:C>G": "synonymous (benign)",
    }
    return impacts.get(variant, "unknown impact")

# THE SUBAGENT - separate context, separate tools
def annotate_variant(variant):
    """Subagent call with its own context and tools"""
    annotation_context.append({
        "role": "user",
        "content": f"What can you tell me about variant {variant}?"
    })
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=annotation_context,
        tools=annotation_tools
    )
    
    # Handle subagent tool calls
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

# Main agent
def process(user_input):
    main_context.append({"role": "user", "content": user_input})
    response = client.chat.completions.create(
        model="gpt-4",
        messages=main_context,
        tools=main_tools
    )
    
    while response.choices[0].message.tool_calls:
        main_context.append(response.choices[0].message)
        
        for tc in response.choices[0].message.tool_calls:
            print(f"[Main agent calling subagent: {tc.function.name}]")
            result = annotate_variant(**json.loads(tc.function.arguments))
            print(f"[Subagent returned: {result[:50]}...]")
            
            main_context.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result
            })
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=main_context,
            tools=main_tools
        )
    
    result = response.choices[0].message.content
    main_context.append({"role": "assistant", "content": result})
    return result

# Demo
if __name__ == "__main__":
    print("=== Subagent Demo ===\n")
    
    queries = [
        "Tell me about variant chr1:100:A>T",
        "What about chr2:150:C>G?"
    ]
    
    for query in queries:
        print(f"> {query}")
        result = process(query)
        print(f"{result}\n")
    
    print(f"\n=== Context Sizes ===")
    print(f"Main context: {len(main_context)} messages")
    print(f"Annotation context: {len(annotation_context)} messages")
    print("\nKey insight: Subagent maintains separate conversation history")
