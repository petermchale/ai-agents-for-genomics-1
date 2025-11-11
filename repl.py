from openai import OpenAI
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def call_llm(messages, client): 
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages 
    )
    return response.choices[0].message.content

def main(): 
    # Initialize client
    client = OpenAI()
    
    # Initialize context (message history)
    messages = []
    
    print(f"{Fore.CYAN}{Style.BRIGHT}Chat REPL - Type 'quit' or 'exit' to end{Style.RESET_ALL}")
    print(f"{Fore.BLACK}{Style.BRIGHT}" + "─" * 60 + f"{Style.RESET_ALL}")
    
    while True:
        # User prompt 
        user_input = input(f"{Style.DIM}You ➜ {Style.RESET_ALL}")
        
        # Check for exit command
        if user_input.lower().strip() in ['quit', 'exit']:
            print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        # Add user message to context
        messages.append({"role": "user", "content": user_input})
        
        # Get LLM response
        try:
            response = call_llm(messages, client)
            # Assistant prompt 
            print(f"{Style.DIM}Assistant ➜ {Style.RESET_ALL}{Style.BRIGHT}{response}{Style.RESET_ALL}")

            # Add assistant response to context
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}Error: {Style.NORMAL}{e}{Style.RESET_ALL}")
            messages.pop()
        
        print()

if __name__ == '__main__': 
    main()