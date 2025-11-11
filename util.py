import re
from rich.markdown import Markdown
from rich.syntax import Syntax

def call_llm(messages, client, tool_schemas=None): 
    """Call LLM with optional tool support"""
    params = {
        "model": "gpt-4",
        "messages": messages
    }
    
    if tool_schemas:
        params["tools"] = tool_schemas
        params["tool_choice"] = "auto"
    
    response = client.chat.completions.create(**params)
    return response.choices[0].message

def render_response(text, console):
    """Render response with syntax highlighting for code blocks"""
    # Pattern to match code blocks with optional language specification
    code_block_pattern = r'```(\w+)?\n(.*?)```'
    
    # Split text into parts (text, language, code, text, language, code, ...)
    parts = re.split(code_block_pattern, text, flags=re.DOTALL)
    
    for i, part in enumerate(parts):
        if i % 3 == 0:  # Regular text (not code)
            if part.strip():
                # Render as markdown for better formatting
                console.print(Markdown(part))
        elif i % 3 == 2:  # Code content
            lang = parts[i-1] or 'python'  # Default to python if no language specified
            syntax = Syntax(
                part.strip(), 
                lang, 
                theme="monokai",
                line_numbers=True,  # Added line numbers
                word_wrap=True
            )
            console.print(syntax)

def print_messages(messages, console): 
    console.print("[dim]Accumulated messages:[/dim]")
    import json
    context_dicts = []
    for message in messages:
        if hasattr(message, 'model_dump'):
            context_dicts.append(message.model_dump())
        else:
            context_dicts.append(message)
    print(json.dumps(context_dicts, indent=2))

