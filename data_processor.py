import re
import pandas as pd
import config


# ============================================================
# TEXT SANITIZATION & REGULATORY PARSING
# ============================================================

def clean_fda_text(text) -> str:
    """Sanitizes FDA regulatory text by removing bracketed references,
    embedded bullet artifacts, section numbering, and repetitive headers."""
    if not text:
        return config.NOT_AVAILABLE

    text = str(text)

    # 1. Remove bracketed cross-references, e.g., [see Warnings (5.1)], [see Dosage...]
    text = re.sub(r"\[see\s+[^\]]+\]", "", text, flags=re.IGNORECASE)

    # 2. Remove isolated section numbering references, e.g., ( 4 ), ( 5.1 )
    text = re.sub(r"\(\s*\d+(?:\.\d+)?\s*\)", "", text)

    # 3. Strip redundant section headers pasted into text paragraphs
    text = re.sub(
        r"^(?:INDICATIONS\s+AND\s+USAGE|CONTRAINDICATIONS|WARNINGS\s+AND\s+PRECAUTIONS|"
        r"MECHANISM\s+OF\s+ACTION|DOSAGE\s+AND\s+ADMINISTRATION|CLINICAL\s+PHARMACOLOGY)[:\s\-]*",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )

    # 4. Turn embedded bullet symbols and sub-bullets into clean sentence breaks
    text = re.sub(r"[\u2022\u00b7\u25cf\u25cb\u25aa]\s*", ". ", text)
    text = re.sub(r"(?<=\s)[o•\*]\s+", ". ", text)

    # 5. Remove subsection numbering artifacts like "1.1 " or "5 " at sentence starts
    text = re.sub(r"(?:^|\.\s+)\d+(?:\.\d+)*\s+", ". ", text)

    # 6. Normalize multiple periods and collapse irregular spacing
    text = re.sub(r"\.{2,}", ".", text)
    text = " ".join(text.split())

    return text.strip(" .")


def get_first_available(*fields, joiner="\n\n") -> str:
    """Inspects candidate fields and returns the first populated field,
    joining lists and cleaning formatting."""
    for f in fields:
        if f:
            raw = joiner.join(map(str, f)) if isinstance(f, list) else str(f)
            return clean_fda_text(raw)
    return config.NOT_AVAILABLE


def format_as_vertical_bullets(text, max_bullets: int = 15) -> str:
    """Splits sanitized FDA text into clean, deduplicated vertical bullet points,
    filtering out punctuation-only artifacts, ghost bullets, and fragments."""
    if not text or text == config.NOT_AVAILABLE:
        return config.NOT_AVAILABLE

    cleaned = clean_fda_text(text)

    # Split across sentence terminators
    raw_sentences = re.split(r"(?<=[.!?])\s+", cleaned)

    seen = set()
    valid_sentences = []

    for s in raw_sentences:
        # Strip residual bullet markers and punctuation
        item = s.strip(" .-•*o\t\r\n")

        # Drop empty strings, lone punctuation, or fragments shorter than 10 characters
        if not item or len(item) < 10:
            continue

        # Capitalize the first character
        formatted_item = item[0].upper() + item[1:]

        # Case-insensitive deduplication to eliminate repeated Highlights/Full Text
        dedup_key = formatted_item.lower()
        if dedup_key not in seen:
            seen.add(dedup_key)
            valid_sentences.append(formatted_item)

    if not valid_sentences:
        return config.NOT_AVAILABLE

    return "\n".join(f"- {sentence}" for sentence in valid_sentences[:max_bullets])


# ============================================================
# CLINICAL & POLYPHARMACY CATEGORIZATION
# ============================================================

def categorize_drugs(n) -> str:
    """Classifies total concomitant drug count into clinical polypharmacy tiers."""
    if pd.isna(n) or n <= 0:
        return "Unknown"
    if n == 1:
        return config.POLY_ORDER[0]
    if n <= 4:
        return config.POLY_ORDER[1]
    if n <= 9:
        return config.POLY_ORDER[2]
    return config.POLY_ORDER[3]


# ============================================================
# TABULAR NORMALIZATION & TIMELINE GROUPING
# ============================================================

def normalize_count_results(results, first_name: str, second_name: str = "Reports", limit: int = None) -> pd.DataFrame:
    """Normalizes openFDA count JSON results into a clean, sorted DataFrame."""
    if not results:
        return pd.DataFrame(columns=[first_name, second_name])
    df = pd.DataFrame(results).rename(columns={"term": first_name, "count": second_name})
    if second_name in df:
        df[second_name] = pd.to_numeric(df[second_name], errors="coerce")
    df = df.dropna(subset=[second_name]).sort_values(second_name, ascending=False).reset_index(drop=True)
    return df.head(limit).reset_index(drop=True) if limit else df


def period_bounds(period, granularity: str):
    """Calculates start and end date bounds (YYYYMMDD) for a given time period."""
    if granularity == "Year":
        year = int(period)
        return f"{year}0101", f"{year}1231", str(year)
    if granularity == "Quarter":
        year, quarter = int(str(period)[:4]), int(str(period)[-1])
        start = pd.Timestamp(year=year, month=(quarter - 1) * 3 + 1, day=1)
        return start.strftime("%Y%m%d"), (start + pd.offsets.QuarterEnd()).strftime("%Y%m%d"), str(period)
    start = pd.Timestamp(str(period))
    return start.strftime("%Y%m%d"), (start + pd.offsets.MonthEnd()).strftime("%Y%m%d"), str(period)


def add_time_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Appends Year, Quarter, and Month string identifiers to a timeline DataFrame."""
    d = df.copy()
    d["Year"] = d["Date"].dt.year
    d["Quarter"] = d["Date"].dt.year.astype(str) + " Q" + d["Date"].dt.quarter.astype(str)
    d["Month"] = d["Date"].dt.to_period("M").astype(str)
    return d


def group_timeline(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    """Aggregates reports based on the selected timeline granularity."""
    key = {"Year": "Year", "Quarter": "Quarter", "Month": "Month"}[granularity]
    out = df.groupby(key, as_index=False)["Reports"].sum()
    out["Period"] = out[key].astype(str)
    return out.reset_index(drop=True)


def selected_period_from_event(event, grouped: pd.DataFrame):
    """Extracts the selected bar period label from a Plotly click event."""
    try:
        indices = event.selection.point_indices
        if indices:
            return grouped.iloc[indices[0]]["Period"]
    except (AttributeError, TypeError, IndexError):
        pass
    return None


# ============================================================
# PATIENT COHORT PARSING & DEMOGRAPHIC STATS
# ============================================================

def normalize_age_to_years(patient: dict) -> float:
    """Converts openFDA patientonsetageunit to years and validates physiological range."""
    age = pd.to_numeric(patient.get("patientonsetage"), errors="coerce")
    if pd.isna(age):
        return float("nan")
    unit = str(patient.get("patientonsetageunit", "")).strip().lower()
    mult = config.AGE_UNIT_CONVERSIONS.get(unit)
    if mult is None:
        return float("nan")
    val = float(age) * mult
    return val if (0 <= val <= 120) else float("nan")


def reports_to_patient_df(reports: list) -> pd.DataFrame:
    """Transforms raw FAERS JSON records into a structured patient cohort DataFrame."""
    rows = []
    for r in reports:
        p = r.get("patient", {}) or {}
        drugs = p.get("drug", []) or []
        reactions = p.get("reaction", []) or []
        if not isinstance(drugs, list):
            drugs = [drugs] if drugs else []
        if not isinstance(reactions, list):
            reactions = [reactions] if reactions else []

        rows.append({
            "Report ID": r.get("safetyreportid"),
            "Age": normalize_age_to_years(p),
            "Weight (kg)": pd.to_numeric(p.get("patientweight"), errors="coerce"),
            "Number of Drugs": len(drugs),
            "Sex": {"0": "Unknown", "1": "Male", "2": "Female"}.get(str(p.get("patientsex", "0")), "Unknown"),
            "Report Date": pd.to_datetime(r.get("receivedate"), format="%Y%m%d", errors="coerce"),
            "Reactions": ", ".join(
                str(rx.get("reactionmeddrapt")) for rx in reactions if isinstance(rx, dict) and rx.get("reactionmeddrapt")
            ),
        })
    return pd.DataFrame(rows)


# ============================================================
# CUMULATIVE & 3D MATRIX CALCULATIONS
# ============================================================

def compute_cumulative_75(adverse_effects_df: pd.DataFrame):
    """Calculates the Pareto cutoff where cumulative adverse reactions reach 75%,
    clustering the residual effects into an 'Other' group."""
    tot_rx = adverse_effects_df["Reports"].sum()
    if tot_rx <= 0:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), 0

    df75 = adverse_effects_df.copy()
    df75["Cumulative %"] = df75["Reports"].cumsum() / tot_rx * 100
    cutoff = df75["Cumulative %"].gt(75).idxmax() if df75["Cumulative %"].gt(75).any() else len(df75) - 1
    df75 = df75.iloc[: cutoff + 1].copy()
    df75["% of Total Adverse Effects"] = df75["Reports"] / tot_rx * 100

    if len(df75) > 10:
        top_10 = df75.head(10).copy()
        other = df75.iloc[10:].copy()
        plot75 = pd.concat([
            top_10,
            pd.DataFrame([{
                "Adverse effect": "Other",
                "Reports": other["Reports"].sum(),
                "Cumulative %": other["Cumulative %"].iloc[-1],
                "% of Total Adverse Effects": other["Reports"].sum() / tot_rx * 100,
            }]),
        ], ignore_index=True)
    else:
        other = pd.DataFrame()
        plot75 = df75.copy()

    return df75, plot75, other, tot_rx


def prepare_3d_matrix(raw_reports: list):
    """Build the 3D matrix directly from aggregated counters.

    The previous implementation created one Python dictionary row for every
    reaction in every report and only then converted it to a DataFrame. With
    large cohorts this creates a very large temporary object.

    This version aggregates counts during the single pass over the reports and
    materializes only the final polypharmacy x top-10-effect matrix.
    """
    from collections import Counter, defaultdict

    effect_totals = Counter()
    cell_counts = defaultdict(lambda: [0, 0])  # reports, deaths

    for r in raw_reports:
        p = r.get("patient", {}) or {}
        drugs = p.get("drug", []) or []
        reactions = p.get("reaction", []) or []

        if not isinstance(drugs, list):
            drugs = [drugs] if drugs else []
        if not isinstance(reactions, list):
            reactions = [reactions] if reactions else []

        cat = categorize_drugs(len(drugs))
        if cat == "Unknown":
            continue

        is_d = int(str(r.get("seriousnessdeath", "0")) == "1")

        for rx in reactions:
            if isinstance(rx, dict):
                effect = rx.get("reactionmeddrapt")
                if effect:
                    effect = str(effect)
                    effect_totals[effect] += 1
                    cell_counts[(cat, effect)][0] += 1
                    cell_counts[(cat, effect)][1] += is_d

    if not effect_totals:
        return pd.DataFrame(), []

    top10_fx = [effect for effect, _ in effect_totals.most_common(10)]

    rows = []
    for cat in config.POLY_ORDER:
        for effect in top10_fx:
            reports, deaths = cell_counts.get((cat, effect), (0, 0))
            if reports:
                rows.append({
                    "Polypharmacy Category": cat,
                    "Adverse Effect": effect,
                    "Reports": reports,
                    "Death": deaths,
                    "Death Percentage (%)": round(deaths / reports * 100, 2),
                })

    if not rows:
        return pd.DataFrame(), top10_fx

    df_3d_agg = pd.DataFrame(rows)
    df_3d_agg["Polypharmacy Category"] = pd.Categorical(
        df_3d_agg["Polypharmacy Category"],
        categories=config.POLY_ORDER,
        ordered=True,
    )
    df_3d_agg["Adverse Effect"] = pd.Categorical(
        df_3d_agg["Adverse Effect"],
        categories=top10_fx,
        ordered=True,
    )
    df_3d_agg = df_3d_agg.sort_values(
        ["Polypharmacy Category", "Reports"],
        ascending=[True, False],
    ).reset_index(drop=True)

    return df_3d_agg, top10_fx
