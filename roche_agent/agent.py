"""
ClinicalTrialDataAgent — translates natural language questions about an
Adverse Events (AE) dataset into structured Pandas filter queries using
LangChain + OpenAI structured output.
"""
from __future__ import annotations

from typing import Union

import pandas as pd
from pydantic import BaseModel, Field


class QuerySchema(BaseModel):
    """Structured output produced by the LLM for each user question."""

    target_column: str = Field(
        description="The exact column name from the dataset to filter on."
    )
    filter_value: str = Field(
        description=(
            "The value to filter by. "
            "For numeric comparisons prefix with an operator: '>=3', '<10', '!=0'. "
            "For categorical/string columns provide the exact value."
        )
    )
def _coerce_numeric(s: str) -> float:
    try:
        return float(s.strip())
    except ValueError:
        raise ValueError(f"Cannot interpret '{s}' as a numeric value for comparison.")


def _operator_str(val: str) -> str:
    """Return a human-readable operator string for display purposes."""
    for op in (">=", "<=", "!=", ">", "<"):
        if val.startswith(op):
            return f"{op} {val[len(op):].strip()}"
    return f"== {val!r}"


class ClinicalTrialDataAgent:
    """
    Agent that maps natural language questions to Pandas filter queries
    by dynamically introspecting the dataset schema at runtime.

    Usage:
        agent = ClinicalTrialDataAgent("ae_dataset.csv")
        result = agent.run_query("Show me all serious adverse events")
        print(result["result_summary"])
        print(result["result_df"])
    """

    def __init__(
        self,
        df_or_path: Union[str, pd.DataFrame],
        model: str = "gpt-4o-mini",
    ) -> None:
        self.df = self._load_data(df_or_path)
        self.schema_description = self._build_schema_description()
        self.chain = self._build_chain(model)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_data(self, df_or_path: Union[str, pd.DataFrame]) -> pd.DataFrame:
        if isinstance(df_or_path, pd.DataFrame):
            return df_or_path.copy()
        if isinstance(df_or_path, str):
            return pd.read_csv(df_or_path)
        raise TypeError(f"Expected str path or DataFrame, got {type(df_or_path)}")

    def _build_schema_description(self) -> str:
        """
        Build a textual description of the DataFrame schema including column
        names, dtypes, and sample values. Injected into the LLM system prompt
        so the model knows exactly which columns exist and what values they hold.
        """
        lines = ["Dataset columns (name | dtype | sample values):"]
        for col in self.df.columns:
            dtype = str(self.df[col].dtype)
            samples = self.df[col].dropna().unique()[:5].tolist()
            lines.append(f"  - {col} | {dtype} | samples: {samples}")
        lines.append(f"\nTotal rows: {len(self.df)}")
        return "\n".join(lines)

    def _build_chain(self, model: str):
        """
        Build a LangChain chain: ChatPromptTemplate | ChatOpenAI (structured output).
        The {schema} placeholder is filled at invoke time so the chain is
        reusable if the DataFrame changes.
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        llm = ChatOpenAI(model=model, temperature=0)
        structured_llm = llm.with_structured_output(QuerySchema)

        system_prompt = """\
You are a clinical data query assistant helping safety reviewers analyze \
Adverse Events (AE) datasets. Your job is to translate a natural language \
question into a structured filter query.

The dataset has the following schema:
{schema}

Rules:
1. You MUST use only column names that appear exactly in the schema above.
2. For string/categorical columns, return the filter_value as an exact \
string match using values from the sample values shown.
3. For numeric columns, you may prefix the filter_value with an operator: \
>=, >, <=, <, != — or leave it bare for equality (e.g. "3" means == 3).
4. Return only ONE column/value pair — the most relevant filter for the question.
5. If the question is ambiguous, pick the most clinically significant column."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{question}"),
        ])

        return prompt | structured_llm

    def _build_mask(self, col: str, val: str) -> pd.Series:
        """
        Parse the filter_value string (possibly with an operator prefix such as
        '>=3') and return a boolean Series for use with df.loc[].
        Falls back to case-insensitive string equality when no operator is found.
        """
        col_series = self.df[col]

        for op in (">=", "<=", "!=", ">", "<"):
            if val.startswith(op):
                numeric_val = _coerce_numeric(val[len(op):])
                if op == ">=":
                    return col_series >= numeric_val
                if op == "<=":
                    return col_series <= numeric_val
                if op == "!=":
                    return col_series != numeric_val
                if op == ">":
                    return col_series > numeric_val
                if op == "<":
                    return col_series < numeric_val

        # No operator prefix — try numeric equality first, then string equality
        try:
            numeric_val = float(val)
            return col_series == numeric_val
        except ValueError:
            return col_series.astype(str).str.upper() == val.strip().upper()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run_query(self, question: str) -> dict:
        """
        Translate a natural language question into a Pandas filter and execute it.

        Returns a dict with:
            query_used (str)    — human-readable representation of the filter
            result_df  (DataFrame) — matching rows
            result_summary (str)  — plain-English summary of the outcome
        """
        # 1. Run LLM chain to get structured output
        parsed: QuerySchema = self.chain.invoke({
            "schema": self.schema_description,
            "question": question,
        })

        col = parsed.target_column
        val = parsed.filter_value
        query_str = f"df[df['{col}'] {_operator_str(val)}]"

        # 2. Guard against hallucinated column names
        if col not in self.df.columns:
            return {
                "query_used": query_str,
                "result_df": pd.DataFrame(),
                "result_summary": (
                    f"Error: column '{col}' not found in dataset. "
                    f"Available columns: {list(self.df.columns)}"
                ),
            }

        # 3. Build and execute the Pandas filter
        try:
            mask = self._build_mask(col, val)
            result_df = self.df.loc[mask].reset_index(drop=True)
        except Exception as exc:
            return {
                "query_used": query_str,
                "result_df": pd.DataFrame(),
                "result_summary": f"Execution error: {exc}",
            }

        # 4. Build a plain-English summary
        n = len(result_df)
        total = len(self.df)

        # Unique subject count and IDs
        if "USUBJID" in result_df.columns:
            unique_subjects = result_df["USUBJID"].dropna().unique().tolist()
            subject_count = len(unique_subjects)
        else:
            unique_subjects = []
            subject_count = 0

        if n == 0:
            summary = f"No rows matched: {col} {_operator_str(val)}"
        elif n == total:
            summary = f"Warning: all {n} rows matched — query may be too broad."
        else:
            summary = (
                f"{n} row(s) matched out of {total} total. "
                f"{subject_count} unique subject(s): {unique_subjects}"
            )

        return {
            "query_used": query_str,
            "result_df": result_df,
            "result_summary": summary,
            "subject_count": subject_count,
            "subject_ids": unique_subjects,
        }
