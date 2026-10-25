"""Shared helpers for the monthly reference loaders: where the month folders live, and cell cleaning."""
import re
from datetime import date, datetime
from pathlib import Path

REFERENCE_DIR = Path(__file__).resolve().parents[3] / "docs" / "reference"
MONTH_DIR = re.compile(r"\d{4}-\d{2}")


def latest_month_dir(root: Path = REFERENCE_DIR, today: str | None = None) -> Path:
    """Newest YYYY-MM folder (not after `today`'s month when given). Raises FileNotFoundError when there is none."""
    months = sorted(p for p in root.iterdir() if p.is_dir() and MONTH_DIR.fullmatch(p.name) and (today is None or p.name <= today[:7]))
    if not months:
        raise FileNotFoundError(f"no YYYY-MM folder in {root}")
    return months[-1]


def clean(raw: str, kind: str):
    """Convert one text cell. Kinds: str, pct (6.80% -> 0.068), num, int, date ("Oct 8, 2026").
    Blank, "-", "N/A" and unparseable cells become None."""
    s = (raw or "").strip()
    if s in ("", "-", "N/A", "n/a"):
        return None
    if kind == "str":
        return s
    if kind == "date":
        try:
            return datetime.strptime(s, "%b %d, %Y").date()
        except ValueError:
            return None
    t = s.replace("$", "").replace(",", "").replace("x", "")
    try:
        if kind == "pct":
            return round(float(t.replace("%", "")) / 100, 6)
        return int(float(t)) if kind == "int" else float(t)
    except ValueError:
        return None


def number(raw: str) -> float | None:
    """Plain number from a PDF table cell ("1,143", "$11,589", "24.10%" stay in their own units); None for NM or blank."""
    s = raw.replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_long_date(text: str) -> date | None:
    """First "Sept. 30, 2026"-style or "9/30/26"-style date in `text`, else None."""
    m = re.search(r"([A-Z][a-z]{2})[a-z]*\.? (\d{1,2}), (\d{4})", text)
    if m:
        try:
            return datetime.strptime(f"{m[1]} {m[2]} {m[3]}", "%b %d %Y").date()
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if m:
        y = int(m[3]) + (2000 if int(m[3]) < 100 else 0)
        return date(y, int(m[1]), int(m[2]))
    return None


def pdf_pages(path: Path) -> list[str]:
    """Text of each PDF page in reading order. PyMuPDF's sorted text keeps table rows on one line (its table finder
    splits decimals), which is what the Morningstar and Argus parsers rely on."""
    try:
        import pymupdf
    except ImportError as e:
        raise ImportError("PDF loaders need PyMuPDF: run through uv (it is a project dependency) or `uv run --with pymupdf`") from e
    with pymupdf.open(path) as doc:
        return [page.get_text("text", sort=True) for page in doc]
