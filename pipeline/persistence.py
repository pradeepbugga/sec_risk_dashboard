

def create_filings_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS filing_sections (
        id SERIAL PRIMARY KEY,
        company_name TEXT,
        ticker TEXT NOT NULL,
        year INTEGER NOT NULL,
        form_type TEXT NOT NULL,
        section_name TEXT NOT NULL,
        text TEXT NOT NULL,
        extractor TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ticker, year, section_name)
        )""")


def insert_filings(cur, company_name, ticker, year, form_type, section_name, text, extractor):
    cur.execute("""
        INSERT INTO filing_sections (company_name, ticker, year, form_type, section_name, text, extractor)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ticker, year, section_name) DO NOTHING
        """, (company_name, ticker, year, form_type, section_name, text, extractor))