"""
One-time conversion script: reads the raw Excel files and produces the two
CSV files the assignment expects (ethiopia_fi_unified_data.csv, reference_codes.csv).

The unified data workbook has two sheets:
  - Sheet 1: observations, events, targets
  - Impact_sheet: impact_links (has one extra column, parent_id, linking
    each impact_link back to the event that caused it)

This script merges both sheets into a single flat CSV, since impact_link
rows are just another record_type in the same unified schema.

Run from the project root:
    python src/convert_raw_data.py
"""

import os
import pandas as pd

RAW_DIR = "data/raw"


def convert():
    main_path = os.path.join(RAW_DIR, "ethiopia_fi_unified_data.xlsx")
    ref_path = os.path.join(RAW_DIR, "reference_codes.xlsx")

    if not os.path.exists(main_path):
        raise FileNotFoundError(f"{main_path} not found. Place the raw Excel files in data/raw/ first.")
    if not os.path.exists(ref_path):
        raise FileNotFoundError(f"{ref_path} not found. Place the raw Excel files in data/raw/ first.")

    try:
        main = pd.read_excel(main_path, sheet_name=0)
    except Exception as e:
        raise ValueError(f"Could not read the first sheet of {main_path}: {e}")

    try:
        impact = pd.read_excel(main_path, sheet_name="Impact_sheet")
    except ValueError as e:
        raise ValueError(
            f"'Impact_sheet' not found in {main_path}. "
            f"Confirm the sheet name matches exactly (case-sensitive). Original error: {e}"
        )

    if "record_type" not in main.columns:
        raise ValueError(f"Expected column 'record_type' not found in {main_path}, sheet 1.")

    main["parent_id"] = None
    missing_cols = set(main.columns) - set(impact.columns)
    if missing_cols:
        raise ValueError(f"Impact_sheet is missing expected column(s): {missing_cols}")
    impact = impact[main.columns]

    unified = pd.concat([main, impact], ignore_index=True)

    unified_out = os.path.join(RAW_DIR, "ethiopia_fi_unified_data.csv")
    unified.to_csv(unified_out, index=False)
    print(f"Wrote {unified_out} ({len(unified)} rows)")
    print(unified["record_type"].value_counts().to_string())

    try:
        ref = pd.read_excel(ref_path)
    except Exception as e:
        raise ValueError(f"Could not read {ref_path}: {e}")

    ref_out = os.path.join(RAW_DIR, "reference_codes.csv")
    ref.to_csv(ref_out, index=False)
    print(f"\nWrote {ref_out} ({len(ref)} rows)")


if __name__ == "__main__":
    convert()
