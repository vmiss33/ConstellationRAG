# ConstellationRAG

Local, enterprise-style Retrieval-Augmented Generation (RAG) app with NVIDIA NIM inference, a FastAPI backend, and a minimal web UI.

## Architecture

```
+---------------------+         +---------------------+         +---------------------+
|        UI           |  HTTP   |        app          |  HTTP   |         nim         |
|  NGINX + static     +-------->+  FastAPI + RAG      +-------->+  NVIDIA NIM LLM     |
|  http://:3000       | /v1/*   |  http://:8080       | /v1/*   |  http://:8000       |
+---------------------+         +---------------------+         +---------------------+
```

## How to run

Copy `.env.example` to `.env` and fill in values (it is gitignored):

```
NGC_API_KEY=...
NIM_MODEL_PROFILE=
NIM_MAX_MODEL_LEN=4096
NIM_MAX_NUM_SEQS=1
LOCAL_NIM_CACHE=/home/your-wsl-user/.cache/nim
```

Then run in the foreground (you will see logs in your terminal):

```powershell
docker compose up --build
```

Open http://localhost:3000

Notes:
- `NIM_MODEL_PROFILE` can be blank to let NIM auto-select a compatible profile.
- `NIM_MAX_MODEL_LEN=4096` is a safe default for 8GB GPUs (e.g., RTX 4070 Laptop).
- If you run Docker from Windows PowerShell, set `LOCAL_NIM_CACHE` to a Windows path (for example `C:\Users\<you>\.cache\nim`).

## Web interface

The UI is a lightweight NGINX-served page for quick testing:
- Chat window + input + send
- "Ingest docs" button to load data from `./data/`
- Uses relative `/v1/*` and `/ingest` paths (no CORS needed)

## NIM standalone (verified on RTX 4070)

```powershell
docker run -it --rm `
  --gpus all `
  --shm-size=16GB `
  -e NGC_API_KEY="$env:NGC_API_KEY" `
  -e NIM_MODEL_PROFILE="$env:NIM_MODEL_PROFILE" `
  -e NIM_MAX_MODEL_LEN=4096 `
  -e NIM_MAX_NUM_SEQS=1 `
  -p 8000:8000 `
  -v "$env:LOCAL_NIM_CACHE:/opt/nim/.cache" `
  nvcr.io/nim/meta/llama-3.2-1b-instruct:1.12.0
```

## How to ingest documents

Use the UI button (top right) or call the endpoint directly:

```powershell
curl -X POST http://localhost:8080/ingest
```

By default, it loads `.txt` and `.md` files from `./data/`.
To refresh the knowledge base, drop new files into `./data/` and re-run `/ingest`.

## Example chat completion

```powershell
curl -X POST http://localhost:8080/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d '{
    "model": "nim",
    "messages": [
      {"role": "user", "content": "Summarize the sample document."}
    ]
  }'
```
