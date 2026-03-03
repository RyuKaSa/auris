"""app_index.py -- Scan a directory and fuzzy-search for app paths."""
import os
from rapidfuzz import process, fuzz

SCAN_DIRS = [
    os.path.expanduser("~/Desktop"),
]

EXTENSIONS = {".exe", ".lnk", ".url"}


def build_index(dirs=SCAN_DIRS):
    """Scan directories and return {display_name: full_path}."""
    index = {}
    for directory in dirs:
        if not os.path.exists(directory):
            continue
        for entry in os.scandir(directory):
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in EXTENSIONS:
                name = os.path.splitext(entry.name)[0].lower()
                index[name] = entry.path
    return index


def search(query, index, threshold=40):
    """Fuzzy search the index. Returns (name, path) or None."""
    if not index:
        return None
    result = process.extractOne(
        query.lower(),
        index.keys(),
        scorer=fuzz.WRatio,
        score_cutoff=threshold,
    )
    if result:
        name = result[0]
        return name, index[name]
    return None