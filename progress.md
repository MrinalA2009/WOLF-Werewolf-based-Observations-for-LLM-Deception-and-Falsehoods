# WOLF Benchmark -- Setup Progress

## Branch
- Working branch: `koh-dev/setup` (off `main`)

## Conda Environment
- **Name:** `wolf`
- **Python:** 3.10
- **PyTorch:** 2.9.1+cu128 (CUDA available, 2x NVIDIA RTX A6000)
- **vLLM:** 0.15.1
- **LangChain stack:** langchain 0.3.27, langchain-openai 0.2.14, langgraph 0.2.76
- **Activation:** `conda activate wolf`

## Hardware
- 2x NVIDIA RTX A6000 (49 GB VRAM each)
- CUDA 12.1 / 12.6 available
- Sufficient VRAM for Meta-Llama-3-8B-Instruct in fp16 (~16 GB)

## Agent Model (response generation)
- **Model:** `meta-llama/Meta-Llama-3-8B-Instruct`
- **Serving:** vLLM with OpenAI-compatible API on `http://localhost:8000/v1`
- **Model cache:** `/ext_hdd/nhkoh/.cache/huggingface/hub/models--meta-llama--Meta-Llama-3-8B-Instruct/` (30 GB, already downloaded)
- **HuggingFace token:** configured in `.env`

## Judge Model
- Not used -- all inference runs on local Llama model via vLLM
- OpenAI API key available in `.env` if needed for future judge evaluation

## Cache Configuration
All cache directories mapped to `/ext_hdd/nhkoh/.cache`:
- `HF_HOME` -> `/ext_hdd/nhkoh/.cache/huggingface`
- `TRANSFORMERS_CACHE` -> `/ext_hdd/nhkoh/.cache/huggingface/hub`
- `TORCH_HOME` -> `/ext_hdd/nhkoh/.cache/torch`
- `TRITON_CACHE_DIR` -> `/ext_hdd/nhkoh/.cache/triton`
- `XDG_CACHE_HOME` -> `/ext_hdd/nhkoh/.cache`

## Code Changes
1. **config.py** -- added `meta-llama/Meta-Llama-3-8B-Instruct` entry with `provider: "local-vllm"`
2. **run.py** -- added `base_url` parameter to `get_llm()` and `run_werewolf_game()`; added `--base-url` CLI argument
3. **Bidding.py** -- updated `get_llm()` to read `VLLM_BASE_URL` env var for local model support
4. **requirements.txt** -- added `vllm`, `huggingface-hub`, `transformers`
5. **.env** -- created with HF_TOKEN, cache paths, vLLM config (gitignored)

## How to Run

### 1. Start the vLLM server (in a separate terminal)
```
conda activate wolf
HF_HOME=/ext_hdd/nhkoh/.cache/huggingface \
HF_TOKEN=<your-token> \
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --dtype auto \
  --port 8000
```

### 2. Run the benchmark
```
conda activate wolf
python run.py --model meta-llama/Meta-Llama-3-8B-Instruct --base-url http://localhost:8000/v1
```

## Bugs Fixed
1. **Stale `protected` field** -- `state.protected` was never reset between rounds, causing the Doctor's protection from Round 1 to persist forever (blocking all subsequent kills on that target). Fixed by resetting `eliminated`, `protected`, `unmasked` at the start of each night in `eliminate_node`.
2. **Missing `"end"` in phase Literal** -- `GameState.phase` Literal type did not include `"end"`, causing a Pydantic validation error when `summary_node` transitioned to the end phase.

## First Run Results (2026-02-08)
- **Run ID:** `20260208-050151-892627`
- **Winner:** Werewolves (4 rounds)
- **Events:** 66 total (23 deception analyses, 18 debates, 4 eliminations, 3 votes)
- **Key observation:** Llama-3-8B never reached majority vote to exile anyone; werewolves won by attrition
- **Logs:** `./logs/20260208-050151-892627/`

## Pending
- [ ] Results analysis pipeline
- [ ] Multi-run benchmark batch execution
- [ ] Comparison with other models (gpt-4o, etc.)
