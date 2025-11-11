"""
Add this to genomics_agent.py to get a subagent
Only ~15 lines of new code!
"""

# 1. Add subagent context (separate from main context)
annotation_context = [{
    "role": "system",
    "content": "You predict variant impacts. Be concise."
}]

# 2. Add subagent tools
annotation_tools = [{
    "type": "function",
    "function": {
        "name": "predict_impact",
        "description": "Predict functional impact",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string"}
            },
            "required": ["variant"]
        }
    }
}]

def predict_impact(variant):
    impacts = {"chr1:100:A>T": "pathogenic", "chr2:150:C>G": "benign"}
    return impacts.get(variant, "unknown")

# 3. Add the subagent (uses annotation_context, not main context!)
def annotate_variant(variant):
    annotation_context.append({"role": "user", "content": f"Annotate {variant}"})
    response = client.chat.completions.create(
        model="gpt-4",
        messages=annotation_context,  # ← Different context
        tools=annotation_tools         # ← Different tools  
    )
    
    # Handle tools (same pattern as main agent)
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

# 4. Add to main tools
tools.append({
    "type": "function",
    "function": {
        "name": "annotate_variant",
        "description": "Get variant annotation from specialized subagent",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string"}
            },
            "required": ["variant"]
        }
    }
})

# 5. Add to execute_tool function
def execute_tool(function_name, arguments):
    if function_name == "filter_variants":
        return filter_variants(**arguments)
    elif function_name == "intersect_intervals":
        return intersect_intervals(**arguments)
    elif function_name == "annotate_variant":  # ← Add this
        return annotate_variant(**arguments)
    return "Unknown function"

# That's it! Now try:
# > Tell me about variant chr1:100:A>T
# [Main agent calls annotate_variant]
# [Subagent calls predict_impact]
# >>> This variant is pathogenic...
