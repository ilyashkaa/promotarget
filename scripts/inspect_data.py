
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/online_retail_II.xlsx")

def audit_transactions(df: pd.DataFrame) -> None:
    print("------------------")

    print("negative quantity:", (df["Quantity"] < 0).sum())
    print("zero quantity:", (df["Quantity"] == 0).sum())
    print("------------------")
    print("negative price:", (df["Price"] < 0).sum())
    print("zero price:", (df["Price"] == 0).sum())

    cancelled = df["Invoice"].astype(str).str.startswith("C")
    print("------------------")
    print("cancelled rows:", cancelled.sum())
    print(
        "cancelled invoices:",
        df.loc[cancelled, "Invoice"].nunique(),
    )

    print("duplicate rows:", df.duplicated().sum())
    print("------------------")
    print("first date:", df["InvoiceDate"].min())
    print("last date:", df["InvoiceDate"].max())
    print("------------------")
    print("unique customers:", df["Customer ID"].nunique())
    print("unique invoices:", df["Invoice"].nunique())


def audit_intersections(df: pd.DataFrame) -> None:
    negative_qty = df["Quantity"] < 0
    positive_qty = df["Quantity"] > 0
    zero_price = df["Price"] == 0
    cancelled = df["Invoice"].astype(str).str.startswith("C")

    print("----------------")

    print("negative quantity without cancellation:", (negative_qty & ~cancelled).sum())

    print("cancelled with positive quantity:", (cancelled & positive_qty).sum())

    print("zero price with positive quantity:", (zero_price & positive_qty).sum())


def main():
    excel = pd.ExcelFile(DATA_PATH)
    print("sheets:", excel.sheet_names)

    schema_reference = None
    invoice_sets = []


    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)
        print("------------------"*2)
        print(f"\n{sheet}")
        print("shape:", df.shape)
        print("\ncolumns:", df.columns.tolist())
        print("------------------")
        print("\ndata types:")
        print(df.dtypes)
        print("------------------")
        print("\nmissing values:")
        print(df.isna().sum())
        print("------------------")
        print("\nmissing percent:")
        print((df.isna().mean() * 100).round(2))
        print("------------------")
        print("\nfirst rows:")
        print(df.head())

        current_schema = df.dtypes
        print("------------------")
        if schema_reference is None:
            schema_reference = current_schema
        else:
            print(
                "\nschema matches:",
                current_schema.equals(schema_reference),
            )
        print("------------------")
        audit_transactions(df)
        audit_intersections(df)

        invoice_sets.append(set(df["Invoice"].astype(str)))

    common_invoices = invoice_sets[0] & invoice_sets[1]

    print("------------------")
    print("common invoices:", len(common_invoices))


if __name__ == "__main__":
    main()
