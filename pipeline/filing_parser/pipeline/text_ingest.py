# this script downloads 10-K filings from the SEC EDGAR database for a list of tickers and saves them as HTML files.
# it uses edgartools package to ingest the filings.
# we will get 10-K filings from 2018 to 2025 (or 20-F in case of foreign companies)


from edgar import *
import pandas as pd
import os 
from filing_parser.utils.trim import trim_to_risk_heading
from filing_parser.parsers.form_detector import detect_form_type
from filing_parser.main import process_file


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
        

        sections = {}
        sections['company'] = ticker
        sections['year'] = i       

        filing = c.get_filings(form="10-K", year=i)
                             
        if len(filing) > 0:
            os.makedirs(f"./data/10K_Filings/processed/{ticker}/{i}", exist_ok=True)
            latest = filing.latest()
            
            tenk = latest.obj()
            risk_factors = tenk.get('Item 1A')
            mda = tenk.get('Item 7')

            if not risk_factors or not mda:
                parse = process_file(f"./data/10K_Filings/raw/{ticker}/{i}.html")
            
            #write risk factors to file
            
            if risk_factors:
                sections['risk_factors'] = {
                    "text": risk_factors
                    "extractor": "edgartools"
                } 
                print(f"Saved risk factors for {ticker} {i}")

            else:
                               
                if parse['risk_factors']:
                    sections['risk_factors'] = {
                        "text": parse['risk_factors'],
                        "extractor": parse['extractor']
                    }
                    print(f"Saved risk factors for {ticker} {i} using parser")

                else: 
                    print(f"{ticker} {i}: No risk factors found")
                    continue

            
            
            if mda:
                sections['mda'] = {
                    "text": mda,
                    "extractor": "edgartools"
                }
                print(f"Saved mda for {ticker} {i}")

            else:
                
                if parse['mda']:
                    sections['mda'] = {
                        "text": parse['mda'],
                        "extractor": parse['extractor']
                    }
                    print(f"Saved mdas for {ticker} {i} using parser")

                else: 
                    print(f"{ticker} {i}: No mda found")
                    continue
           

        else:
            os.makedirs(f"./data/20F_Filings/processed/{ticker}/{i}", exist_ok=True)
            filing = c.get_filings(form="20-F", year=i)
            if len(filing) > 0:
                latest = filing.latest()


                twentyf = latest.obj()

                risk_factors = twentyf.get('Item 3')
                risk_factors = trim_to_risk_heading(risk_factors)

                mda = twentyf.get('Item 5')

                if not risk_factors or not mda:
                    parse = process_file(f"./data/20F_Filings/raw/{ticker}/{i}.html")

                if risk_factors:
                    sections['risk_factors'] = risk_factors
                    sections['extractor'] = "edgartools"
                    print(f"Saved risk factors for {ticker} {i}")

                else:
                    
                    if parse['risk_factors']:
                        sections['risk_factors'] = trim_to_risk_heading(parse['risk_factors'])
                        sections['extractor'] = parse['extractor'] 
                        print(f"Saved risk factors for {ticker} {i} using parser")

                    else: 
                        print(f"{ticker} {i}: No risk factors found")
                        continue


                

                if mda:
                    sections['mda'] = mda
                    sections['extractor'] = "edgartools"
                    print(f"Saved mda for {ticker} {i}")

                else:
                    
                    if parse['mda']:
                        sections['mda'] = parse['mda']
                        sections['extractor'] = parse['extractor'] 
                        print(f"Saved mdas for {ticker} {i} using parser")

                    else: 
                        print(f"{ticker} {i}: No mda found")
                        continue
                
            else:
                print(f"No 10-K or 20-F filing found for {ticker} in {i}")
