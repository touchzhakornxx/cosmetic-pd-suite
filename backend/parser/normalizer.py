import re
import html
from typing import List, Dict, Optional


def _clean_text(t: str) -> str:
    # Remove HTML tags, decode entities, strip bullets/markers and extra whitespace
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    # remove common leading markers like ›, •, -, »
    t = re.sub(r"^[\s\-\u2022\u00BB\u203A›»]+", "", t)
    return ' '.join(t.split()).strip(' .:\n\t')


def _parse_percentage(s: str) -> Optional[float]:
    # Find percent patterns; prefer a max value if range present (e.g., '1-5%')
    m = re.search(r"(\d+(?:\.\d+)?)(?:\s*[-–~]\s*(\d+(?:\.\d+)?))?\s*%", s)
    if not m:
        return None
    if m.group(2):
        try:
            return max(float(m.group(1)), float(m.group(2)))
        except Exception:
            return float(m.group(1))
    try:
        return float(m.group(1))
    except Exception:
        return None


def parse_ingredient_text(raw: str) -> List[Dict[str, Optional[float]]]:
    """Parse raw INCI/ingredient text into a list of {name, percentage}.

    - Removes HTML and anchor tags, leading markers, and stray punctuation.
    - Extracts percentage (handles ranges by taking the larger value).
    - Returns majors (>1%) sorted descending by percentage, then minors in original order.
    """
    if not raw:
        return []

    # Normalize and remove weird separators
    cleaned_raw = html.unescape(raw)

    # Split on newlines, semicolons, and bullets first.
    # For commas, only split when the comma is NOT immediately followed by a digit —
    # this preserves INCI names like "1,2-Hexanediol" and "1,3-Butylene Glycol".
    parts = re.split(r"[\n\r;•›»]+|,(?!\d)", cleaned_raw)
    items: List[Dict[str, Optional[float]]] = []

    for part in parts:
        s = part.strip()
        if not s:
            continue
        s = _clean_text(s)
        if not s:
            continue
        pct = _parse_percentage(s)
        # remove percentage text from name
        name = re.sub(r"\d+(?:\.\d+)?(?:\s*[-–~]\s*\d+(?:\.\d+)?)?\s*%", "", s)
        # remove leading labels like 'Ingredients:', 'INCI', Thai 'ส่วนผสม'
        name = re.sub(r"^(Ingredients|INCI|ส่วนผสม)[:\s-]*", "", name, flags=re.IGNORECASE)
        name = _clean_text(name)
        if not name:
            continue
        # Discard tokens that contain no letters — pure numbers/symbols are never valid INCI names
        if not re.search(r'[A-Za-z]', name):
            continue
        items.append({"name": name, "percentage": pct})

    # Preserve original order for minors; sort majors (>1%) descending
    majors = [i for i in items if i.get('percentage') is not None and i['percentage'] > 1]
    minors = [i for i in items if not (i.get('percentage') is not None and i['percentage'] > 1)]
    majors_sorted = sorted(majors, key=lambda x: -x['percentage'])
    return majors_sorted + minors

