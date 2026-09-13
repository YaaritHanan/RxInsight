import pandas as pd
import plotly.express as px
import streamlit as st

import config
from ui_styles import apply_ui_styling
from api_client import (
    get_death_medicines, get_timeline, get_label,
    get_count_data, get_patient_reports, get_individual_serious_reports,
    get_top_medicines_for_period, get_medicine_adverse_effects_for_period,
)
from data_processor import (
    add_time_groups, group_timeline, period_bounds,
    selected_period_from_event, normalize_count_results,
    reports_to_patient_df, categorize_drugs,
    compute_cumulative_75, prepare_3d_matrix,
)
from visualizations import timeline_chart, render_metric_squares, render_3d_matrix

# Initialize Custom CSS Styling
apply_ui_styling()

st.caption("Disclaimer: For informational and educational purposes only. RxInsight does not provide medical advice, diagnosis, or treatment recommendations. Adverse event data are based on reported cases and do not establish causality.")

st.title("RxInsight: Pharmacovigilance & Drug Safety ℞☤💊")

if config.OPENFDA_API_KEY:
    st.caption(f"⚡ **Fast Mode Active:** Key verified via `secrets.toml` (`...{config.OPENFDA_API_KEY[-4:]}`).")
else:
    st.caption("No API key detected — verify `OPENFDA_API_KEY` in `.streamlit/secrets.toml`.")

# ------------------------------------------------------------
# 1. Top Death Reports Slider & Chart
# ------------------------------------------------------------
st.markdown("---")
st.markdown("## Top 10 Medicines with the Most Death Reports")
death_limit = st.slider("Number of top medications to display:", 5, 25, 10, key="death_limit")
death_df, _ = get_death_medicines()

if not death_df.empty:
    top_death = death_df.head(death_limit)
    st.dataframe(top_death, width="stretch", hide_index=True)
    fig_d = px.bar(
        top_death.sort_values("Reports"),
        x="Reports",
        y="Medicine",
        orientation="h",
        text="Reports",
        title=f"Top {death_limit} Medicines in Reports with Death",
    )
    fig_d.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_d.update_layout(height=500, margin=dict(l=20, r=20, t=70, b=20))
    st.plotly_chart(fig_d, width="stretch")

# ------------------------------------------------------------
# 2. General Timeline
# ------------------------------------------------------------
st.markdown("---")
st.markdown("## 📈 FDA Adverse-Event Reports Over Time")
general_granularity = st.selectbox("Time resolution:", ["Year", "Quarter", "Month"], key="timeline_granularity")
general_timeline, _ = get_timeline()

if general_timeline is not None and not general_timeline.empty:
    grouped = group_timeline(add_time_groups(general_timeline), general_granularity)
    ev = timeline_chart(
        grouped,
        f"FDA Adverse-Event Reports by {general_granularity}",
        "fda_timeline_chart",
        general_granularity,
        "Click a bar to load Top 10 medicines.",
    )
    sel = selected_period_from_event(ev, grouped)
    if sel:
        start, end, label = period_bounds(sel, general_granularity)
        top_p, _ = get_top_medicines_for_period(start, end)
        st.markdown(f"### 💊 Top 10 Medicines — {label}")
        if not top_p.empty:
            st.dataframe(top_p, width="stretch", hide_index=True)

# ------------------------------------------------------------
# 3. Drug Search
# ------------------------------------------------------------
st.markdown("## Enter drug name (Brand or Generic):")
medicinalproduct = st.text_input(
    "Drug name",
    value="",
    placeholder="e.g. aspirin, ibuprofen, Eliquis",
    label_visibility="collapsed",
).strip()
search_drug = medicinalproduct.upper() if medicinalproduct else ""

if medicinalproduct:
    st.markdown(f"## General Drug Information — {search_drug}")
    label_info, _ = get_label(medicinalproduct)
    if label_info:
        for f, v in label_info.items():
            with st.expander(f, expanded=f in ("Generic Name", "Indications / Purpose")):
                st.write(v)

    # Adverse Effects Trend
    st.markdown("---")
    st.markdown(f"## 📈 Adverse-Event Trend for {search_drug}")
    med_gran = st.selectbox("Time resolution for selected medicine:", ["Year", "Quarter", "Month"], key="med_gran")
    med_time, _ = get_timeline(f'patient.drug.medicinalproduct:"{search_drug}"')

    if med_time is not None and not med_time.empty:
        g_med = group_timeline(add_time_groups(med_time), med_gran)
        ev_med = timeline_chart(
            g_med,
            f"{search_drug} — Adverse-Event Reports by {med_gran}",
            "med_chart",
            med_gran,
            "Click a bar to load Top 10 adverse effects.",
        )
        sel_m = selected_period_from_event(ev_med, g_med)
        if sel_m:
            st_val, en_val, lb_val = period_bounds(sel_m, med_gran)
            top_period_ae, _ = get_medicine_adverse_effects_for_period(search_drug, st_val, en_val)
            if not top_period_ae.empty:
                st.dataframe(top_period_ae, width="stretch", hide_index=True)

    # Top 10 Adverse Effects
    st.markdown("---")
    st.markdown(f"## Top 10 Adverse Effects — {search_drug} 💊")
    ae_res, _ = get_count_data(
        search=f'patient.drug.medicinalproduct:"{search_drug}"',
        count_field="patient.reaction.reactionmeddrapt.exact",
    )
    ae_df = normalize_count_results(ae_res, "Adverse effect")

    if not ae_df.empty:
        c1, c2 = st.columns([1, 1.5])
        c1.dataframe(ae_df.head(10), width="stretch", hide_index=True)
        fig_ae = px.bar(
            ae_df.head(10).sort_values("Reports"),
            x="Reports",
            y="Adverse effect",
            orientation="h",
            title=f"Top 10 Adverse Effects — {search_drug}",
        )
        c2.plotly_chart(fig_ae, width="stretch")

    # 75% Pareto Cumulative Analysis
    st.markdown("---")
    st.markdown("## Adverse Effects Responsible for 75% of Reports 📊")
    if not ae_df.empty:
        df75, plot75, other, tot_rx = compute_cumulative_75(ae_df)
        if not df75.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total reports", f"{int(tot_rx):,}")
            m2.metric("Effects needed for 75%", len(df75))
            m3.metric("Cumulative coverage", f"{df75['Cumulative %'].iloc[-1]:.1f}%")

            fig75 = px.bar(
                plot75.sort_values("Reports"),
                x="Reports",
                y="Adverse effect",
                orientation="h",
                title=f"Adverse Effects Contributing to 75% Cumulative Reports — {search_drug}",
                hover_data={"Reports": True, "Cumulative %": ":.1f", "% of Total Adverse Effects": ":.1f"},
            )
            fig75.update_layout(height=550, margin=dict(l=20, r=20, t=70, b=20))
            st.plotly_chart(fig75, width="stretch")

            cols = ["Adverse effect", "Reports", "Cumulative %", "% of Total Adverse Effects"]
            with st.expander("🔍 View detailed adverse effects included in the 75% group"):
                st.dataframe(df75[cols].round({"Cumulative %": 1, "% of Total Adverse Effects": 1}), width="stretch", hide_index=True)
            if not other.empty:
                with st.expander("🔍 View adverse effects grouped under 'Other' (Excludes Top 10)"):
                    st.dataframe(other[cols].round({"Cumulative %": 1, "% of Total Adverse Effects": 1}), width="stretch", hide_index=True)

    # ------------------------------------------------------------
    # 4. Patient-Level Data & Demographics
    # ------------------------------------------------------------
    st.markdown("---")
    st.markdown("## 👤 Patient-Level Data & Statistics")
    pat_limit = st.slider(
        "Maximum patient-level reports to load:",
        1000, int(config.PATIENT_MAX), int(config.PATIENT_DEFAULT_MAX), 1000,
        key="pat_limit",
    )

    if pat_limit >= 100_000:
        st.caption(
            "ℹ️ Large cohort mode: records are downloaded in pages and reduced "
            "to only the fields required by RxInsight."
        )

    if st.button("🔄 Refresh FDA patient data"):
        get_patient_reports.clear()
        get_individual_serious_reports.clear()
        st.rerun()

    with st.spinner(f"Loading {int(pat_limit):,} FDA reports..."):
        raw_reps, _ = get_patient_reports(search_drug, pat_limit)
    pat_df = reports_to_patient_df(raw_reps)

    if not pat_df.empty:
        tot_pat = len(pat_df)
        sex_c = pat_df["Sex"].value_counts().reindex(["Male", "Female", "Unknown"], fill_value=0)
        sex_p = (sex_c / tot_pat * 100).round(1)

        # Sex Distribution Squares
        st.markdown("### Sex Distribution")
        render_metric_squares([
            {"title": "Male", "value": f"{sex_c['Male']:,}", "sub": f"{sex_p['Male']:.1f}%"},
            {"title": "Female", "value": f"{sex_c['Female']:,}", "sub": f"{sex_p['Female']:.1f}%"},
            {"title": "Unknown", "value": f"{sex_c['Unknown']:,}", "sub": f"{sex_p['Unknown']:.1f}%"},
        ])

        fig_s = px.bar(
            pd.DataFrame({
                "Sex": ["Male", "Female", "Unknown"],
                "Reports": [sex_c[s] for s in ["Male", "Female", "Unknown"]],
                "Pct": [sex_p[s] for s in ["Male", "Female", "Unknown"]],
            }),
            x="Sex",
            y="Reports",
            color="Sex",
            color_discrete_map={"Male": "#1f77b4", "Female": "#e377c2", "Unknown": "#7f7f7f"},
            text="Pct",
        )
        fig_s.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_s.update_layout(height=380, showlegend=False, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_s, width="stretch")

        # Age Statistics per Sex (Square Cards)
        st.markdown("### Age Statistics")
        pat_df["Age"] = pd.to_numeric(pat_df["Age"], errors="coerce")
        pat_df.loc[(pat_df["Age"] < 0) | (pat_df["Age"] > 120), "Age"] = float("nan")

        for s_val in ["Male", "Female", "Unknown"]:
            sub_ages = pat_df.loc[pat_df["Sex"] == s_val, "Age"].dropna()
            st.markdown(f"#### {s_val}")
            render_metric_squares([
                {"title": f"Mean Age ({s_val})", "value": f"{sub_ages.mean():.1f}" if not sub_ages.empty else "N/A", "sub": "Years"},
                {"title": f"Median Age ({s_val})", "value": f"{sub_ages.median():.1f}" if not sub_ages.empty else "N/A", "sub": "Years"},
                {"title": "Valid Records", "value": f"{len(sub_ages):,}", "sub": "Patients"},
            ])

        c = st.columns(4)
        c[0].metric("Mean Age — All Patients", f"{pat_df['Age'].mean():.1f} years" if pd.notna(pat_df['Age'].mean()) else "N/A")
        c[1].metric("Median Age — All Patients", f"{pat_df['Age'].median():.1f} years" if pd.notna(pat_df['Age'].median()) else "N/A")
        c[2].metric("Average Drugs per Report", f"{pat_df['Number of Drugs'].mean():.1f}" if pd.notna(pat_df['Number of Drugs'].mean()) else "N/A")
        c[3].metric("Average Weight", f"{pat_df['Weight (kg)'].mean():.1f} kg" if pd.notna(pat_df['Weight (kg)'].mean()) else "N/A")

        # Medication Categories
        st.markdown("### Medication categories 💊")
        pat_df["Poly Category"] = pat_df["Number of Drugs"].map(categorize_drugs)
        cat_sum = pat_df["Poly Category"].value_counts().reindex(config.POLY_ORDER, fill_value=0)
        st.dataframe(
            pd.DataFrame({
                "Pharmacy Category": cat_sum.index,
                "Total Reports": cat_sum.values,
                "Percentage (%)": (cat_sum.values / tot_pat * 100).round(1),
            }),
            width="stretch",
            hide_index=True,
        )

        poly_sex = (
            pat_df.groupby(["Poly Category", "Sex"], as_index=False)["Report ID"]
            .count()
            .rename(columns={"Report ID": "Reports"})
        )
        full_idx = pd.MultiIndex.from_product(
            [config.POLY_ORDER, ["Male", "Female", "Unknown"]], names=["Poly Category", "Sex"]
        )
        poly_sex_df = poly_sex.set_index(["Poly Category", "Sex"]).reindex(full_idx, fill_value=0).reset_index()
        fig_ps = px.bar(
            poly_sex_df,
            x="Poly Category",
            y="Reports",
            color="Sex",
            barmode="group",
            color_discrete_map={"Male": "#1f77b4", "Female": "#e377c2", "Unknown": "#7f7f7f"},
            text="Reports",
        )
        fig_ps.update_traces(textposition="outside")
        fig_ps.update_layout(height=480, margin=dict(l=20, r=20, t=60, b=40))
        st.plotly_chart(fig_ps, width="stretch")

    # ------------------------------------------------------------
    # 5. Seriousness Groups & Individual Reports
    # ------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"## Seriousness Groups — Aggregate Statistics for {search_drug}")
    if raw_reps:
        n_c = len(raw_reps)
        ser_stats = pd.DataFrame([
            {
                "Code": c,
                "Category": lbl,
                "Reports": sum(1 for r in raw_reps if str(r.get(fld, "0")) == "1"),
            }
            for c, (fld, lbl) in config.SERIOUSNESS_FIELD_MAP.items()
        ])
        ser_stats["% of Sample"] = (ser_stats["Reports"] / n_c * 100).round(1)

        c_s1, c_s2 = st.columns([1, 1.4])
        c_s1.dataframe(ser_stats, width="stretch", hide_index=True)
        fig_ser = px.bar(
            ser_stats,
            x="Category",
            y="% of Sample",
            color="Category",
            text="% of Sample",
            title=f"Seriousness Groups — {search_drug} (n={n_c:,})",
        )
        fig_ser.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_ser.update_layout(height=420, showlegend=False, margin=dict(l=20, r=20, t=60, b=20))
        c_s2.plotly_chart(fig_ser, width="stretch")

    st.markdown("---")
    st.markdown("## Seriousness Reports — Individual")
    ser_choice = st.selectbox(
        "Choose the required seriousness:",
        ["1", "2", "3", "4"],
        format_func=lambda x: f"{x} - {config.SERIOUSNESS_FIELD_MAP[x][1]}",
        key="seriousness",
    )
    ser_fld = config.SERIOUSNESS_FIELD_MAP[ser_choice][0]
    s_rows, _ = get_individual_serious_reports(search_drug, ser_fld, limit=200)
    if s_rows:
        serious_df = pd.DataFrame(s_rows)
        serious_df["Date"] = serious_df["Date"].dt.strftime("%d/%m/%Y")
        st.dataframe(serious_df, width="stretch", hide_index=True)

    # ------------------------------------------------------------
    # 6. 3D Balloon Safety Landscape
    # ------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"## 3D Balloon Safety Landscape — {search_drug} 🌐")
    st.markdown(
        """
        * **X-Axis**: Polypharmacy tiers
        * **Y-Axis**: Top 10 adverse effects cross-sectioned across all tiers
        * **Z-Axis**: Cross-sectional death percentage for that specific intersection
        * **Color**: One distinct color for each polypharmacy tier
        """
    )
    if raw_reps:
        df_3d, top10_fx = prepare_3d_matrix(raw_reps)
        if not df_3d.empty:
            render_3d_matrix(df_3d, top10_fx, search_drug)
            with st.expander("🔍 View Underlying 3D Balloon Data Matrix"):
                st.dataframe(
                    df_3d[["Polypharmacy Category", "Adverse Effect", "Reports", "Death", "Death Percentage (%)"]],
                    width="stretch",
                    hide_index=True,
                )
        else:
            st.warning("Insufficient parsed records matching polypharmacy criteria to render 3D balloons.")


