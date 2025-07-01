import os
import sqlite3

import pandas as pd

CLEANED_DATA_FOLDER = "cleaned_data"
CSV_NAME_PITCHERS = "American_League_Pitcher_Review"
CSV_NAME_PLAYERS = "American_League_Player_Review"
PITCHERS = "pitchers"
PLAYERS = "players"
DATASET_NAME_TO_FILE_MAP = {
    PITCHERS: f"{os.getcwd()}/{CLEANED_DATA_FOLDER}/{CSV_NAME_PITCHERS}_cleaned.csv",
    PLAYERS: f"{os.getcwd()}/{CLEANED_DATA_FOLDER}/{CSV_NAME_PLAYERS}_cleaned.csv"
}

DB_PATH = "db/baseball_data.sqlite"

conn = sqlite3.connect(DB_PATH)
print(f"Connected to SQLite database: {DB_PATH}")

try:
    for table_name, csv_path in DATASET_NAME_TO_FILE_MAP.items():
        print(f"\nProcessing {csv_path} into table: {table_name}")

        df = pd.read_csv(csv_path)

        print(f" - Loaded {df.shape[0]} rows with columns: {list(df.columns)}")

        # Drop rows where essential fields are missing to be sure DB is populated only with valid data
        df = df.dropna(subset=["Year", "Statistic Name", "Statistic Value"])

        df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f" - Imported successfully into table '{table_name}'!")

    print("\n All CSV files have been imported into the database successfully!")
except Exception as e:
    print(f"\n Error during import: {e}")
finally:
    conn.close()
    print("Closed SQLite connection.")
