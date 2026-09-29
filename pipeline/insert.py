from db.connection import get_db_connection
from persistence import create_filings_table, insert_filings
from glob import glob
import json
from pathlib import Path
import pandas as pd
from utils.normalize import normalize_text

CSV_PATH = "./data/tickers.csv"



if __name__ == "__main__":

    conn = get_db_connection()
    cur = conn.cursor()
    create_filings_table(cur)

    df = pd.read_csv(CSV_PATH)

    for file in Path("./data/processed").rglob("*.json"):

        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Failed loading {file}: {e}")
            continue

        ticker = data.get("company")
        year = data.get("year")
        form_type = data.get("form_type")

        # Safe company name lookup
        match = df.loc[df["Ticker"] == ticker, "Company_Name"]
        name = match.iloc[0] if not match.empty else None

        sections = data.get("sections", {})

        for section_name, section_data in sections.items():

            try:
                text = section_data.get("text")
                text = normalize_text(text)
                extractor = section_data.get("extractor")

                if not text:
                    continue

                insert_filings(
                    cur,
                    name,
                    ticker,
                    year,
                    form_type,
                    section_name,
                    text,
                    extractor
                )
            except Exception as e:
                print(f"Failed inserting section {section_name} for {ticker} {year}: {e}")
                conn.rollback()
                continue


    conn.commit()
    cur.close()
    conn.close()