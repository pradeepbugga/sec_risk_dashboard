# this script downloads 10-K filings from the SEC EDGAR database for a list of tickers and saves them as HTML files.
# it uses edgartools package to ingest the filings.
# we will get 10-K filings from 2018 to 2025 (or 20-F in case of foreign companies)


from edgar import *
import pandas as pd
import os 
set_identity("pradeep.bugga0@gmail.com")


#load tickers from CSV
tickers = pd.read_csv("./data/tickers.csv")

for ticker in tickers['Ticker']:
    c = Company(ticker)
    
    os.makedirs(f"./data/10-K_Filings/raw/{ticker}", exist_ok=True)

    #get filings for 2018 -2025

    

    for i in range(2018, 2026):
        #ignore if already downloaded
        if os.path.exists(f"./data/10-K_Filings/raw/{ticker}/{i}.html"):
            continue

        filing = c.get_filings(form="10-K", year=i)

        if len(filing) > 0:
            latest = filing.latest()

            html_content = None

            for att in latest.attachments:
                if att.is_report and att.is_html:
                    content = att.download()

                    if isinstance(content, bytes):
                        html_content = content.decode("utf-8", errors="ignore")
                    else:
                        html_content = content

                    break

            if html_content is None:
                print(f"{ticker} {i}: 10-K document not found")
                continue

            if "<html" not in html_content.lower():
                print(f"{ticker} {i}: invalid HTML")
                continue

            with open(f"./data/10-K_Filings/raw/{ticker}/{i}.html", "w") as f:
                    f.write(html_content)

        else:
            filing = c.get_filings(form="20-F", year=i)
            if len(filing) > 0:
                latest = filing.latest()

               
            html_content = None

            for att in latest.attachments:
                if att.is_report and att.is_html:
                    content = att.download()

                    if isinstance(content, bytes):
                        html_content = content.decode("utf-8", errors="ignore")
                    else:
                        html_content = content

                    break

            if html_content is None:
                print(f"{ticker} {i}: 10-K document not found")
                continue

            if "<html" not in html_content.lower():
                print(f"{ticker} {i}: invalid HTML")
                continue

            else:
                print(f"No 10-K or 20-F filing found for {ticker} in {i}")
