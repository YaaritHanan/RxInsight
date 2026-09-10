import os
import re
import streamlit as st

EVENT_API_URL = "https://api.fda.gov/drug/event.json"
LABEL_API_URL = "https://api.fda.gov/drug/label.json"
NOT_AVAILABLE = "Not available - consult a healthcare professional"

PATIENT_PAGE_SIZE = 1000
PATIENT_DEFAULT_MAX = 1_000
PATIENT_MAX = 100_000
CACHE_TTL = 3600
CACHE_TTL_GLOBAL = 86400

POLY_ORDER = [
    "Monopharmacy (1 medication)",
    "Minor polypharmacy (2-4 medications)",
    "Major polypharmacy (5-9 medications)",
    "Hyperpolypharmacy (>= 10 medications)",
]

SERIOUSNESS_FIELD_MAP = {
    "1": ("seriousnessdeath", "Death"),
    "2": ("seriousnessdisabling", "Disability"),
    "3": ("seriousnesshospitalization", "Hospitalization"),
    "4": ("seriousnesslifethreatening", "Life-threatening"),
}

AGE_UNIT_CONVERSIONS = {
    "800": 10.0, "decade": 10.0, "decades": 10.0,
    "801": 1.0, "year": 1.0, "years": 1.0, "yr": 1.0, "yrs": 1.0,
    "802": 1.0 / 12.0, "month": 1.0 / 12.0, "months": 1.0 / 12.0,
    "803": 1.0 / 52.1429, "week": 1.0 / 52.1429, "weeks": 1.0 / 52.1429,
    "804": 1.0 / 365.25, "day": 1.0 / 365.25, "days": 1.0 / 365.25,
    "805": 1.0 / (365.25 * 24), "hour": 1.0 / (365.25 * 24), "hours": 1.0 / (365.25 * 24),
    "806": 1.0 / (365.25 * 24 * 60), "minute": 1.0 / (365.25 * 24 * 60), "minutes": 1.0 / (365.25 * 24 * 60),
    "807": 1.0 / (365.25 * 24 * 60 * 60), "second": 1.0 / (365.25 * 24 * 60 * 60), "seconds": 1.0 / (365.25 * 24 * 60 * 60),
}

def get_openfda_api_key() -> str:
    """Reads API key from .streamlit/secrets.toml, root secrets.toml, or environment."""
    try:
        if "OPENFDA_API_KEY" in st.secrets:
            key = str(st.secrets["OPENFDA_API_KEY"]).strip()
            if key:
                return key
        if "openfda" in st.secrets and "api_key" in st.secrets["openfda"]:
            key = str(st.secrets["openfda"]["api_key"]).strip()
            if key:
                return key
    except Exception:
        pass

    for path in [os.path.join(".streamlit", "secrets.toml"), "secrets.toml", ".secrets.toml"]:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                match = re.search(
                    r'(?:OPENFDA_API_KEY|openfda_api_key|api_key)\s*=\s*["\']([^"\']+)["\']',
                    content,
                    re.IGNORECASE,
                )
                if match and match.group(1).strip():
                    return match.group(1).strip()
            except Exception:
                pass

    return os.getenv("OPENFDA_API_KEY", "").strip()

OPENFDA_API_KEY = get_openfda_api_key()
PATIENT_REQUEST_DELAY = 0.05 if OPENFDA_API_KEY else 0.25