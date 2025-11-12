#!/usr/bin/env python3
"""
Genomics Agent with OpenAI API
Demonstrates an agent choosing a path through tool calls for genetic diagnosis

Usage:
    export OPENAI_API_KEY="your-key-here"
    python four_tools.py
"""

from openai import OpenAI
from rich.console import Console
from rich.panel import Panel
import json
import os

from util import call_llm, render_response, print_messages, execute_tool_call
from tools.search_disease_genes import search_disease_genes, search_disease_genes_schema
from tools.check_variant import check_variant, check_variant_schema
from tools.check_population_frequency import check_population_frequency, check_population_frequency_schema
from tools.query_clinvar import query_clinvar, query_clinvar_schema

def main(show_messages):
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='sk-...'")
        exit(1)
    
    # Initialize Rich console
    console = Console()
    
    # Initialize client
    client = OpenAI()
    
    # Initialize context (message history)
    messages = []
    
    # Define the mapping of function names to function objects
    tool_functions = {
        "search_disease_genes": search_disease_genes,
        "check_variant": check_variant,
        "check_population_frequency": check_population_frequency,
        "query_clinvar": query_clinvar
    }
    
    # Define the tool schemas
    tool_schemas = [
        search_disease_genes_schema,
        check_variant_schema,
        check_population_frequency_schema,
        query_clinvar_schema
    ]
    
    # Welcome message
    console.print(Panel.fit(
        "[cyan bold]Genomics Agent - Genetic Diagnosis Assistant[/cyan bold]\n"
        "[dim]Type 'quit' or 'exit' to end[/dim]\n"
        "[yellow]Try: 'Patient has epilepsy. Find the genetic cause.'[/yellow]\n"
        "[yellow]Or: 'Analyze variant chr2:166245425:T:C for clinical significance'[/yellow]",
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
        
        try:
            # Track tool calls for path visualization
            tool_call_count = 0
            
            # Show spinner while waiting for initial response
            with console.status("[bold green]Thinking...", spinner="dots"):
                response_message = call_llm(messages, client, tool_schemas)
            
            # Handle tool calls in a loop until we get a final response
            while response_message.tool_calls:
                # Add the assistant's response (with tool call) to messages
                messages.append(response_message)
                
                # Execute each tool call
                for tool_call in response_message.tool_calls:
                    tool_call_count += 1
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    console.print(
                        f"[cyan]🔧 Tool Call {tool_call_count}: {function_name}"
                        f"({', '.join(f'{k}={v}' for k, v in function_args.items())})"
                        f"[/cyan]"
                    )
                    
                    # Execute the tool using the tool_functions dictionary
                    tool_result = execute_tool_call(tool_call, tool_functions)
                    
                    # Show tool result briefly
                    console.print(f"[green]  ✓ {json.dumps(tool_result, indent=2)}[/green]")
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result)
                    })
                
                # Get the next response from the model
                with console.status("[bold green]Processing...", spinner="dots"):
                    response_message = call_llm(messages, client, tool_schemas)
            
            # We've exited the loop, so response_message contains the final text response
            console.print("[dim]Assistant ➜[/dim] ", end='')
            render_response(response_message.content, console)
            
            # Add final response to context
            messages.append(response_message)
            
            # Show summary
            if tool_call_count > 0:
                console.print(f"\n[yellow italic]({tool_call_count} tool call(s) executed)[/yellow italic]")
            
            if show_messages:
                print_messages(messages, console)
        
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            # Remove the last user message on error
            if messages and messages[-1].get("role") == "user":
                messages.pop()
        
        console.print()


if __name__ == '__main__':
    import sys
    
    # Check if --show-messages flag is provided
    show_messages = '--show-messages' in sys.argv
    
    main(show_messages=show_messages)
