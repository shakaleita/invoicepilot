"""Small, deterministic CSV serializer safe for spreadsheet viewing.

User-provided cells that could be interpreted as formulas are escaped.
"""
import csv
import io
import re

DANGEROUS = re.compile(r"^\s*[=+\-@\t\r]")

def serialize_csv(rows, columns):
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n", quoting=csv.QUOTE_ALL)
    writer.writerow(columns)
    for row in rows:
        values = []
        for value in row:
            text = "" if value is None else str(value)
            if DANGEROUS.match(text):
                text = "'" + text
            values.append(text)
        writer.writerow(values)
    return output.getvalue()
