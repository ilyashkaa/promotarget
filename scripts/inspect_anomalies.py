
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


def get_valid_product_mask(df: pd.DataFrame) -> pd.Series:
    return (
        df["Customer ID"].notna()
        & (df["Quantity"] > 0)
        & (df["Price"] > 0)
        & ~df["Invoice"].astype(str).str.startswith("C")
        & ~df["StockCode"].astype(str).isin(SERVICE_CODES)
    )


def inspect_anomalies(df: pd.DataFrame) -> None:
    cancelled = df["Invoice"].astype(str).str.startswith("C")

    conditions = {
        "negative quantity without cancellation": (
            (df["Quantity"] < 0) & ~cancelled
        ),
        "zero price with positive quantity": (
            (df["Price"] == 0) & (df["Quantity"] > 0)
        ),
        "negative price": df["Price"] < 0,
        "cancelled with positive quantity": (
            cancelled & (df["Quantity"] > 0)
        ),
    }

    for name, mask in conditions.items():
        print("----------------")
        print(name)
        print("----------------")
        print("rows:", mask.sum())

        columns = [
            "Invoice",
            "StockCode",
            "Description",
            "Quantity",
            "Price",
            "Customer ID",
        ]

        print(df.loc[mask, columns].head(10).to_string(index=False))
        print(df.loc[mask, "StockCode"].value_counts().head(10))


def main() -> None:
    excel = pd.ExcelFile(DATA_PATH)


    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)
        print("----------------")
        print(sheet)
        inspect_anomalies(df)
        service_lines = df[df["StockCode"].astype(str).isin(SERVICE_CODES)]
        print("----------------")
        print(
            service_lines.groupby(["StockCode", "Description"], dropna=False)
            .agg(
                rows=("Invoice", "size"),
                invoices=("Invoice", "nunique"),
            )
            .to_string()
        )


if __name__ == "__main__":
    main()
