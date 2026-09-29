from edgar import *
import pandas as pd
import os
import json

from filing_parser.utils.trim import trim_to_risk_heading
from filing_parser.main import process_file

set_identity("pradeep.bugga0@gmail.com")

# Load tickers
tickers = pd.read_csv("./data/tickers.csv")


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


for ticker in tickers["Ticker"]:
    print(f"\nProcessing {ticker}")
    c = Company(ticker)

    for i in range(2018, 2026):

        output_path = f"./data/processed/{ticker}/{i}.json"
        if os.path.exists(output_path):
            print(f"Skipping {ticker} {i}")
            continue

        sections = {
            "company": ticker,
            "year": i,
            "sections": {}
        }

        parser_cache = None

        # ------------------------
        # Determine Filing Type
        # ------------------------
        filing_10k = c.get_filings(form="10-K", year=i)
        filing_20f = c.get_filings(form="20-F", year=i)

        if len(filing_10k) > 0:
            filing = filing_10k.latest()
            form_type = "10-K"
            risk_key = "Item 1A"
            mda_key = "Item 7"
            raw_path = f"./data/10K_Filings/raw/{ticker}/{i}.html"

        elif len(filing_20f) > 0:
            filing = filing_20f.latest()
            form_type = "20-F"
            risk_key = "Item 3"
            mda_key = "Item 5"
            raw_path = f"./data/20F_Filings/raw/{ticker}/{i}.html"

        else:
            print(f"No 10-K or 20-F filing found for {ticker} {i}")
            continue

        sections["form_type"] = form_type

        try:
            filing_obj = filing.obj()
        except Exception as e:
            print(f"{ticker} {i}: edgartools failed ({e})")
            continue

        # ------------------------
        # Extract Risk + MDA
        # ------------------------
        try:
            risk_text = filing_obj[risk_key]
        except KeyError:
            risk_text = None

        try:
            mda_text = filing_obj[mda_key]
        except KeyError:
            mda_text = None

        # 20F trimming
        if form_type == "20-F" and risk_text:
            risk_text = trim_to_risk_heading(risk_text)

        # Only parse HTML once if needed
        if (not risk_text or not mda_text) and os.path.exists(raw_path):
            parser_cache, tree = process_file(raw_path)

        # ------------------------
        # Risk
        # ------------------------
        if risk_text:
            sections["sections"]["risk_factors"] = {
                "text": risk_text,
                "extractor": "edgartools"
            }
            print(f"{ticker} {i}: Risk via edgartools")

        elif parser_cache and parser_cache.get("risk_factors"):
            parsed_risk = parser_cache["risk_factors"]

            if form_type == "20-F":
                parsed_risk = trim_to_risk_heading(parsed_risk)

            sections["sections"]["risk_factors"] = {
                "text": parsed_risk["text"],
                "extractor": parser_cache.get("extractor", "parser")
            }
            print(f"{ticker} {i}: Risk via parser")

        else:
            print(f"{ticker} {i}: Risk missing")

        # ------------------------
        # MDA
        # ------------------------
        if mda_text:
            sections["sections"]["mda"] = {
                "text": mda_text,
                "extractor": "edgartools"
            }
            print(f"{ticker} {i}: MDA via edgartools")

        elif parser_cache and parser_cache.get("mda"):
            parsed_mda = parser_cache["mda"]
            sections["sections"]["mda"] = {
                "text": parsed_mda["text"],                
                "extractor": parser_cache.get("extractor", "parser")
            }
            print(f"{ticker} {i}: MDA via parser")

        else:
            print(f"{ticker} {i}: MDA missing")

        # ------------------------
        # Save If Anything Extracted
        # ------------------------
        if sections["sections"]:
            save_json(output_path, sections)
            print(f"Saved {ticker} {i}")
        else:
            print(f"{ticker} {i}: Nothing extracted — not saving")