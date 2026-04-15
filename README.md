# roche_ads_programmer

Programming exercise for the Roche ADS Programmer interview. The repository
contains four self-contained pieces of work: three R-based clinical
programming tasks (SDTM, ADaM, TLG) built on the **pharmaverse** stack, and
one Python project that wraps a clinical-trial dataset in a natural-language
agent powered by the OpenAI API.

## Repository layout

| Folder | What it contains |
|---|---|
| [inst/](inst/) | Shared inputs used by the R scripts (e.g. controlled-terminology CSVs). |
| [question_1_sdtm/](question_1_sdtm/) | **Task 1 — SDTM:** build the `DS` (Disposition) domain from raw `pharmaverseraw` data using `sdtm.oak`. |
| [question_2_adam/](question_2_adam/) | **Task 2 — ADaM:** derive `ADSL` (Subject-Level Analysis Dataset) from SDTM domains using `admiral`. |
| [question_3_tlg/](question_3_tlg/) | **Task 3 — TLG:** produce an Adverse Events summary table (`gtsummary`) and visualizations (`ggplot2`). |
| [roche_agent/](roche_agent/) | **Bonus — Python agent:** natural-language query interface over an ADAE dataset using LangChain + OpenAI structured output. |
| [project.Rproj](project.Rproj) | RStudio project file — open this to load the R workspace. |

Each `question_*` folder follows the same convention:

- `create_*.R` / `0X_*.R` — the main script(s) that build the artifact.
- `*_run.R` or `run_*.R` — a wrapper that sources the script(s) and writes a log.
- `*_log.txt` — captured run output for the reviewer.
- `*.RDS` / `*.html` / `*.png` — the resulting artifacts.

---

## Task 1 — SDTM (`question_1_sdtm/`)

Builds the **DS (Disposition)** domain.

- [01_create_ds_domain.R](question_1_sdtm/01_create_ds_domain.R) — reads
  `pharmaverseraw::ds_raw`, applies controlled terminology from
  [inst/sdtm_ct.csv](inst/sdtm_ct.csv), and maps raw variables to SDTM
  variables via `sdtm.oak::assign_*` helpers.
- [ds_run.R](question_1_sdtm/ds_run.R) — sources the script and captures
  output to [ds_log.txt](question_1_sdtm/ds_log.txt).
- [ds.RDS](question_1_sdtm/ds.RDS) — final DS dataset.

## Task 2 — ADaM (`question_2_adam/`)

Derives **ADSL** from SDTM domains using `admiral`.

- [create_adsl.R](question_2_adam/create_adsl.R) — pulls `dm`, `ex`, `vs`,
  `ae`, `ds` from `pharmaversesdtm`, derives demographic groupings (e.g.
  `AGEGR9`), treatment dates, and other subject-level variables.
- [adsl_run.R](question_2_adam/adsl_run.R) — wrapper + logging.
- [adsl.RDS](question_2_adam/adsl.RDS) — final ADSL dataset.

## Task 3 — TLG (`question_3_tlg/`)

Tables, Listings & Graphs for Adverse Events on the safety population.

- [01_create_ae_summary_table.R](question_3_tlg/01_create_ae_summary_table.R)
  — hierarchical AE summary by SOC / preferred term using
  `gtsummary::tbl_hierarchical`. Output:
  [ae_summary_table.html](question_3_tlg/ae_summary_table.html).
- [02_create_visualizations.R](question_3_tlg/02_create_visualizations.R)
  — `ggplot2` charts:
  [ae_severity_bar_chart.png](question_3_tlg/ae_severity_bar_chart.png) and
  [top10_ae_chart.png](question_3_tlg/top10_ae_chart.png).
- [run_01_02.R](question_3_tlg/run_01_02.R) — runs both scripts and writes
  `summary_table_log.txt` / `visualizations_log.txt`.

---

## Bonus — Python agent (`roche_agent/`)

A small CLI agent that turns natural-language questions about an Adverse
Events dataset into structured Pandas filter queries.

- [agent.py](roche_agent/agent.py) — `ClinicalTrialDataAgent` class. Uses a
  Pydantic `QuerySchema` and LangChain's structured-output binding so the
  LLM returns a `(target_column, filter_value)` pair that is applied to the
  DataFrame.
- [main.py](roche_agent/main.py) — REPL CLI. Run with a path to a CSV and
  ask questions like *"Show subjects with nausea"* or *"Find all events
  with toxicity grade 3 or higher"*.
- [test.py](roche_agent/test.py) — example invocations against
  [adae.csv](roche_agent/adae.csv).
- [requirements.txt](roche_agent/requirements.txt) — Python dependencies.

### Running the Python agent locally

The agent calls the OpenAI API, so each user must supply their **own** API
key. The `OPENAI_API_KEY` referenced in GitHub Actions is a private
repository secret and is not available outside this repo's CI runs.

1. Get a key at <https://platform.openai.com/api-keys>.
2. Export it in your shell:
   ```bash
   export OPENAI_API_KEY=sk-...          # macOS / Linux
   $env:OPENAI_API_KEY = "sk-..."        # Windows PowerShell
   ```
3. Install dependencies:
   ```bash
   cd roche_agent
   pip install -r requirements.txt
   ```
4. Start the interactive REPL:
   ```bash
   python main.py adae.csv
   ```
   Type a question at the `Question>` prompt, or use `schema` to print the
   dataset schema and `quit` / `exit` to leave.

> ⚠️ Never commit your API key — anyone with the key can spend against your
> account.

### Running the example script (`test.py`)

[test.py](roche_agent/test.py) runs a fixed set of example questions
against [adae.csv](roche_agent/adae.csv) non-interactively — useful as a
quick smoke-test that your API key and dependencies are working. From the
`roche_agent/` directory:

```bash
python test.py
```

The script prints, for each example question, the number of unique
subjects matched and their `USUBJID`s. Edit the `QUESTIONS` list at the
bottom of the file to try your own prompts.

---

## Reproducing the R tasks

Open [project.Rproj](project.Rproj) in RStudio, then for each task run the
corresponding `*_run.R` (or `run_01_02.R` for Task 3). The required
packages are from CRAN and the pharmaverse:
`sdtm.oak`, `pharmaverseraw`, `pharmaversesdtm`, `pharmaverseadam`,
`admiral`, `dplyr`, `gtsummary`, `gt`, `ggplot2`, `lubridate`, `stringr`.
