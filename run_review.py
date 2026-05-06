#!/usr/bin/env python3
"""
Run the Critique-Oriented RAG peer review.

Usage:
  python3 run_review.py                                # Full comprehensive review
  python3 run_review.py --mode parameter               # All 21 parameters individually
  python3 run_review.py --mode single --param "OH KIE" # Single parameter
  python3 run_review.py --model claude-opus-4-6   # Use a specific model
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Load .env
env_path = BASE_DIR / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

from reviewer_agent import ReviewerAgent, MODEL_PARAMETERS
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Peer Reviewer Agent for Methane Isotope Box Model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 run_review.py                                # Full review
  python3 run_review.py --mode single --param "Cl sink"
  python3 run_review.py --mode parameter --output results.json
  python3 run_review.py --list-params                  # Show all parameters
        """
    )
    parser.add_argument("--mode", choices=["full", "parameter", "single"],
                       default="full", help="Review mode (default: full)")
    parser.add_argument("--param", type=str, help="Parameter name substring (for --mode single)")
    parser.add_argument("--model", type=str, default=None, help="LLM model override")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--list-params", action="store_true", help="List all reviewable parameters")
    
    args = parser.parse_args()
    
    if args.list_params:
        print("Reviewable Parameters:")
        print("=" * 60)
        for i, p in enumerate(MODEL_PARAMETERS, 1):
            print(f"  {i:2d}. {p['name']}")
            print(f"      Current: {p['current_value']}")
            print(f"      Source:  {p['current_source']}")
            print()
        return
    
    agent = ReviewerAgent(model=args.model)
    
    if args.mode == "full":
        review = agent.full_review()
        out = Path(args.output) if args.output else BASE_DIR / "full_review.md"
        with open(out, 'w') as f:
            f.write("# Comprehensive Peer Review: Methane Isotope Box Model\n\n")
            f.write(review)
        print(f"\n  Saved to: {out}")
    
    elif args.mode == "parameter":
        agent.review_all_parameters(
            output_path=Path(args.output) if args.output else None
        )
    
    elif args.mode == "single":
        if not args.param:
            print("Error: --param required for --mode single")
            print("Use --list-params to see available parameters")
            return
        matching = [p for p in MODEL_PARAMETERS if args.param.lower() in p["name"].lower()]
        if not matching:
            print(f"No parameter matching '{args.param}'. Use --list-params to see options.")
            return
        for param in matching:
            agent.review_parameter(param)


if __name__ == "__main__":
    main()
