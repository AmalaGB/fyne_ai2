# Task 1 – Rating Prediction with LLMs

This task focuses on using LLMs (Google Gemini and OpenRouter models) to **predict star ratings** from Yelp review text.

**What this notebook does:**
- Loads and samples a Yelp review dataset (200 rows, stratified by star rating)
- Implements 3 prompt versions (V1 baseline, V2 rubric, V3 few-shot)
- Runs full evaluation comparing all prompts
- Computes metrics: accuracy, MAE, confusion matrices
- Saves artifacts for review

The main notebook is `rating_prediction_task1.ipynb`.

---

## Quick Start

```bash
cd task1
pip install -r requirements.txt

# Set your API key(s)
export OPENROUTER_API_KEY="your_openrouter_key"
export GOOGLE_API_KEY="your_gemini_key"  # optional, for Gemini features

# Open notebook and Run All
```

---

## Environment Setup

### 1. Install dependencies

```bash
cd task1
pip install -r requirements.txt
```

### 2. API Keys

**OpenRouter (recommended for bulk evaluation):**
- Gemini free tier has strict rate limits (20 requests/minute)
- OpenRouter provides more generous quotas for bulk evaluation
- Get your key at: https://openrouter.ai/keys

**Gemini (optional, for spot checks):**
- Can still be used for quick tests
- Get your key at: https://aistudio.google.com/app/apikey

Set keys via environment or `.env` file:

```bash
# Option 1: Shell export
export OPENROUTER_API_KEY="your_key"
export GOOGLE_API_KEY="your_key"

# Option 2: Create task1/.env file
OPENROUTER_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

> **Security note:** Never commit `.env` files or API keys to version control.

---

## Configuration

The notebook has a **Configuration cell** at the top with these constants:

```python
EVAL_PROVIDER = "openrouter"              # or "gemini"
EVAL_MODEL = "qwen/qwen-2.5-7b-instruct"  # OpenRouter model
SAMPLE_SIZE = 200                          # rows to sample
RANDOM_STATE = 42                          # reproducibility
EVAL_LIMIT = None                          # None=full eval, or int for quick mode
```

### Switching providers/models

1. Change `EVAL_PROVIDER` to `"gemini"` or `"openrouter"`
2. Change `EVAL_MODEL` to your preferred model:
   - OpenRouter: `"qwen/qwen-2.5-7b-instruct"`, `"meta-llama/llama-3.1-8b-instruct"`
   - Gemini: `"gemini-2.5-flash"`

### Quick mode vs Full mode

- `EVAL_LIMIT = None` → Full 200-row evaluation (~10-20 min)
- `EVAL_LIMIT = 20` → Quick 20-row smoke test (~2 min)

---

## Data

Place your Yelp CSV in:

```
../data/yelp.csv
```

The notebook auto-detects columns named `text`/`review` and `stars`/`rating`.

---

## Running the Notebook

1. Open `task1/rating_prediction_task1.ipynb` in VS Code/Cursor
2. Select your Python interpreter (with dependencies installed)
3. **Run All** (or run cells sequentially)

The notebook will:
1. Validate environment and API keys
2. Load and sample data
3. Define prompts V1, V2, V3
4. Run full evaluation
5. Display metrics and confusion matrices
6. Save outputs to `task1/outputs/`

---

## Outputs

After running, these files are saved to `task1/outputs/`:

| File | Description |
|------|-------------|
| `prompt_comparison.csv` | Metrics for each prompt (accuracy, MAE, etc.) |
| `per_class_accuracy.csv` | Per-star accuracy breakdown |
| `confusion_matrices.png` | Visual confusion matrices |
| `full_results.csv` | Raw predictions for all rows |

---

## Notebook Structure

1. **Setup** – Configuration and environment validation
2. **Data loading** – Load CSV, sample 200 rows stratified by stars
3. **LLM utilities** – `call_gemini`, `call_openrouter`, `predict_one_llm`
4. **Prompt V1** – Baseline minimal prompt
5. **Prompt V2** – Rubric + JSON hardening
6. **Prompt V3** – Few-shot examples + edge cases
7. **Evaluation harness** – Full 200-row eval, metrics, confusion matrices
8. **Results summary** – Save artifacts, discussion

---

## Expected Results

Typical results on Yelp data:

| Prompt | Exact Accuracy | Off-by-1 | MAE |
|--------|---------------|----------|-----|
| V1 | ~35-40% | ~75% | ~0.8 |
| V2 | ~40-45% | ~78% | ~0.7 |
| V3 | ~45-50% | ~82% | ~0.6 |

V3 (few-shot) typically performs best, especially on ambiguous 3★ reviews.

---

## Troubleshooting

**"OPENROUTER_API_KEY not set"**
- Add key to `.env` or export in shell

**Rate limit errors (429)**
- Switch to OpenRouter for bulk eval
- Or set `EVAL_LIMIT = 20` for quick mode

**"call_openrouter not defined"**
- Run the LLM utilities cell first
- Or restart kernel and Run All from top
