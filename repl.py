from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
import re

# Initialize Rich console
console = Console()

def call_llm(messages, client): 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages 
    )
    return response.choices[0].message.content

def render_response(text):
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

def main(): 
    # Initialize client
    client = OpenAI()
    
    # Initialize context (message history)
    messages = []
    
    # Welcome message
    console.print(Panel.fit(
        "[cyan bold]Chat REPL[/cyan bold]\n[dim]Type 'quit' or 'exit' to end[/dim]",
        border_style="cyan"
    ))
    console.print()
    
    while True:
        # User prompt 
        user_input = console.input("[dim]You ➜ [/dim]")
        
        # Check for exit command
        if user_input.lower().strip() in ['quit', 'exit']:
            console.print("[cyan]Goodbye![/cyan]")
            break
        
        # Skip empty inputs
        if not user_input.strip():
            continue
        
        # Add user message to context
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response
        try:
            # Show spinner while waiting for response
            with console.status("[bold green]Thinking...", spinner="dots"):
                response = call_llm(messages, client)
            
            # Assistant prompt and response
            console.print("[dim]Assistant ➜[/dim] ", end='')
            render_response(response)
            
            # Add assistant response to context
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            messages.pop()
        
        console.print()

if __name__ == '__main__': 
    main()