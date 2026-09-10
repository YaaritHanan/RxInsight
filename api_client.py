import re
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests
import streamlit as st

import config
import data_processor as dp

SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=15, pool_maxsize=15, max_retries=2)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)

def _with_key(params=None):
    p = dict(params or {})
    if config.OPENFDA_API_KEY and "api_key" not in p:
        p["api_key"] = config.OPENFDA_API_KEY
    return p

def _keyed_url(url: str) -> str:
    if not config.OPENFDA_API_KEY:
        return url
    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["api_key"] = [config.OPENFDA_API_KEY]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))

def fda_get(url: str, params=None, timeout: int = 45, retries: int = 2):
    headers = {"User-Agent": "RxInsight/1.0", "Accept-Encoding": "gzip, deflate"}
    for attempt in range(retries):
        try:
            resp = SESSION.get(url, params=_with_key(params), timeout=timeout, headers=headers)
            if resp.status_code == 200:
                return resp, None
            if resp.status_code == 403:
                return resp, "openFDA returned 403 (Forbidden). Check API key in secrets.toml."
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            return resp, f"Request failed with status {resp.status_code}."
        except requests.RequestException as exc:
            if attempt < retries - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            return None, f"Request failed: {exc}"
    return None, "Request failed after retries."

def safe_json(resp):
    try:
        return resp.json()
    except (ValueError, AttributeError):
        return {}

def next_openfda_url(resp):
    link = resp.headers.get("Link", "") if resp else ""
    match = re.search(r"<([^>]+)>;\s*rel=\"?next\"?", link, flags=re.I)
    return match.group(1) if match else None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_label(drug_name: str):
    params = {
        "search": f'(openfda.generic_name:"{drug_name.lower()}" OR openfda.brand_name:"{drug_name.lower()}")',
        "limit": 1,
    }
    resp, err = fda_get(config.LABEL_API_URL, params=params, timeout=20)
    if not resp or resp.status_code != 200:
        return None, err or "Label request failed."
    records = safe_json(resp).get("results", [])
    if not records:
        return None, None
    rec = records[0]
    op = rec.get("openfda", {})
    return {
        "Generic Name": dp.get_first_available(op.get("generic_name"), op.get("substance_name")),
        "Brand Names": dp.get_first_available(op.get("brand_name")),
        "Indications / Purpose": dp.format_as_vertical_bullets(
            dp.get_first_available(rec.get("indications_and_usage"), rec.get("purpose"), joiner=" ")
        ),
        "Contraindications / Warnings": dp.format_as_vertical_bullets(
            dp.get_first_available(
                rec.get("contraindications"), rec.get("warnings"), rec.get("warnings_and_cautions"),
                rec.get("boxed_warning"), rec.get("precautions"), rec.get("general_precautions"), joiner="\n\n"
            )
        ),
        "Mechanism of Action / Pharmacology": dp.format_as_vertical_bullets(
            dp.get_first_available(
                rec.get("mechanism_of_action"), rec.get("clinical_pharmacology"),
                rec.get("pharmacodynamics"), rec.get("pharmacokinetics"), joiner=" "
            )
        ),
        "Pharmacological Class": dp.get_first_available(
            op.get("pharm_class_epc"), op.get("pharm_class_moa"), op.get("pharm_class_pe"), op.get("pharm_class_cs")
        ),
    }, None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_count_data(search: str = None, count_field: str = None, timeout: int = 30):
    params = {"count": count_field}
    if search:
        params["search"] = search
    resp, err = fda_get(config.EVENT_API_URL, params=params, timeout=timeout)
    if not resp or resp.status_code != 200:
        return [], err or "Count query failed."
    return safe_json(resp).get("results", []), None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_patient_reports(drug_name: str, max_reports: int):
    """
    Patient-level report harvester.
    sort='receivedate:asc' is strictly preserved to maintain chronological demographic consistency.
    """
    max_reports = int(max(1000, min(max_reports, config.PATIENT_MAX)))
    search = f'patient.drug.medicinalproduct:"{drug_name}"'
    reports, url, first = [], config.EVENT_API_URL, True
    params = {"search": search, "limit": min(config.PATIENT_PAGE_SIZE, max_reports), "sort": "receivedate:asc"}

    while url and len(reports) < max_reports:
        if not first:
            time.sleep(config.PATIENT_REQUEST_DELAY)
        resp, err = fda_get(url if first else _keyed_url(url), params=params if first else None, timeout=60)
        if not resp or resp.status_code != 200:
            return reports, err
        page = safe_json(resp).get("results", [])
        if not page:
            break
        reports.extend(page[: max_reports - len(reports)])
        if len(reports) >= max_reports:
            break
        url = next_openfda_url(resp)
        first = False
    return reports, None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_individual_serious_reports(drug_name: str, seriousness_field: str, limit: int = 200):
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}" AND {seriousness_field}:1',
        "limit": limit,
    }
    resp, err = fda_get(config.EVENT_API_URL, params=params, timeout=25)
    if not resp or resp.status_code != 200:
        return [], err
    rows = []
    for r in safe_json(resp).get("results", []):
        p = r.get("patient", {}) or {}
        rows.append({
            "Report ID": r.get("safetyreportid"),
            "Date": pd.to_datetime(r.get("receivedate"), format="%Y%m%d", errors="coerce"),
            "Age": p.get("patientonsetage"),
            "Sex": {"0": "Unknown", "1": "Male", "2": "Female"}.get(str(p.get("patientsex", "0")), "Unknown"),
            "Weight (kg)": p.get("patientweight"),
            "Number of Drugs": len(p.get("drug", []) or []),
        })
    return rows, None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_medicine_adverse_effects_for_period(drug_name: str, start_date: str, end_date: str):
    results, error = get_count_data(
        search=f'patient.drug.medicinalproduct:"{drug_name}" AND receivedate:[{start_date} TO {end_date}]',
        count_field="patient.reaction.reactionmeddrapt.exact",
    )
    return dp.normalize_count_results(results, "Adverse effect", limit=10), error

@st.cache_data(ttl=config.CACHE_TTL_GLOBAL, show_spinner=False)
def get_timeline(count_search: str = None):
    results, error = get_count_data(search=count_search, count_field="receivedate")
    if error:
        return None, error
    df = pd.DataFrame(results)
    if df.empty or not {"time", "count"}.issubset(df.columns):
        return None, "Timeline fields missing."
    df["Date"] = pd.to_datetime(df["time"], format="%Y%m%d", errors="coerce")
    df["Reports"] = pd.to_numeric(df["count"], errors="coerce")
    return df.dropna(subset=["Date", "Reports"]).sort_values("Date").reset_index(drop=True), None

@st.cache_data(ttl=config.CACHE_TTL, show_spinner=False)
def get_top_medicines_for_period(start_date: str, end_date: str):
    results, _ = get_count_data(
        search=f"receivedate:[{start_date} TO {end_date}]",
        count_field="patient.drug.medicinalproduct.exact",
    )
    return dp.normalize_count_results(results, "Medicine", limit=10), None

@st.cache_data(ttl=config.CACHE_TTL_GLOBAL, show_spinner=False)
def get_death_medicines():
    results, _ = get_count_data(
        search="seriousnessdeath:1",
        count_field="patient.drug.medicinalproduct.exact",
    )
    return dp.normalize_count_results(results, "Medicine"), None