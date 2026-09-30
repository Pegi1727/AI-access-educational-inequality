#!/usr/bin/env python3
"""Inspect SDG4 quantitative data and its codebook."""
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent
quant_path = DATA_DIR / "SDG4_Quant_Data.csv"
codebook_path = DATA_DIR / "SDG4_Codebook.csv"

df = pd.read_csv(quant_path)
print("Columns:", df.columns.tolist())
print("Head (first 3 rows):\n", df.head(3))
print("Summary statistics:\n", df.describe(include="all"))

try:
    codebook = pd.read_csv(codebook_path)
    print("Codebook:\n", codebook.to_string(index=False))
except Exception as exc:
    print(f"Could not read codebook ({codebook_path}): {exc}")
