"""
Example of ClinicalTrialDataAgent using pharamaverseadam::adae dataset.
Requires the OPENAI_API_KEY environment variable to be set
(provided via the GitHub repository secret in CI).
"""
import pandas as pd

from agent import ClinicalTrialDataAgent


# Define the function to run the model and print number of unique subjects
# and their USUBJIDs
def run_usubjid_query(question: str, dataset: str) -> None:
    """Load a CSV dataset, run a natural language query, and print the results."""
    df = pd.read_csv(dataset)
    agent = ClinicalTrialDataAgent(df)
    result = agent.run_query(question)
    print(f"Question        : {question}")
    print(f"Unique subjects : {result['subject_count']}")
    print(f"Subject IDs     : {result['subject_ids']}")

# Run the run_query function on adae.csv using example questions
if __name__ == "__main__":
    DATASET = "adae.csv"
    QUESTIONS = [
        "Find all events with toxicity grade 3 or higher",
        "Show subjects with nausea",
        "Which adverse events were fatal?",
    ]

    for q in QUESTIONS:
        run_usubjid_query(q, DATASET)
        print()