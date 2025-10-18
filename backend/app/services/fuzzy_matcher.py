from rapidfuzz import process, fuzz

def best_match(query: str, choices: list[str], threshold: int = 80):
    if not query or not choices:
        return None, 0
    match, score, _ = process.extractOne(query, choices, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, score
    return None, score
