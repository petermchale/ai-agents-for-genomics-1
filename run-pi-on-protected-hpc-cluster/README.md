# How to run the Pi coding agent on a protected HPC cluster 

## Run a 80B-parameter open-source coding LLM on a H200 GPU 

1. Determine whether GPUs are available on compute node `rw236` (say) by issuing `scontrol show node rw236` and looking for: 
* CfgTRES: The total resources configured on the node (e.g., gres/gpu=4).
* AllocTRES: The resources currently allocated to running jobs. If you see gres/gpu=2, it means 2 GPUs are taken and the rest are free.
* GresUsed: This often lists the specific indices (e.g., gpu:2(IDX:0-1)) so you know exactly which physical cards are busy.
2. If a GPU is free, run `ollama` on the H200 with enough resources to accommodate `qwen3-coder-next`: 
```
sbatch run-qwen3-coder-next-on-h200.sh
``` 
3. Once the ollama server is running, one may download `qwen3-coder-next:q8_0` as follows:
```
salloc --nodes=1 --ntasks=1 --account=rai-gpu-rw --partition=rai-gpu-rw --time=1:00:00 --nodelist=rw236
module load ollama 
export OLLAMA_MODELS="/scratch/ucgd/lustre-labs/quinlan/data-shared/ollama-models" 
ollama pull qwen3-coder-next:q8_0 
```
4. To have ollama serve clients (like the Pi coding agent) running on another machine, hunnicutt (say), one needs to run: 
```
salloc --nodes=1 --ntasks=1 --account=rai-gpu-rw --partition=rai-gpu-rw --time=1:00:00 --nodelist=rw236
```     
to drop into the machine running the LLM, and then do a reverse ssh tunnel: 
```
ssh -f -N -R 11434:localhost:11434 hunnicutt
```
Later, one can kill the background ssh process: 
```
pgrep -f "ssh.*11434" | xargs kill
```
or simply logout. 

5. One can monitor GPU and CPU usage at https://portal.chpc.utah.edu/

## Install, configure, and run Pi coding agent 

https://buildwithpi.ai

1. Download Node.js (https://nodejs.org/en/download) 
2. Install Pi, without `-g` option (https://github.com/badlogic/pi-mono/tree/main/packages/coding-agent#quick-start) 
3. Add Pi CLI entry point to `PATH`:
```
export PATH="$HOME/node_modules/.bin:$PATH"
```
4. Configure Pi to use `qwen3-coder-next:q8_0` by pasting the following into `$HOME/.pi/agent/models.json` (from: https://github.com/badlogic/pi-mono/blob/main/packages/coding-agent/docs/models.md#full-example)
```
{
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "api": "openai-completions",
      "apiKey": "ollama",
      "models": [
        {
          "id": "qwen3-coder-next:q8_0",
          "name": "qwen3-coder-next:q8_0 (Local)",
          "reasoning": false,
          "input": ["text"],
          "contextWindow": 128000,
          "maxTokens": 32000,
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
        }
      ]
    }
  }
}
```
5. Run the agent by typing `pi` at the command line 
