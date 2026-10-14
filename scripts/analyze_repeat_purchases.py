
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/online_retail_II.xlsx")

SERVICE_CODES = {
    "POST",
    "DOT",
    "M",
    "D",
    "B",
    "BANK CHARGES",
}


def load_transactions() -> pd.DataFrame:
    excel = pd.ExcelFile(DATA_PATH)

    first = pd.read_excel(excel, sheet_name=0)
    second = pd.read_excel(excel, sheet_name=1)

    common_invoices = set(first["Invoice"]) & set(second["Invoice"])

    first_common = first[first["Invoice"].isin(common_invoices)]
    second_common = second[second["Invoice"].isin(common_invoices)]

    first_counts = first_common.value_counts(dropna=False, sort=False)
    second_counts = second_common.value_counts(dropna=False, sort=False)

    comparison = first_counts.to_frame("first_count").join(
        second_counts.to_frame("second_count"),
        how="outer",
        sort=False,
    ).fillna(0)
    
    different = comparison[
        comparison["first_count"] != comparison["second_count"]
    ]
    
    if not different.empty:
        raise ValueError(
            "Overlapping records do not match"
        )

    second = second[~second["Invoice"].isin(common_invoices)]

    transactions = pd.concat(
        [first, second],
        ignore_index=True,
    )

    print("combined rows:", len(transactions))

    return transactions


def get_valid_purchases(df: pd.DataFrame) -> pd.DataFrame:
    mask = (
        df["Customer ID"].notna()
        & (df["Quantity"] > 0)
        & (df["Price"] > 0)
        & ~df["Invoice"].astype(str).str.startswith("C")
        & ~df["StockCode"].astype(str).isin(SERVICE_CODES)
    )

    return df.loc[mask].copy()


def analyze_repeat_purchases(df: pd.DataFrame) -> None:
    purchase_days = (
        df[["Customer ID", "InvoiceDate"]]
        .assign(
            purchase_date=lambda x: x["InvoiceDate"].dt.normalize()
        )
        [["Customer ID", "purchase_date"]]
        .drop_duplicates()
        .sort_values(["Customer ID", "purchase_date"])
        .reset_index(drop=True)
    )

    days_per_customer = (
        purchase_days.groupby("Customer ID")["purchase_date"]
        .nunique()
    )

    returning_customers = (days_per_customer >= 2).sum()

    print("\n--- customer statistics ---")
    print("unique customers:", df["Customer ID"].nunique())

    print(
        "unique orders:",
        df[["Customer ID", "Invoice"]].drop_duplicates().shape[0],
    )

    print("purchase days:", len(purchase_days))
    print("returning customers:", returning_customers)

    print(
        "returning customers (%):",
        round(returning_customers / len(days_per_customer) * 100, 2),
    )

    purchase_days["previous_date"] = (
        purchase_days.groupby("Customer ID")["purchase_date"].shift(1)
    )

    purchase_days["days_between"] = (
        purchase_days["purchase_date"]
        - purchase_days["previous_date"]
    ).dt.days

    intervals = purchase_days["days_between"].dropna()

    print("\n--- purchase intervals ---")
    print(intervals.describe())

    for horizon in [7, 14, 30, 60, 90]:
        share = (intervals <= horizon).mean() * 100
        print(f"intervals <= {horizon} days: {share:.2f}%")


def main() -> None:
    transactions = load_transactions()

    valid = get_valid_purchases(transactions)

    print("valid product rows:", len(valid))
    print(
        "retained rows (%):",
        round(len(valid) / len(transactions) * 100, 2),
    )

    analyze_repeat_purchases(valid)


if __name__ == "__main__":
    main()
