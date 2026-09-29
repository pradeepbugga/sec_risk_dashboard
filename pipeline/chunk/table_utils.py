import re

def classify_table(table_node):

    rows = table_node.xpath("./tbody/tr | ./tr")
    if len(rows) < 2:
        return "layout"

    numeric_rows = 0
    multi_cell_rows = 0
    total_rows = 0
    total_cells = 0
    numeric_cells = 0

    for row in rows:
        cells = row.xpath("./td | ./th")
        if not cells:
            continue

        total_rows += 1
        nonempty_cells = 0
        row_has_number = False

        for cell in cells:
            cell_text = " ".join(cell.itertext()).strip()
            if not cell_text:
                continue

            nonempty_cells += 1
            total_cells += 1

            if any(c.isdigit() for c in cell_text):
                numeric_cells += 1
                row_has_number = True

        if nonempty_cells >= 2:
            multi_cell_rows += 1

        if row_has_number:
            numeric_rows += 1

    if total_rows == 0 or total_cells == 0:
        return "layout"

    numeric_ratio = numeric_cells / total_cells
    row_numeric_ratio = numeric_rows / total_rows
    multi_cell_ratio = multi_cell_rows / total_rows

    # ---- DATA TABLE DECISION ----
    if (
        total_rows >= 3
        and multi_cell_ratio > 0.5
        and row_numeric_ratio > 0.5
        and numeric_ratio > 0.25
    ):
        return "data"

    return "layout"


def extract_row_tokens(row):

    # 1️⃣ Flatten all text in order
    raw = " ".join(row.itertext())

    raw = raw.replace("\xa0", " ")
    raw = re.sub(r'\s+', ' ', raw).strip()

    if not raw:
        return None

    # 2️⃣ Remove currency symbols and decorative dashes
    raw = raw.replace("$", "")
    raw = raw.replace("—", "")
    raw = raw.replace("–", "")

    # 3️⃣ Fix split parentheses like "(72 )"
    raw = re.sub(r'\(\s*(\d[\d,\.]*)\s*\)', r'-\1', raw)

    # 4️⃣ Fix split parentheses like "(72 )" where ) is separate token
    #raw = re.sub(r'\(\s*(\d[\d,\.]*)', r'-\1', raw)
    #raw = raw.replace(")", "")

    return raw.strip()

def parse_row(raw_text):

    # Find numeric values
    values = re.findall(r'-?\d[\d,\.]*', raw_text)

    if not values:
        return None

    # Label is everything before first number
    first_number = re.search(r'-?\d[\d,\.]*', raw_text)
    label = raw_text[:first_number.start()].strip()

    return label, values

def is_header_row(text):
    return (
        "Years Ended" in text
        or re.search(r'Dec\s+\d{1,2},\s*\d{4}', text)
        or re.search(r'\b20\d{2}\b', text) and "income" not in text.lower()
    )
def clean_header(text):

    # Remove month/day patterns entirely
    text = re.sub(r'Dec\s+\d{1,2},?', '', text)

    # Extract years
    years = re.findall(r'\b20\d{2}\b', text)

    # Extract leading descriptor (before first year)
    first_year_match = re.search(r'\b20\d{2}\b', text)

    if first_year_match:
        label = text[:first_year_match.start()].strip()
    else:
        label = text.strip()

    # Remove trailing junk like partial commas
    label = re.sub(r'\s+,?\s*$', '', label)

    return [label] + years

def normalize_data_table(table_node):

    rows = table_node.xpath(".//tr")
    structured = []

    for row in rows:

        raw = extract_row_tokens(row)

        if not raw:
            continue




        if is_header_row(raw):
            # clean header separately
            header = clean_header(raw)
            structured.append("Columns: " + " | ".join(header))
            continue

        parsed = parse_row(raw)

        if not parsed:
            continue

        label, values = parsed

        structured.append(f"{label} | " + " | ".join(values))

    return "\n".join(structured)