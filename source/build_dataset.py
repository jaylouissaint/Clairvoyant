"""
Build a merged, analysis-ready dataset from:
- LinkedIn job postings
- A manual finance mapping table (LinkedIn company_name -> finance identifier)
- Financial metrics table (output of health_score.py)
- LinkedIn company follower counts (employee_counts.csv)
- Job skills table(s)

"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


# Columns dropped in the notebook 
DEFAULT_DROP_COLUMNS = [
    "description",
    "max_salary",
    "pay_period",
    "med_salary",
    "min_salary",
    "formatted_work_type",
    "applies",
    "original_listed_time",
    "remote_allowed",
    "job_posting_url",
    "application_url",
    "application_type",
    "expiry",
    "closed_time",
    "listed_time",
    "posting_domain",
    "sponsored",
    "work_type",
    "currency",
    "compensation_type",
    "normalized_salary",
    "zip_code",
    "fips",
    "Industry.1",
]


def read_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV with a helpful error message."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p.resolve()}")
    return pd.read_csv(p)


def clean_string_columns(df: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    """
    Normalize string columns:
    - strip whitespace
    - collapse internal whitespace
    - lowercase
    - convert literal "nan" string back to NaN

    Returns a copy.
    """
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            continue
        out[col] = (
            out[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
            .str.lower()
            .replace("nan", np.nan)
        )
    return out


def latest_follower_counts(employee_counts: pd.DataFrame) -> pd.DataFrame:
    """
    Keep the most recent follower_count per company_id.

    Equivalent to:
        employee_counts.loc[employee_counts.groupby('company_id')['time_recorded'].idxmax()]
    """
    if employee_counts.empty:
        return pd.DataFrame(columns=["company_id", "follower_count"])

    # Ensure time_recorded can be ordered
    ec = employee_counts.copy()
    if "time_recorded" in ec.columns:
        ec["time_recorded"] = pd.to_datetime(ec["time_recorded"], errors="coerce")
    idx = ec.groupby("company_id")["time_recorded"].idxmax()
    out = ec.loc[idx, ["company_id", "follower_count"]].copy()
    return out


def build_skills_table(skills_abr: pd.DataFrame, skills_full: pd.DataFrame) -> pd.DataFrame:
    """
    Build a job_id -> (skill_abr list, skill_name list) table.

    Mirrors the notebook logic:
      - join abr -> full
      - group by job_id and aggregate unique skills into comma-separated strings
    """
    if skills_abr.empty or skills_full.empty:
        return pd.DataFrame(columns=["job_id", "skill_abr", "skill_name"])

    skills = skills_abr.merge(skills_full, on="skill_abr", how="inner")
    agg = (
        skills.groupby("job_id", as_index=False)
        .agg(
            skill_abr=lambda x: ", ".join(sorted(set(map(str, x)))),
            skill_name=lambda x: ", ".join(sorted(set(map(str, x)))),
        )
    )
    return agg


def build_master_dataset(
    postings: pd.DataFrame,
    finance_mapping: pd.DataFrame,
    financial_metrics: pd.DataFrame,
    employee_counts: pd.DataFrame,
    skills_table: Optional[pd.DataFrame] = None,
    drop_columns: Sequence[str] = DEFAULT_DROP_COLUMNS,
) -> pd.DataFrame:
    """
    Merge and clean all inputs into a single "master" dataset.

    Parameters
    ----------
    postings:
        Raw job postings (must include: company_name, company_id, job_id).
    finance_mapping:
        Mapping from company_name -> finance_mapping (or equivalent identifier).
    financial_metrics:
        Output from health score computation; must include Company metrics keyed by Company name,
        or a compatible join key (see notes below).
    employee_counts:
        LinkedIn follower counts history.
    skills_table:
        Optional job_id -> skills aggregated table (columns: job_id, skill_abr, skill_name).
    drop_columns:
        Columns to drop after merges.

    Returns
    -------
    pd.DataFrame
        Cleaned, merged master dataset.

    Notes
    -----
    The notebook merged `financial_metrics` using:
        master_df.merge(finance, left_on='finance_mapping', right_on='Company')
    So `financial_metrics` should contain a `Company` column matching the finance_mapping values.
    """
    df = postings.copy()

    # Remove rows without company_name (matches notebook)
    if "company_name" in df.columns:
        df = df[~df["company_name"].isna()].copy()

    # Join finance mapping
    master = df.merge(finance_mapping, how="left", on="company_name")
    if "finance_mapping" in master.columns:
        master = master[~master["finance_mapping"].isna()].copy()

    # Join financial metrics
    if not financial_metrics.empty:
        if "Company" in financial_metrics.columns:
            master = master.merge(financial_metrics, how="left", left_on="finance_mapping", right_on="Company")
        else:
            # Fallback: attempt merge on finance_mapping if the column exists
            if "finance_mapping" in financial_metrics.columns:
                master = master.merge(financial_metrics, how="left", on="finance_mapping")

    # Join latest follower count
    followers = latest_follower_counts(employee_counts)
    if not followers.empty and "company_id" in master.columns:
        master = master.merge(followers, on="company_id", how="left")

    # Drop noisy columns
    cols_to_drop = [c for c in drop_columns if c in master.columns]
    if cols_to_drop:
        master = master.drop(columns=cols_to_drop)

    # Standardize column names and string columns
    if "company_name" in master.columns:
        master = master.rename(columns={"company_name": "company_linkedin"})
    master.columns = [c.lower() for c in master.columns]

    string_cols = [
        "company_linkedin",
        "company",
        "title",
        "location",
        "formatted_experience_level",
        "skills_desc",
    ]
    master = clean_string_columns(master, [c for c in string_cols if c in master.columns])

    # Optional skills join
    if skills_table is not None and not skills_table.empty and "job_id" in master.columns:
        master = master.merge(skills_table, on="job_id", how="left")

    return master


def build_dataset_from_paths(
    postings_csv: str | Path,
    finance_mapping_csv: str | Path,
    financial_metrics_csv: str | Path,
    employee_counts_csv: str | Path,
    skills_abr_csv: Optional[str | Path] = None,
    skills_full_csv: Optional[str | Path] = None,
) -> pd.DataFrame:
    """
    Convenience wrapper that reads inputs from disk and returns the cleaned master dataset.
    """
    postings = read_csv(postings_csv)
    fm = read_csv(finance_mapping_csv)
    fin = read_csv(financial_metrics_csv)
    ec = read_csv(employee_counts_csv)

    skills_table = None
    if skills_abr_csv and skills_full_csv:
        skills_abr = read_csv(skills_abr_csv)
        skills_full = read_csv(skills_full_csv)
        skills_table = build_skills_table(skills_abr, skills_full)

    return build_master_dataset(
        postings=postings,
        finance_mapping=fm,
        financial_metrics=fin,
        employee_counts=ec,
        skills_table=skills_table,
    )


if __name__ == "__main__":
    # Example CLI usage:
    # python -m src.build_dataset --postings data/postings.csv --finance-mapping data/finance_mapping.csv ...
    import argparse

    parser = argparse.ArgumentParser(description="Build the merged Clairvoyant dataset.")
    parser.add_argument("--postings", required=True, help="Path to postings.csv")
    parser.add_argument("--finance-mapping", required=True, help="Path to finance_mapping.csv")
    parser.add_argument("--financial-metrics", required=True, help="Path to final_financial_dataframe.csv (health score output)")
    parser.add_argument("--employee-counts", required=True, help="Path to employee_counts.csv")
    parser.add_argument("--skills-abr", default=None, help="Optional: path to job_skills.csv")
    parser.add_argument("--skills-full", default=None, help="Optional: path to skills.csv")
    parser.add_argument("--out", required=True, help="Output CSV path")

    args = parser.parse_args()

    df = build_dataset_from_paths(
        postings_csv=args.postings,
        finance_mapping_csv=args.finance_mapping,
        financial_metrics_csv=args.financial_metrics,
        employee_counts_csv=args.employee_counts,
        skills_abr_csv=args.skills_abr,
        skills_full_csv=args.skills_full,
    )
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"Wrote merged dataset: {args.out} | rows={len(df):,} cols={df.shape[1]:,}")
