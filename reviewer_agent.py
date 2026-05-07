#!/usr/bin/env python3
"""
Critique-Oriented RAG: Peer Reviewer Agent for Methane Isotope Box Model
=========================================================================
Compares current model parameters against a knowledge base of 100+ publications
to identify discrepancies and suggest improvements.

Uses hybrid search (vector + BM25) to find relevant literature, then prompts
an LLM to act as an expert peer reviewer.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional

from search_engine import HybridSearchEngine
from llm_client import LLMClient, PROVIDERS

BASE_DIR = Path(__file__).resolve().parent
MY_MODEL_PATH = BASE_DIR / "my_model.md"


# ---------------------------------------------------------------------------
# Configuration (from environment)
# ---------------------------------------------------------------------------
def get_config():
    """Load configuration from environment variables."""
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    model = os.environ.get("REVIEWER_MODEL")  # None means use provider default

    # Backward compatibility: if ANTHROPIC_API_KEY is set and no LLM_PROVIDER, use anthropic
    if provider not in PROVIDERS:
        raise EnvironmentError(
            f"Unknown LLM_PROVIDER '{provider}'. Supported: {list(PROVIDERS.keys())}"
        )

    return {
        "provider": provider,
        "model": model,
    }


# ---------------------------------------------------------------------------
# Load model description (the "anchor")
# ---------------------------------------------------------------------------
def load_model_description() -> str:
    with open(MY_MODEL_PATH, 'r') as f:
        return f.read()


# ---------------------------------------------------------------------------
# Model Parameters for Discrepancy Search
# ---------------------------------------------------------------------------
MODEL_PARAMETERS = [
    {
        "name": "OH KIE for 13C (KIE_OH_13C)",
        "current_value": "Uniform(1.0039, 1.0054)",
        "current_source": "Saueressig 2001 (1.0039) to Cantrell 1990 (1.0054)",
        "search_queries": [
            "OH kinetic isotope effect 13C CH4 measurement",
            "hydroxyl radical methane carbon isotope fractionation",
            "KIE OH CH4 13C laboratory measurement",
        ]
    },
    {
        "name": "OH KIE for D/H (KIE_OH_D)",
        "current_value": "Uniform(1.294, 1.327)",
        "current_source": "Saueressig 2001 at lab T=296K",
        "search_queries": [
            "OH kinetic isotope effect deuterium CH4",
            "hydroxyl radical methane D/H fractionation temperature",
            "KIE OH CH3D measurement temperature dependence",
        ]
    },
    {
        "name": "Cl KIE for 13C (KIE_Cl_13C)",
        "current_value": "Normal(1.066, 0.002)",
        "current_source": "Saueressig 1995",
        "search_queries": [
            "chlorine kinetic isotope effect 13C CH4",
            "Cl atom methane carbon isotope fractionation",
            "marine boundary layer Cl methane KIE",
        ]
    },
    {
        "name": "Cl KIE for D/H (KIE_Cl_D)",
        "current_value": "Normal(1.52, 0.02)",
        "current_source": "Saueressig 2001",
        "search_queries": [
            "chlorine kinetic isotope effect deuterium CH4",
            "Cl atom CH3D fractionation",
        ]
    },
    {
        "name": "Cl Sink Fraction",
        "current_value": "0.035 (3.5% of total sink)",
        "current_source": "Standard budget assumption",
        "search_queries": [
            "chlorine sink fraction methane global budget",
            "Cl CH4 loss marine boundary layer tropospheric",
            "atomic chlorine methane removal rate global",
        ]
    },
    {
        "name": "OH Sink Fraction",
        "current_value": "0.835 (83.5% of total sink)",
        "current_source": "Standard budget assumption",
        "search_queries": [
            "OH sink fraction methane global budget tropospheric",
            "hydroxyl radical methane loss fraction total",
        ]
    },
    {
        "name": "Stratospheric KIE for 13C",
        "current_value": "1.003 (fixed)",
        "current_source": "Lassey 2007",
        "search_queries": [
            "stratospheric methane isotope fractionation 13C",
            "stratospheric sink KIE methane carbon",
        ]
    },
    {
        "name": "Stratospheric KIE for D/H",
        "current_value": "1.179 (fixed)",
        "current_source": "Dyonisius 2020; Beck 2018",
        "search_queries": [
            "stratospheric methane deuterium fractionation",
            "stratospheric sink KIE D/H methane firn",
        ]
    },
    {
        "name": "Soil KIE for 13C",
        "current_value": "1.0201 (fixed)",
        "current_source": "Average of Snover & Quay, Tyler, Reeburgh",
        "search_queries": [
            "soil uptake methane carbon isotope fractionation",
            "methanotrophic oxidation 13C KIE soil",
        ]
    },
    {
        "name": "Soil KIE for D/H",
        "current_value": "1.083 (fixed)",
        "current_source": "Snover & Quay 2000",
        "search_queries": [
            "soil uptake methane deuterium fractionation",
            "methanotroph D/H KIE soil oxidation",
        ]
    },
    {
        "name": "CH4 Lifetime (time-varying)",
        "current_value": "τ(t) = 9.0 − 0.017×(t−2010), giving 9.19yr (1999) to 8.80yr (2022)",
        "current_source": "Linear parameterization inspired by He et al. 2026",
        "search_queries": [
            "methane lifetime tropospheric OH time-varying",
            "CH4 atmospheric lifetime trend interannual variability",
            "methane lifetime OH concentration global mean",
            "perturbation lifetime methane CH4-OH feedback",
        ]
    },
    {
        "name": "Interhemispheric Exchange Time (τ_ex)",
        "current_value": "1.0 year (fixed)",
        "current_source": "Nguyen et al. 2020",
        "search_queries": [
            "interhemispheric exchange time methane transport",
            "interhemispheric mixing time troposphere SF6",
        ]
    },
    {
        "name": "Fossil Fuel δ13C source signature",
        "current_value": "~−44‰ (time-varying, from EDGAR8 MC)",
        "current_source": "Riddell-Young 2025 pipeline, EDGAR8 weighting",
        "search_queries": [
            "fossil fuel methane δ13C source signature thermogenic",
            "natural gas coal methane carbon isotope",
            "fossil fuel CH4 13C emission weighted global",
        ]
    },
    {
        "name": "Fossil Fuel δD source signature",
        "current_value": "~−186‰ (time-varying, from EDGAR8 MC)",
        "current_source": "Riddell-Young 2025 pipeline",
        "search_queries": [
            "fossil fuel methane δD source signature",
            "natural gas coal methane deuterium isotope",
            "thermogenic CH4 D/H global weighted",
        ]
    },
    {
        "name": "Microbial δ13C source signature",
        "current_value": "~−62‰ (time-varying, from CT-CH4 posterior)",
        "current_source": "Oh 2022 wetlands + Chang 2019 ruminants",
        "search_queries": [
            "microbial methane δ13C source signature wetland",
            "biogenic CH4 carbon isotope ruminant rice wetland",
            "microbial methane 13C emission weighted",
        ]
    },
    {
        "name": "Microbial δD source signature",
        "current_value": "~−299‰ (time-varying)",
        "current_source": "d2H water map + CT-CH4 posterior fractions",
        "search_queries": [
            "microbial methane δD source signature wetland",
            "biogenic CH4 deuterium tropical wetland ruminant",
            "wetland methane D/H water hydrogen isotope",
        ]
    },
    {
        "name": "Biomass Burning δ13C source signature",
        "current_value": "~−22‰ (time-varying)",
        "current_source": "C3/C4 distribution + GFED5",
        "search_queries": [
            "biomass burning methane δ13C source signature",
            "fire CH4 carbon isotope C3 C4 pyrogenic",
        ]
    },
    {
        "name": "Biomass Burning δD source signature",
        "current_value": "~−217‰",
        "current_source": "Literature compilation",
        "search_queries": [
            "biomass burning methane δD source signature",
            "pyrogenic CH4 deuterium fire",
        ]
    },
    {
        "name": "Microbial δD uncertainty (mic_dd_U)",
        "current_value": "7‰ (hardcoded)",
        "current_source": "Ad hoc estimate",
        "search_queries": [
            "microbial methane δD uncertainty variability",
            "wetland methane deuterium range spatial variability",
            "EMID database methane isotope Menoud",
        ]
    },
    {
        "name": "NH/SH Emission Ratios",
        "current_value": "FF: 85/15, Mic: 65/35, BB: 55/45",
        "current_source": "Approximate from EDGAR/CT-CH4, Saunois 2020",
        "search_queries": [
            "hemispheric methane emission distribution NH SH",
            "northern southern hemisphere methane source split",
            "EDGAR methane emission spatial distribution",
        ]
    },
    {
        "name": "NH/SH Lifetime Ratio",
        "current_value": "NH: 0.95×τ, SH: 1.05×τ",
        "current_source": "Prather 2012, Lawrence 2001 approximation",
        "search_queries": [
            "hemispheric OH concentration NH SH asymmetry",
            "northern southern hemisphere OH methane lifetime",
            "tropospheric OH interhemispheric asymmetry",
        ]
    },
]


# ---------------------------------------------------------------------------
# Reviewer Agent Prompts
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert Atmospheric Chemist specializing in Methane Isotope Geochemistry. 
You serve as a rigorous Peer Reviewer for a dual-isotope (δ¹³C + δD) Monte Carlo box model 
used for global methane source partitioning.

Your role is to:
1. **Identify Discrepancies**: Compare model parameters against values in the research literature.
2. **Suggest Improvements**: Provide specific parametric or structural changes with citations.
3. **Propose Validation Tests**: Suggest stress cases or sensitivity experiments.

CRITICAL RULES:
- Only cite papers that appear in the provided Research Context. Do NOT hallucinate citations.
- If the context doesn't contain relevant information for a parameter, say so explicitly.
- Distinguish between "confirmed correct", "potentially outdated", and "clearly discrepant" parameters.
- For numerical values, always specify units and conditions (e.g., temperature for KIE).
- Be specific: "Use 1.0052 ± 0.0005 from Smith2024" not "consider updating".

OUTPUT FORMAT (for each parameter reviewed):
```
Parameter Name: <name>
Current Value: <what the model uses>
Literature Value: <what the papers say, with citation>
Status: CONFIRMED | OUTDATED | DISCREPANT | INSUFFICIENT_DATA
Reason for Change: <physical/chemical justification from the text>
Suggested Action: <specific change to implement>
Confidence: HIGH | MEDIUM | LOW
Validation Test: <how to verify the improvement>
```
"""

REVIEW_PROMPT_TEMPLATE = """
## The Current Model (Anchor)
{model_description}

## Parameter Under Review
**{param_name}**
- Current Value: {current_value}
- Current Source: {current_source}

## Research Context (Retrieved from {n_chunks} publications)
{retrieved_context}

## Task
Review the parameter "{param_name}" against the research context above.

1. Does the current value match the literature? If not, what value should be used?
2. Is the uncertainty range appropriate? Too wide? Too narrow?
3. Are there newer measurements or compilations that supersede the current source?
4. What physical or methodological factors explain any discrepancy?
5. Suggest a specific validation test or sensitivity experiment.

Provide your review in the structured format specified in your system instructions.
"""

FULL_REVIEW_PROMPT = """
## The Current Model (Anchor)
{model_description}

## Full Research Context
The following are the most relevant excerpts from {n_papers} publications in the knowledge base, 
covering KIEs, source signatures, lifetime, sink fractions, and structural model choices.

{all_context}

## Task: Comprehensive Peer Review

Perform a complete peer review of this box model. For EACH parameter listed in the model description:

1. **Check against literature**: Does the value match current best estimates?
2. **Check the uncertainty treatment**: Is it sampled? Fixed? Appropriate distribution?
3. **Structural critique**: Are there fundamental model design issues the literature addresses?
4. **Priority ranking**: Which changes would have the biggest impact on model output?

Additionally, identify:
- **Missing parameters**: Things the model SHOULD include but doesn't
- **Outdated assumptions**: Approaches superseded by newer methods
- **Best practice violations**: Things no modern paper would do this way

Provide your full review in the structured output format, then add a PRIORITY SUMMARY 
ranking the top 5 most impactful changes.
"""


class ReviewerAgent:
    """Peer Reviewer Agent using hybrid RAG and LLM."""
    
    def __init__(self, model: str = None, provider: str = None):
        self.search = HybridSearchEngine()
        self.model_description = load_model_description()
        
        config = get_config()
        provider = provider or config["provider"]
        model = model or config["model"]
        
        self.llm = LLMClient(provider=provider, model=model)
        print(f"  Reviewer Agent initialized with: {self.llm.provider_name} ({self.llm.model})")
    
    def review_parameter(self, param: Dict, verbose: bool = True) -> str:
        """Review a single model parameter against the literature."""
        if verbose:
            print(f"\n{'─'*60}")
            print(f"Reviewing: {param['name']}")
            print(f"{'─'*60}")
        
        # Gather evidence from multiple search queries
        all_results = []
        seen_ids = set()
        
        for query in param["search_queries"]:
            results = self.search.hybrid_search(
                query=query,
                n_results=8,
                section_filter=["Results", "Discussion", "Methods", "Abstract", "Body"],
                year_boost=True,
            )
            for r in results:
                if r["id"] not in seen_ids:
                    seen_ids.add(r["id"])
                    all_results.append(r)
        
        # Also do a discrepancy-focused search
        disc_results = self.search.discrepancy_search(
            parameter_name=param["name"],
            current_value=param["current_value"],
            n_results=5,
        )
        for r in disc_results:
            if r["id"] not in seen_ids:
                seen_ids.add(r["id"])
                all_results.append(r)
        
        # Sort by relevance and take top chunks
        all_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        top_results = all_results[:20]
        
        if verbose:
            print(f"  Found {len(top_results)} relevant chunks from "
                  f"{len(set(r['metadata']['title'] for r in top_results))} papers")
        
        # Format context
        context_parts = []
        for i, r in enumerate(top_results):
            meta = r["metadata"]
            context_parts.append(
                f"### [{i+1}] {meta.get('title', '?')} ({meta.get('year', '?')}) "
                f"— Section: {meta.get('section', '?')}\n{r['text']}\n"
            )
        retrieved_context = "\n".join(context_parts)
        
        # Build prompt
        prompt = REVIEW_PROMPT_TEMPLATE.format(
            model_description=self.model_description,
            param_name=param["name"],
            current_value=param["current_value"],
            current_source=param["current_source"],
            n_chunks=len(top_results),
            retrieved_context=retrieved_context,
        )
        
        # Call LLM
        response_text = self.llm.chat(
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=4000,
            temperature=0.1,
        )
        
        review_text = response_text
        
        if verbose:
            print(f"\n{review_text}")
        
        return review_text
    
    def full_review(self, verbose: bool = True) -> str:
        """Perform a comprehensive review of all parameters."""
        print(f"\n{'='*70}")
        print("COMPREHENSIVE PEER REVIEW")
        print(f"{'='*70}")
        
        # Gather broad context covering all major topics
        broad_queries = [
            "methane isotope source partitioning box model parameters",
            "KIE kinetic isotope effect OH Cl methane fractionation",
            "methane source signature δ13C δD fossil microbial biomass",
            "methane lifetime tropospheric OH trend variability",
            "methane budget global sink fraction OH Cl stratosphere soil",
            "dual isotope methane source attribution uncertainty",
            "interhemispheric transport methane two-box model",
            "methane δD deuterium source signature uncertainty",
        ]
        
        all_results = []
        seen_ids = set()
        for query in broad_queries:
            results = self.search.hybrid_search(query, n_results=10, year_boost=True)
            for r in results:
                if r["id"] not in seen_ids:
                    seen_ids.add(r["id"])
                    all_results.append(r)
        
        all_results.sort(key=lambda x: x.get("rrf_score", 0), reverse=True)
        top_results = all_results[:40]
        
        papers = set(r["metadata"]["title"] for r in top_results)
        print(f"  Using context from {len(top_results)} chunks across {len(papers)} papers")
        
        # Format context
        context_parts = []
        for i, r in enumerate(top_results):
            meta = r["metadata"]
            context_parts.append(
                f"### [{i+1}] {meta.get('title', '?')} ({meta.get('year', '?')}) "
                f"— {meta.get('section', '?')}\n{r['text']}\n"
            )
        
        prompt = FULL_REVIEW_PROMPT.format(
            model_description=self.model_description,
            n_papers=len(papers),
            all_context="\n".join(context_parts),
        )
        
        response_text = self.llm.chat(
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt},
            ],
            max_tokens=8000,
            temperature=0.1,
        )
        
        review_text = response_text
        
        if verbose:
            print(f"\n{review_text}")
        
        return review_text
    
    def review_all_parameters(self, output_path: Optional[Path] = None) -> List[Dict]:
        """Review each parameter individually and compile results."""
        print(f"\n{'='*70}")
        print("PARAMETER-BY-PARAMETER REVIEW")
        print(f"Reviewing {len(MODEL_PARAMETERS)} parameters...")
        print(f"{'='*70}")
        
        reviews = []
        for param in MODEL_PARAMETERS:
            review_text = self.review_parameter(param, verbose=True)
            reviews.append({
                "parameter": param["name"],
                "current_value": param["current_value"],
                "current_source": param["current_source"],
                "review": review_text,
            })
        
        # Save results
        if output_path is None:
            output_path = BASE_DIR / "review_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(reviews, f, indent=2, ensure_ascii=False)
        
        # Also save markdown report
        md_path = output_path.with_suffix('.md')
        with open(md_path, 'w') as f:
            f.write("# Peer Review Report: Methane Isotope Box Model\n\n")
            f.write(f"Generated by Critique-Oriented RAG\n\n")
            f.write(f"Parameters reviewed: {len(reviews)}\n\n")
            f.write("---\n\n")
            for r in reviews:
                f.write(f"## {r['parameter']}\n\n")
                f.write(f"**Current Value:** {r['current_value']}\n\n")
                f.write(f"**Current Source:** {r['current_source']}\n\n")
                f.write(f"{r['review']}\n\n")
                f.write("---\n\n")
        
        print(f"\n  Results saved to: {output_path}")
        print(f"  Markdown report: {md_path}")
        
        return reviews


# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------
def main():
    import argparse
    
    # Load .env file if present
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
    
    parser = argparse.ArgumentParser(description="Peer Reviewer Agent for Methane Box Model")
    parser.add_argument("--mode", choices=["full", "parameter", "single"],
                       default="full", help="Review mode")
    parser.add_argument("--param", type=str, help="Parameter name for single review")
    parser.add_argument("--provider", type=str, default=None,
                       help="LLM provider (anthropic, openai, gemini, deepseek, kimi, minimax, glm)")
    parser.add_argument("--model", type=str, default=None,
                       help="LLM model to use (default: from env or provider default)")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    agent = ReviewerAgent(model=args.model, provider=args.provider)
    
    if args.mode == "full":
        review = agent.full_review()
        output_path = Path(args.output) if args.output else BASE_DIR / "full_review.md"
        with open(output_path, 'w') as f:
            f.write("# Comprehensive Peer Review: Methane Isotope Box Model\n\n")
            f.write(review)
        print(f"\n  Full review saved to: {output_path}")
    
    elif args.mode == "parameter":
        reviews = agent.review_all_parameters(
            output_path=Path(args.output) if args.output else None
        )
    
    elif args.mode == "single":
        if not args.param:
            print("Error: --param required for single mode")
            return
        # Find matching parameter
        matching = [p for p in MODEL_PARAMETERS if args.param.lower() in p["name"].lower()]
        if not matching:
            print(f"No parameter matching '{args.param}'. Available:")
            for p in MODEL_PARAMETERS:
                print(f"  - {p['name']}")
            return
        for param in matching:
            agent.review_parameter(param)


if __name__ == "__main__":
    main()
