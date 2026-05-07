# Critique-Oriented RAG: Peer Reviewer for Methane Isotope Box Model

An automated peer review system that compares a dual-isotope (δ¹³C + δD) Monte Carlo methane box model against a knowledge base of **135+ publications** to identify parameter discrepancies and suggest evidence-based improvements.

Built with **hybrid search** (semantic + keyword) and **Claude** as the reviewer LLM.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Customization](#customization)
- [Example Output](#example-output)
- [Key Findings](#key-findings)
- [Paper Conventions](#paper-conventions)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Overview

### The Problem

A methane isotope box model relies on dozens of parameters (KIEs, sink fractions, source signatures, lifetimes) drawn from literature spanning decades. Keeping these parameters current requires manually cross-referencing 100+ papers — tedious and error-prone.

### The Solution

This system:
1. **Ingests** 135+ research papers into a searchable knowledge base (vector + keyword)
2. **Retrieves** the most relevant literature for each model parameter using hybrid search
3. **Reviews** each parameter using an LLM acting as an expert atmospheric chemist
4. **Outputs** structured reports with specific values, citations, confidence levels, and validation tests

### What It Reviews (21 Parameters)

| Category | Parameters |
|----------|-----------|
| **Kinetic Isotope Effects** | OH (¹³C, D), Cl (¹³C, D), Stratospheric (¹³C, D), Soil (¹³C, D) |
| **Sink Fractions** | OH, Cl, Stratosphere, Soil (global + hemisphere-specific) |
| **Lifetime** | Time-varying τ(t), NH/SH lifetime scaling |
| **Source Signatures** | δ¹³C and δD for Fossil Fuel, Microbial, Biomass Burning |
| **Transport** | Interhemispheric exchange time (τ_ex), NH/SH emission ratios |
| **Uncertainty** | Microbial δD uncertainty (mic_dd_U) |

---

## Architecture

```
┌────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  135+ Papers (.md) │ ──→ │  Ingest Pipeline     │ ──→ │  ChromaDB (Vector)  │
│  • isotope-db (92) │     │  • Section chunking  │     │  6535 chunks        │
│  • OH papers  (43) │     │  • Metadata tagging  │     │  + BM25 (Keyword)   │
└────────────────────┘     │  • 2000 char chunks  │     └──────────┬──────────┘
                           └──────────────────────┘                │
                                                                   │
┌────────────────────┐     ┌──────────────────────┐     ┌──────────▼──────────┐
│  my_model.md       │ ──→ │  Reviewer Agent      │ ←── │  Hybrid Search      │
│  (Anchor Document) │     │  (Claude LLM)        │     │  • RRF Fusion       │
│  • Equations       │     │  • 21 parameters     │     │  • Year Boosting    │
│  • Parameters      │     │  • Expert prompts    │     │  • Section Filter   │
│  • Known Issues    │     │  • Discrepancy logic │     │  • Discrepancy Mode │
└────────────────────┘     └──────────┬───────────┘     └─────────────────────┘
                                      │
                           ┌──────────▼───────────┐
                           │  Peer Review Report   │
                           │  • Per-parameter      │
                           │  • Status flags       │
                           │  • Citations          │
                           │  • Validation tests   │
                           └──────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- An API key for at least one supported LLM provider (see below)
- ~2 GB disk space (papers + embeddings)

### Supported LLM Providers

| Provider | Env Variable | Default Model | Notes |
|----------|-------------|---------------|-------|
| **Anthropic** (Claude) | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` | Original provider |
| **OpenAI** (ChatGPT) | `OPENAI_API_KEY` | `gpt-4o` | |
| **Google Gemini** | `GEMINI_API_KEY` | `gemini-2.0-flash` | Via OpenAI-compatible endpoint |
| **DeepSeek** | `DEEPSEEK_API_KEY` | `deepseek-chat` | |
| **Kimi** (Moonshot AI) | `KIMI_API_KEY` | `moonshot-v1-128k` | 128k context |
| **MiniMax** | `MINIMAX_API_KEY` | `MiniMax-Text-01` | |
| **GLM** (Zhipu AI) | `GLM_API_KEY` | `glm-4-plus` | ChatGLM series |

### 1. Clone and Set Up

```bash
git clone https://github.com/Ilovecodinghhh/critique-rag-methane.git
cd critique-rag-methane

# Copy the environment template and add your API key
cp .env.example .env
nano .env   # Set LLM_PROVIDER and the corresponding API key

# Example for OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here

# Example for Anthropic (default):
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your-key-here

# If paper repos are private, also set:
# export GITHUB_TOKEN=ghp_your_token_here

# Run the automated setup
bash setup.sh
```

The setup script will:
- Install Python dependencies
- Clone the paper repositories
- Run the ingestion pipeline (~2 minutes)
- Validate the setup

### 2. Run a Review

```bash
# Full comprehensive review (all parameters, one LLM call)
python3 run_review.py --mode full

# Use a specific provider
python3 run_review.py --provider openai --model gpt-4o
python3 run_review.py --provider gemini --model gemini-2.0-flash
python3 run_review.py --provider deepseek
python3 run_review.py --provider kimi
python3 run_review.py --provider minimax
python3 run_review.py --provider glm

# Review a specific parameter
python3 run_review.py --mode single --param "OH KIE"

# Review all 21 parameters individually (detailed, 21 LLM calls)
python3 run_review.py --mode parameter

# List all reviewable parameters
python3 run_review.py --list-params

# List all supported LLM providers
python3 run_review.py --list-providers
```

---

## Usage

### Review Modes

| Mode | Command | LLM Calls | Output |
|------|---------|-----------|--------|
| **Full** | `--mode full` | 1 (large context) | `full_review.md` |
| **Parameter** | `--mode parameter` | 21 (one per parameter) | `review_results.json` + `review_results.md` |
| **Single** | `--mode single --param "Cl sink"` | 1 | Console output |

### Options

```bash
python3 run_review.py [OPTIONS]

  --mode {full,parameter,single}   Review mode (default: full)
  --param TEXT                     Parameter name substring (for --mode single)
  --provider TEXT                  LLM provider (anthropic, openai, gemini, deepseek, kimi, minimax, glm)
  --model TEXT                     Override LLM model (e.g., gpt-4o, gemini-2.0-flash)
  --output PATH                   Custom output path
  --list-params                   Show all 21 reviewable parameters
  --list-providers                Show all supported LLM providers
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `anthropic` | LLM provider to use |
| `ANTHROPIC_API_KEY` | *(required if provider=anthropic)* | Anthropic API key |
| `OPENAI_API_KEY` | *(required if provider=openai)* | OpenAI API key |
| `GEMINI_API_KEY` | *(required if provider=gemini)* | Google Gemini API key |
| `DEEPSEEK_API_KEY` | *(required if provider=deepseek)* | DeepSeek API key |
| `KIMI_API_KEY` | *(required if provider=kimi)* | Moonshot AI API key |
| `MINIMAX_API_KEY` | *(required if provider=minimax)* | MiniMax API key |
| `GLM_API_KEY` | *(required if provider=glm)* | Zhipu AI API key |
| `REVIEWER_MODEL` | *(provider default)* | Override the default model |
| `GITHUB_TOKEN` | *(optional)* | For cloning private paper repos |

---

## Project Structure

```
critique-rag-methane/
├── README.md                 # This file
├── setup.sh                  # One-command setup script
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Excludes generated data
│
├── ingest_papers.py          # Paper chunking + indexing pipeline
├── search_engine.py          # Hybrid vector + keyword search
├── llm_client.py             # Unified multi-provider LLM client
├── reviewer_agent.py         # LLM reviewer with 21 parameter definitions
├── run_review.py             # CLI entry point
│
├── my_model.md               # Anchor: current model description
├── full_review.md            # Generated: comprehensive review output
├── full_review_appendix.md   # Generated: additional parameter reviews
│
├── research-methane-isotope-db/  # (cloned) 92 isotope papers
├── research-methane-OH/          # (cloned) 43 OH papers
├── upgrade_two_isotope_model/    # (cloned) The box model code
│
├── chroma_db/                # (generated) Vector database
├── all_chunks.json           # (generated) Full chunk data for BM25
├── chunk_metadata.json       # (generated) Chunk previews
└── bm25_index.json           # (generated) BM25 statistics
```

---

## How It Works

### 1. Paper Ingestion (`ingest_papers.py`)

- Reads all `.md` papers from two repositories (135 total)
- Extracts metadata from filenames: `AuthorYYYYJournal.md` → author, year, journal
- **Chunks by section** using markdown headers (##, ###) and page markers
- Classifies each chunk into: Abstract, Introduction, Methods, Results, Discussion, Conclusions, Supplementary, or Body
- Skips References sections (not useful for parameter extraction)
- Splits long sections into overlapping sub-chunks (~2000 chars, 200 char overlap)
- Stores in **ChromaDB** with `all-MiniLM-L6-v2` sentence-transformer embeddings
- Builds a **BM25** index for keyword search
- Attaches metadata to every chunk: `title`, `year`, `section`, `author`, `journal`, `is_supplement`

### 2. Hybrid Search (`search_engine.py`)

Combines two retrieval strategies:

| Strategy | Strengths | Example |
|----------|-----------|---------|
| **Vector (ChromaDB)** | Conceptual/semantic matches | "temperature dependence of fractionation" finds "KIE varies with T" |
| **BM25 (Keyword)** | Exact technical terms | "KIE_OH_13C 1.0039" finds exact values |

**Reciprocal Rank Fusion (RRF)** merges results:
```
score(doc) = Σ weight_i / (k + rank_i)
```
where `k=60`, default weights are 60% vector / 40% BM25.

Additional features:
- **Year boosting**: Papers from 2020+ get up to 20% score bonus
- **Section filtering**: Focus on Results/Discussion/Methods (where values live)
- **Discrepancy search**: Specialized mode that queries both the parameter name and its current value

### 3. Reviewer Agent (`reviewer_agent.py`)

For each of the 21 parameters:

1. **Multi-query retrieval**: Each parameter has 2-4 specialized search queries
2. **Discrepancy search**: Additional search using the parameter name + current value
3. **Deduplication**: Merges results, keeps top 20 chunks by RRF score
4. **Context assembly**: Formats chunks with source metadata
5. **LLM review**: Sends the model anchor + retrieved context + structured prompt to Claude

The LLM is instructed to:
- Only cite papers present in the retrieved context (no hallucination)
- Flag status as: `CONFIRMED`, `OUTDATED`, `DISCREPANT`, or `INSUFFICIENT_DATA`
- Provide specific numerical values with units and conditions
- Suggest concrete validation experiments

### 4. Output Format

Each parameter review follows this structure:
```
Parameter Name: <name>
Current Value: <what the model uses>
Literature Value: <what the papers say, with citation>
Status: CONFIRMED | OUTDATED | DISCREPANT | INSUFFICIENT_DATA
Reason for Change: <physical/chemical justification>
Suggested Action: <specific change to implement>
Confidence: HIGH | MEDIUM | LOW
Validation Test: <how to verify the improvement>
```

---

## Customization

### Adding New Papers

1. Convert to markdown (e.g., via MinerU or pandoc), trim to content
2. Name following convention: `AuthorYYYYJournal.md`, `AuthorYYYYJournal_SI.md`, `AuthorYYYYJournal_SD.md`
3. Place in either paper directory
4. Re-run: `python3 ingest_papers.py`

### Updating the Model Description

Edit `my_model.md` — this is the "anchor" document fed into every review prompt. Include:
- Governing equations
- All parameter values with sources
- Known issues and assumptions
- Comparison to previous versions

### Adding New Parameters

Edit `MODEL_PARAMETERS` in `reviewer_agent.py`:
```python
{
    "name": "Your Parameter Name",
    "current_value": "Current value and distribution",
    "current_source": "Where this value comes from",
    "search_queries": [
        "search query 1 for this parameter",
        "search query 2 with technical terms",
    ]
}
```

### Adjusting Search Behavior

In `search_engine.py`:
- `vector_weight` / `bm25_weight`: Adjust the hybrid balance (default 0.6/0.4)
- `year_boost`: Toggle recency preference
- `MAX_CHUNK_CHARS`: Increase for more context per chunk (costs more tokens)
- `EMBEDDING_MODEL`: Swap to a larger model for better semantic search

---

## Example Output

### Single Parameter Review (OH KIE for ¹³C)

```
Parameter Name: OH KIE for ¹³C (KIE_OH_13C)
Current Value: Uniform(1.0039, 1.0054)
Literature Value: 1.0039 (Saueressig et al., 2001) — confirmed in Tyler2007JGR,
                  Tapin2026ESSD, Basu2022ACP. No newer lab measurement supersedes it.
Status: OUTDATED (distribution form)
Reason for Change: Modern studies converge on 1.0039 (Saueressig 2001) as the
                   best single value. The upper bound of 1.0054 (Cantrell 1990) is
                   a 35-year-old measurement. Uniform distribution artificially
                   inflates uncertainty and biases mean KIE high.
Suggested Action: Use Normal(1.0039, 0.0004) or narrow Uniform(1.0035, 1.0043).
Confidence: HIGH
Validation Test: Compare MC-derived atmospheric δ¹³C SD against Tapin2026ESSD
                 benchmark of 0.4‰ from OH-KIE uncertainty alone.
```

---

## Key Findings

The initial review of the box model identified these high-priority issues:

| # | Issue | Current → Suggested | Impact |
|---|-------|-------------------|--------|
| 1 | **Cl sink fraction** | 3.5% → ~2% | Over-fractionates ¹³C and δD; ~1‰ shift in effective sink ε |
| 2 | **Strat KIE ¹³C** | 1.003 → ~1.013 | 4× underestimate; need composite O(¹D)+Cl+OH weighting |
| 3 | **CH₄ lifetime** | 8.8–9.2 yr → 9.5–9.7 yr | ~30 Tg/yr bias in total source |
| 4 | **OH_KIE_13C dist.** | Uniform(1.0039–1.0054) → Normal(1.0039, 0.0004) | Cantrell 1990 superseded |
| 5 | **τ_ex** | Fixed 1.0 yr → Trending −0.35%/yr | ~8% change over study period (Naus 2019) |
| 6 | **NH/SH lifetime** | 0.95/1.05 → ~0.98/1.02 | OH near parity (Patra 2014, Zhang 2021) |
| 7 | **BB NH/SH ratio** | 55/45 → ~45/55 | Open fires are SH-dominated per GFED |
| 8 | **mic_dd_U** | Hardcoded 7‰ → Data-derived | Should use EMID database (Menoud 2022) |

---

## Paper Conventions

When adding papers to the knowledge base:

| Type | Naming Convention | Example |
|------|-------------------|---------|
| Main paper | `AuthorYYYYJournal.md` | `Chen2026PNAS.md` |
| Supplementary info | `AuthorYYYYJournal_SI.md` | `Chen2026PNAS_SI.md` |
| Supplementary data | `AuthorYYYYJournal_SD.md` | `Chen2026PNAS_SD.md` |

- Convert PDFs to markdown first (e.g., MinerU, marker, or nougat)
- Trim boilerplate (headers, footers, page numbers)
- Keep figures/tables as text where possible

---

## Troubleshooting

### `ANTHROPIC_API_KEY not set` / API key errors
```bash
cp .env.example .env
nano .env  # Set LLM_PROVIDER and the corresponding API key
```

### `torch`/`torchvision` version mismatch
```bash
pip install 'torch>=2.0' 'torchvision>=0.15' --force-reinstall
```

### Ingestion takes too long
The sentence-transformer model (`all-MiniLM-L6-v2`) downloads ~80MB on first run. Subsequent runs are cached.

### Empty search results
Check that `chroma_db/` exists and `all_chunks.json` is non-empty. Re-run `python3 ingest_papers.py`.

### API rate limits
The parameter-by-parameter mode makes 21 API calls. If rate-limited, switch to `--mode full` (1 call) or add delays.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `chromadb` | Vector database for semantic search |
| `sentence-transformers` | Local embedding model (all-MiniLM-L6-v2) |
| `rank-bm25` | BM25 keyword search |
| `anthropic` | Anthropic Claude API client |
| `openai` | OpenAI API client (also used for Gemini, DeepSeek, Kimi, MiniMax, GLM) |
| `numpy` | Numerical operations |
| `torch` + `transformers` | Backend for sentence-transformers |

---

## License

This project is for research use. The paper repositories may have their own licensing terms.
