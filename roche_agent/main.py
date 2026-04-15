#!/usr/bin/env python3
"""
CLI REPL for ClinicalTrialDataAgent.

Usage:
    python main.py path/to/ae_dataset.csv

Set the OPENAI_API_KEY environment variable before running.
In CI it is provided via the GitHub repository secret OPENAI_API_KEY.

Special commands:
    schema  — print the dataset schema used by the agent
    quit / exit / q  — exit the REPL
"""
import os
import sys

from tabulate import tabulate

from agent import ClinicalTrialDataAgent

BANNER = """\
=============================================
  Clinical Trial AE Query Agent
  Type a question to query the dataset.
  Commands: 'schema' | 'quit' | 'exit'
============================================="""

MAX_DISPLAY_ROWS = 20


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_ae_dataset.csv>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print(
            "Warning: OPENAI_API_KEY is not set. "
            "Export it in your shell or provide it via the GitHub Actions secret."
        )

    print(f"Loading dataset: {csv_path}")
    agent = ClinicalTrialDataAgent(csv_path)
    print(BANNER)

    while True:
        try:
            question = input("\nQuestion> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        if question.lower() == "schema":
            print(agent.schema_description)
            continue

        result = agent.run_query(question)

        print(result["query_used"])
        print("Number of unique subjects: ", result["subject_count"])
        print("List of USUBJIDs:", result["subject_ids"])

if __name__ == "__main__":
    main()
