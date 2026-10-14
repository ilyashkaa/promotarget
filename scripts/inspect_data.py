
from pathlib import Path

import pandas as pd


DATA_PATH = Path("data/raw/online_retail_II.xlsx")


def main():
    excel = pd.ExcelFile(DATA_PATH)
    print("sheets:", excel.sheet_names)

    schema_reference = None

    for sheet in excel.sheet_names:
        df = pd.read_excel(excel, sheet_name=sheet)

        print(f"\n{sheet}")
        print("shape:", df.shape)
        print("\ncolumns:", df.columns.tolist())

        print("\ndata types:")
        print(df.dtypes)

        print("\nmissing values:")
        print(df.isna().sum())

        print("\nmissing percent:")
        print((df.isna().mean() * 100).round(2))

        print("\nfirst rows:")
        print(df.head())

        current_schema = df.dtypes

        if schema_reference is None:
            schema_reference = current_schema
        else:
            print(
                "\nschema matches:",
                current_schema.equals(schema_reference),
            )


if __name__ == "__main__":
    main()
