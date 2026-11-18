"""Clean the UCI Online Retail dataset and create reproducible quality reports.

Usage:
  python src/clean_data.py --input "data/raw/Online Retail.xlsx"
  python src/clean_data.py --fetch-uci

The script preserves the original source file and writes derived files to data/processed/.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "processed"
REPORT_DIR = ROOT / "reports"
EXPECTED = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"]


def load_data(input_path: Path | None, fetch_uci: bool) -> pd.DataFrame:
    if fetch_uci:
        try:
            from ucimlrepo import fetch_ucirepo
        except ImportError as exc:
            raise SystemExit("Install dependencies first: pip install -r requirements.txt") from exc
        dataset = fetch_ucirepo(id=352)
        frame = dataset.data.original
        if frame is None or frame.empty:
            frame = dataset.data.features.copy()
            if dataset.data.targets is not None:
                frame = pd.concat([frame, dataset.data.targets], axis=1)
        return frame
    if input_path is None:
        raise SystemExit("Provide --input PATH or use --fetch-uci")
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}\nDownload the UCI file and place it in data/raw/.")
    if input_path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(input_path)
    if input_path.suffix.lower() == ".csv":
        return pd.read_csv(input_path)
    raise SystemExit("Supported input formats: .xlsx, .xls, .csv")


def normalize_text(series: pd.Series) -> pd.Series:
    return (series.astype("string").str.strip().str.replace(r"\s+", " ", regex=True))


def profile(df: pd.DataFrame) -> dict:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values_by_column": {str(k): int(v) for k, v in df.isna().sum().items()},
        "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
    }


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.copy()
    # Standardize header spelling and whitespace before validation.
    df.columns = [str(c).strip() for c in df.columns]
    missing_columns = sorted(set(EXPECTED) - set(df.columns))
    if missing_columns:
        raise ValueError(f"Dataset is missing expected columns: {missing_columns}. Found: {list(df.columns)}")
    df = df[EXPECTED].copy()
    before = profile(df)

    # Text cleanup: preserve IDs as strings so leading zeros/letters are not lost.
    for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
        df[col] = normalize_text(df[col])
    for col in ["InvoiceNo", "StockCode"]:
        df[col] = df[col].str.upper()
    df["Description"] = df["Description"].str.upper()
    df["Country"] = df["Country"].str.title()

    # Convert numeric/date columns safely; invalid values become missing and are audited.
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["CustomerID"] = pd.to_numeric(df["CustomerID"], errors="coerce")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce", dayfirst=True)

    invalid_numeric = int(df["Quantity"].isna().sum() + df["UnitPrice"].isna().sum())
    invalid_dates = int(df["InvoiceDate"].isna().sum())
    duplicate_rows = int(df.duplicated().sum())
    df = df.drop_duplicates().copy()

    # Rows without essential transaction/product/date/price information cannot support sales analysis.
    essential = ["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "Country"]
    missing_essential = int(df[essential].isna().any(axis=1).sum())
    df = df.dropna(subset=essential).copy()

    # Keep source cancellation/return transactions for auditability; flag them instead of deleting.
    df["IsCancellation"] = df["InvoiceNo"].str.startswith("C", na=False)
    df["IsReturnOrNegativeQty"] = df["Quantity"].lt(0)
    df["LineTotal"] = (df["Quantity"] * df["UnitPrice"]).round(2)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df["CustomerID"] = df["CustomerID"].astype("Int64").astype("string")
    df["Quantity"] = df["Quantity"].astype("int64")
    df["UnitPrice"] = df["UnitPrice"].astype("float64").round(2)

    # Deterministic ordering makes output reproducible.
    df = df.sort_values(["InvoiceDate", "InvoiceNo", "StockCode"], kind="stable").reset_index(drop=True)
    after = profile(df)
    audit = {
        "dataset": "UCI Online Retail (ID 352)",
        "before_cleaning": before,
        "cleaning_actions": {
            "duplicate_rows_removed": duplicate_rows,
            "rows_with_missing_essential_fields_removed": missing_essential,
            "invalid_numeric_cells_detected_in_Quantity_and_UnitPrice": invalid_numeric,
            "invalid_invoice_dates_detected": invalid_dates,
            "text_fields_trimmed_and_whitespace_normalized": ["InvoiceNo", "StockCode", "Description", "Country"],
            "identifier_fields_preserved_as_text": ["InvoiceNo", "StockCode", "CustomerID"],
            "date_converted_to_datetime": "InvoiceDate",
            "numeric_conversions": ["Quantity", "UnitPrice", "CustomerID"],
            "cancellations_and_negative_quantities": "retained and flagged; not silently deleted",
            "derived_column": "LineTotal = Quantity * UnitPrice",
            "missing_CustomerID": "retained as missing because customer identity is unknown; not imputed",
        },
        "after_cleaning": after,
        "rows_removed_total": int(before["rows"] - after["rows"]),
        "rows_retained": int(after["rows"]),
    }
    return df, audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean UCI Online Retail data")
    parser.add_argument("--input", type=Path, help="Path to raw .xlsx/.xls/.csv file")
    parser.add_argument("--fetch-uci", action="store_true", help="Fetch dataset 352 using ucimlrepo")
    args = parser.parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    raw = load_data(args.input, args.fetch_uci)
    cleaned, audit = clean_data(raw)
    output_csv = OUT_DIR / "online_retail_cleaned.csv"
    report_json = REPORT_DIR / "data_quality_report.json"
    missing_csv = REPORT_DIR / "missing_values_after_cleaning.csv"
    cleaned.to_csv(output_csv, index=False, encoding="utf-8-sig")
    report_json.write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    pd.DataFrame({"column": cleaned.columns, "missing_count": [int(cleaned[c].isna().sum()) for c in cleaned.columns], "missing_pct": [round(float(cleaned[c].isna().mean() * 100), 2) for c in cleaned.columns]}).to_csv(missing_csv, index=False)

    print("\nCLEANING COMPLETED")
    print(f"Input rows:     {audit['before_cleaning']['rows']:,}")
    print(f"Output rows:    {audit['after_cleaning']['rows']:,}")
    print(f"Rows removed:   {audit['rows_removed_total']:,}")
    print(f"Duplicates:     {audit['cleaning_actions']['duplicate_rows_removed']:,}")
    print(f"Output:         {output_csv.relative_to(ROOT)}")
    print(f"Quality report: {report_json.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
