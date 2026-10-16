"""Deterministic, conservative checks: uncertainty is not an approval."""
import re
import unicodedata
from difflib import SequenceMatcher

WARNING = ("GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink "
           "alcoholic beverages during pregnancy because of the risk of birth defects. "
           "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
           "operate machinery, and may cause health problems.")
FIELDS = ("brand", "class_type", "abv", "net_contents", "producer", "country_of_origin")

def normalize(s):
    s = unicodedata.normalize("NFKC", s or "").casefold().replace("’", "'")
    return re.sub(r"[^\w]+", " ", s).strip()

def compact(s):
    return re.sub(r"\s+", " ", s or "").strip()

def amount(s):
    m = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*(ml|m\s*l|cl|l|liters?|litres?|fl\.?\s*oz|ounces?)\b", s, re.I)
    if not m: return None
    v = float(m.group(1)); unit = re.sub(r"\s", "", m.group(2).lower()).replace('.', '')
    return round(v * ({'l':1000,'liter':1000,'liters':1000,'litre':1000,'litres':1000,'cl':10,'floz':29.5735295625,'ounce':29.5735295625,'ounces':29.5735295625}.get(unit,1)), 2)

def abv(s):
    m = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*%\s*(?:alc(?:ohol)?\.?\s*(?:/|by)?\s*vol(?:ume)?\.?)?", s, re.I)
    if m: return float(m.group(1))
    m = re.search(r"(?<!\d)(\d+(?:\.\d+)?)\s*proof\b", s, re.I)
    return float(m.group(1))/2 if m else None

def result(field, expected, observed, status, explanation):
    return dict(field=field, expected=expected, observed=observed, status=status, explanation=explanation)

def verify_field(field, expected, lines):
    text = " ".join(lines)
    if not expected.strip():
        return result(field, expected, "", "not_checked", "No application value supplied")
    if field in ('abv', 'net_contents'):
        parser = abv if field == 'abv' else amount
        exp = parser(expected)
        if exp is None: return result(field, expected, "", "manual_review", "Application value could not be parsed")
        # Scan individual OCR lines to avoid accidentally combining unrelated numbers.
        matches = [(line, parser(line)) for line in lines]
        matches = [(line, val) for line, val in matches if val is not None]
        if not matches: return result(field, expected, "", "manual_review", "Value not reliably found in image")
        matched = next(((line,val) for line,val in matches if abs(val-exp)<0.011), None)
        if matched: return result(field, expected, matched[0], "match", "Equivalent numeric value")
        return result(field, expected, matches[0][0], "mismatch", "Detected numeric value differs; confirm label context")
    target = normalize(expected)
    if not target: return result(field, expected, "", "not_checked", "No value supplied")
    normalized_text = normalize(text)
    if target in normalized_text:
        return result(field, expected, expected, "match", "Text found (case and punctuation ignored)")
    # Join lines for labels broken across multiple OCR boxes; near matches are NOT approved.
    candidates = lines + [text]
    best = max(candidates, key=lambda x: SequenceMatcher(None,target,normalize(x)).ratio(), default='')
    score = SequenceMatcher(None,target,normalize(best)).ratio()
    if score >= .72: return result(field, expected, best, "manual_review", "Possible OCR/format variation; agent confirmation required")
    return result(field, expected, best if score >= .45 else "", "manual_review", "Expected text not confidently located")

def verify_warning(lines):
    text = compact(" ".join(lines))
    normalized = normalize(text)
    wanted = normalize(WARNING)
    if wanted in normalized:
        # OCR cannot reliably prove boldface or physical text size.
        return result('government_warning', 'Standard government warning', 'Full text detected', 'manual_review', 'Wording detected; agent must confirm uppercase heading, boldface, size and layout')
    if 'government warning' in normalized:
        return result('government_warning', 'Standard government warning', 'Partial warning detected', 'manual_review', 'Warning detected but full exact wording/format cannot be verified')
    return result('government_warning', 'Standard government warning', 'Not detected', 'manual_review', 'Warning not detected; inspect artwork before determining compliance')

def validate(application, lines):
    checks = [verify_field(f, str(application.get(f) or ''), lines) for f in FIELDS]
    checks.append(verify_warning(lines))
    statuses = [c['status'] for c in checks]
    overall = 'mismatch' if 'mismatch' in statuses else ('manual_review' if 'manual_review' in statuses else 'match')
    return dict(status=overall, checks=checks)
