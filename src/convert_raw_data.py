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

    main = pd.read_excel(main_path, sheet_name=0)
    impact = pd.read_excel(main_path, sheet_name="Impact_sheet")

    main["parent_id"] = None
    impact = impact[main.columns]

    unified = pd.concat([main, impact], ignore_index=True)

    unified_out = os.path.join(RAW_DIR, "ethiopia_fi_unified_data.csv")
    unified.to_csv(unified_out, index=False)
    print(f"Wrote {unified_out} ({len(unified)} rows)")
    print(unified["record_type"].value_counts().to_string())

    ref = pd.read_excel(ref_path)
    ref_out = os.path.join(RAW_DIR, "reference_codes.csv")
    ref.to_csv(ref_out, index=False)
    print(f"\nWrote {ref_out} ({len(ref)} rows)")


if __name__ == "__main__":
    convert()
