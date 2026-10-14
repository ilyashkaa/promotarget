
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/online_retail_II.xlsx")


def audit_structure(df: pd.DataFrame, sheet: str) -> None:
    print("------------------")
    print(f"{sheet}")
    print("------------------")
    print("shape:", df.shape)
    print("columns:", df.columns.tolist())
    print("\ndata types:\n", df.dtypes, sep="")
    print("\nmissing values:\n", df.isna().sum(), sep="")
    print("\nmissing percent:\n", (df.isna().mean() * 100).round(2), sep="")
    print("\nfirst rows:\n", df.head(), sep="")


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


def audit_cross_sheet(first: pd.DataFrame, second: pd.DataFrame) -> None:
    first = first.copy()
    second = second.copy()
    first["Invoice"] = first["Invoice"].astype(str)
    second["Invoice"] = second["Invoice"].astype(str)

    common_invoices = set(first["Invoice"]) & set(second["Invoice"])
    first_common = first[first["Invoice"].isin(common_invoices)]
    second_common = second[second["Invoice"].isin(common_invoices)]

    print("----------------------------")
    print("common invoices:", len(common_invoices))
    print("rows with common invoices in first sheet:", len(first_common))
    print("rows with common invoices in second sheet:", len(second_common))

    for name, frame in (("first", first_common), ("second", second_common)):
        grouped = frame.groupby("Invoice")
        date_conflicts = grouped["InvoiceDate"].nunique(dropna=False).gt(1).sum()
        customer_conflicts = grouped["Customer ID"].nunique(dropna=False).gt(1).sum()
        print(f"{name} sheet invoices with multiple dates:", date_conflicts)
        print(f"{name} sheet invoices with multiple customers:", customer_conflicts)

    first_meta = first_common.groupby("Invoice").agg(
        first_date=("InvoiceDate", "min"),
        first_customer=("Customer ID", "first"),
    )
    second_meta = second_common.groupby("Invoice").agg(
        second_date=("InvoiceDate", "min"),
        second_customer=("Customer ID", "first"),
    )
    comparison = first_meta.join(second_meta, how="inner")

    same_date = comparison["first_date"].eq(comparison["second_date"])
    known_customers = comparison["first_customer"].notna() & comparison["second_customer"].notna()
    same_customer = known_customers & comparison["first_customer"].eq(comparison["second_customer"])

    print("same invoice dates:", same_date.sum())
    print("different invoice dates:", (~same_date).sum())
    print("same known customers:", same_customer.sum())
    print("invoices with unknown customer on either side:", (~known_customers).sum())
    print("different known customers:", (known_customers & ~same_customer).sum())
    print("\nexamples with different dates:")
    print(comparison.loc[~same_date].head())

    columns = list(first.columns)
    matching_unique_rows = first.drop_duplicates().merge(
        second.drop_duplicates(), on=columns, how="inner"
    )
    print("\nmatching unique full rows:", len(matching_unique_rows))

    first_items = first_common[["Invoice", "StockCode"]].drop_duplicates()
    second_items = second_common[["Invoice", "StockCode"]].drop_duplicates()
    matching_items = first_items.merge(
        second_items, on=["Invoice", "StockCode"], how="inner"
    )
    print("matching unique invoice-stockcode pairs:", len(matching_items))
    print("common invoices with matching stockcodes:", matching_items["Invoice"].nunique())


def compare_overlapping_rows(first: pd.DataFrame, second: pd.DataFrame) -> None:
    common = set(first["Invoice"]) & set(second["Invoice"])

    first_common = first[first["Invoice"].isin(common)]
    second_common = second[second["Invoice"].isin(common)]

    first_counts = first_common.value_counts(dropna=False)
    second_counts = second_common.value_counts(dropna=False)

    comparison = first_counts.to_frame("first_count").join(
        second_counts.to_frame("second_count"),
        how="outer",
        sort=False,
    ).fillna(0)

    different = comparison[
        comparison["first_count"] != comparison["second_count"]
    ]

    print("different row patterns:", len(different))
    rows_only_first = int(
        (comparison["first_count"] - comparison["second_count"])
        .clip(lower=0)
        .sum()
    )
    rows_only_second = int(
        (comparison["second_count"] - comparison["first_count"])
        .clip(lower=0)
        .sum()
    )
    print("rows only in first:", rows_only_first)
    print("rows only in second:", rows_only_second)

    print("\nexamples of differences:")
    print(different.head())

    if not different.empty:
        raise ValueError("Overlapping invoices contain different transactions")

    print("overlapping records match, including duplicate counts")
    print(
        "expected rows after removing second-sheet overlapping invoices:",
        len(first) + len(second) - len(second_common),
    )



def main() -> None:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH.resolve()}")

    excel = pd.ExcelFile(DATA_PATH)
    print("sheets:", excel.sheet_names)

    frames = []
    schema_reference = None

    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)
        audit_structure(df, sheet)

        if schema_reference is None:
            schema_reference = df.dtypes
        else:
            print("\nschema matches:", df.dtypes.equals(schema_reference))

        audit_transactions(df)
        audit_intersections(df)
        frames.append(df)

    if len(frames) == 2:
        audit_cross_sheet(frames[0], frames[1])
        compare_overlapping_rows(frames[0], frames[1])
    else:
        print("\ncross-sheet audit skipped: expected exactly two sheets")


if __name__ == "__main__":
    main()