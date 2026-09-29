# this script downloads 10-K filings from the SEC EDGAR database for a list of tickers and saves them as HTML files.
# it uses edgartools package to ingest the filings.
# we will get 10-K filings from 2018 to 2025 (or 20-F in case of foreign companies)


from edgar import *
import pandas as pd
import os 
from filing_parser.utils.trim import trim_to_risk_heading
from filing_parser.parsers.form_detector import detect_form_type

set_identity("pradeep.bugga0@gmail.com")




#load tickers from CSV
tickers = pd.read_csv("./data/tickers.csv")


for ticker in tickers['Ticker']:
    c = Company(ticker)
       

    #get filings for 2018 -2025

    
    for i in range(2018, 2026):
        #ignore if already downloaded
        if os.path.exists(f"./data/10K_Filings/processed/{ticker}/{i}.json"):
            continue
        if os.path.exists(f"./data/10K_Filings/processed/{ticker}/{i}.json"):
            continue

        sections = {}
        sections['company'] = ticker
        sections['year'] = i
        


        filing = c.get_filings(form="10-K", year=i)
                       

        
        if len(filing) > 0:
            os.makedirs(f"./data/10K_Filings/raw/{ticker}", exist_ok=True)
            latest = filing.latest()
            
            tenk = latest.obj()
            risk_factors = tenk['Item 1A']
            mda = tenk['Item 7']
            
            #write risk factors to file
            
            
            if risk_factors is None:
                print(f"{ticker} {i}: No risk factors found")
                continue

            with open(f"./data/10K_Filings/raw/{ticker}/{i}_risk_factors.txt", "w") as f:
                f.write(risk_factors)
            print(f"Saved risk factors for {ticker} {i}")

            if mda is None:
                print(f"{ticker} {i}: No MDA found")
                continue

            with open(f"./data/10K_Filings/raw/{ticker}/{i}_mda.txt", "w") as f:
                f.write(mda)
            print(f"Saved MDA for {ticker} {i}")
           


        else:
            os.makedirs(f"./data/20F_Filings/raw/{ticker}", exist_ok=True)
            filing = c.get_filings(form="20-F", year=i)
            if len(filing) > 0:
                latest = filing.latest()


                twentyf = latest.obj()

                risk_factors = twentyf['Item 3']
                risk_factors = trim_to_risk_heading(risk_factors)

                mda = twentyf['Item 5']


                if risk_factors is None:
                    print(f"{ticker} {i}: No risk factors found")
                    continue

                with open(f"./data/20F_Filings/raw/{ticker}/{i}_risk_factors.txt", "w") as f:
                    f.write(risk_factors)
                print(f"Saved risk factors for {ticker} {i}")

                if mda is None:
                    print(f"{ticker} {i}: No MDA found")
                    continue

                with open(f"./data/20F_Filings/raw/{ticker}/{i}_mda.txt", "w") as f:
                    f.write(mda)
                print(f"Saved MDA for {ticker} {i}")
                
            else:
                print(f"No 10-K or 20-F filing found for {ticker} in {i}")
