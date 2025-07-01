import pandas as pd

SCRAPED_DATA_FOLDER = "scraped_data"
CLEANED_DATA_FOLDER = "cleaned_data"
CSV_NAMES = ["American_League_Pitcher_Review", "American_League_Player_Review"]

for csv_name in CSV_NAMES:
    # Load raw CSV with no headers because the real headers are in data rows
    df_raw = pd.read_csv(f"{SCRAPED_DATA_FOLDER}/{csv_name}.csv", header=None)

    # Drop the last column since it contains junk ("Top 25")
    df = df_raw.iloc[:, :-1]

    # Remove rows where second column has years — these rows are incorrectly parsed years
    mask_years = df.iloc[:, 1].astype(str).str.contains(r"\b(?:18|19|20)\d{2}\b", na=False)
    df = df[~mask_years]

    # Use the new first row as proper column headers
    df.columns = df.iloc[0]
    df = df[1:]  # remove header row from the data

    # Rename the first column to "Year" from "1991"
    df = df.rename(columns={df.columns[0]: "Year"})

    # Reset index for a clean DataFrame after dropping rows
    df = df.reset_index(drop=True)

    # Convert "Year" column to numeric to catch bad or missing years
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Strip leading/trailing spaces from all column names
    df.columns = df.columns.str.strip()

    # Strip spaces from all string values in the DataFrame for consistency
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

    # Convert any numeric-looking columns to real numeric types where possible
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    # Drop rows where Year is 2025, because data not available
    df = df[df["Year"] != 2025]

    # Remove rows that are repeated headers embedded in data ("Statistic" are definitely not a player name)
    repeated_headers = df["Statistic"] == "Statistic"
    df = df[~repeated_headers]

    # Rename 'Statistic' column to "Statistic Name" to reflect its meaning as the actual statistic name
    df = df.rename(columns={"Statistic": "Statistic Name"})
    # Rename '#' column to 'Statistic Value' to reflect its meaning as the actual statistic value
    df = df.rename(columns={"#": "Statistic Value"})

    df["Statistic Value"] = pd.to_numeric(df["Statistic Value"], errors="coerce")
    non_numeric = df[df["Statistic Value"].isna()]
    print("Potentially bad Statistic Values (converted to NaN):\n", non_numeric)
    # 1 bad value inside Player dataset. Need to clean it.
    df = df.dropna(subset=["Statistic Value"])
    non_numeric = df[df["Statistic Value"].isna()]
    print("Potentially bad Statistic Values (converted to NaN):\n", non_numeric)
    # No bad values now

    # Remove symbols like '*' for consistency
    df["Statistic Name"] = df["Statistic Name"].astype(str).str.replace(r"[*]", "", regex=True).str.strip()

    df = df.drop_duplicates()

    missing_summary = df.isnull().sum()
    print("Missing values:\n", missing_summary)
    # no missing values

    # Reset index after cleaning rows
    df = df.reset_index(drop=True)

    print(df.head(5))
    print(df.tail(5))
    print(df.sample(10))
    print(df.info())

    df.to_csv(f"{CLEANED_DATA_FOLDER}/{csv_name}_cleaned.csv", index=False)
