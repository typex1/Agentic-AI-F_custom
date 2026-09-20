"""Step 2: Read files (port of the Langdock Code node `code2`).

Langdock needed this node because interpolating a FILE form field into a prompt
inserts the file *object*, not its text. In plain Python the step is trivial,
but it is kept as its own function so the six steps stay recognisable.
"""

from pathlib import Path


def read_text(path: str | Path) -> str:
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")
