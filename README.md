# ai-agents-for-genomics

Inspired by https://fly.io/blog/everyone-write-an-agent/ 

## Installation 

Python dependencies:
```
python3 -m venv .venv
source .venv/bin/activate
pip install openai colorama rich
```

OpenAI API key configuration: 
```
export OPENAI_API_KEY=XXX
```

Install `ollama` to download and serve open-source LLMs locally: 
```
curl -fsSL https://ollama.com/install.sh | sh
PATH=$PATH:$HOME/.local/bin
export OLLAMA_CONTEXT_LENGTH=16384
ollama pull qwen3:8b
ollama serve
```

## Chapter 1 

1. llms_are_stateless.py
2. repl.py
3. one_tool.py 
4. two_tools.py
5. four_tools.py
6. four_tools.py with local LLM