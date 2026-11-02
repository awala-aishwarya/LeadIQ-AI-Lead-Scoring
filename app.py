from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agents.explanation_agent import generate_ai_insights
from core.lead_validator import normalize_lead, validate_lead
from core.scoring_engine import WEIGHTS, score_lead
from utils.demo_data import SAMPLE_LEADS


st.set_page_config(
    page_title="LeadIQ | Lead Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { --ink:#17243b; --muted:#68758a; --line:#e7ebf2; --blue:#315efb; }
    .block-container { padding-top:1.6rem; padding-bottom:3rem; max-width:1500px; }
    [data-testid="stMetric"] {
        background:#f7f9fd; border:1px solid #e8edf5;
        padding:15px 17px; border-radius:13px;
    }
    [data-testid="stMetricValue"] { color:#17243b; }
    .hero {
        background:linear-gradient(120deg,#17243b,#263e68);
        padding:25px 29px; border-radius:17px; color:white; margin-bottom:20px;
    }
    .hero p { color:#d8e1f3; margin:5px 0 0 0; }
    .subtle { color:#68758a; font-size:13px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session-state defaults
DEFAULTS: dict[str, Any] = {
    "lead_result": None,
    "current_lead": None,
    "bulk_df": None,
    "scored_df": None,
    "invalid_bulk_rows": [],
}
for state_key, default_value in DEFAULTS.items():
    if state_key not in st.session_state:
        st.session_state[state_key] = default_value


with st.sidebar:
    st.markdown("# 🎯 LeadIQ")
    st.caption("AI-powered lead intelligence")
    page = st.radio(
        "Workspace",
        [
            "Lead Analyzer",
            "Bulk Scoring",
            "Lead Comparison",
            "Scoring Methodology",
            "About & Help",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption("DETERMINISTIC SCORING")
    st.write(
        "A transparent weighted algorithm calculates every score. "
        "AI is reserved for grounded explanations and sales assistance."
    )
    st.caption("v1.2 · Leadonspot candidate project")


st.markdown(
    """
    <div class="hero">
      <h1 style="margin:0;color:white">Lead Intelligence Workspace</h1>
      <p>Qualify prospects, understand buying signals, and prioritize the next best sales action.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


def _lead_label(lead: dict[str, Any], index: int = 0) -> str:
    name = str(lead.get("name") or f"Lead {index + 1}")
    company = str(lead.get("company_name") or "Unknown company")
    return f"{name} — {company}"


def _ai_cache_key(lead: dict[str, Any], result: dict[str, Any]) -> str:
    """Stable per-lead cache key; avoids collisions between leads with same score."""
    cache_payload = {
        "lead": {
            key: str(lead.get(key, "") or "")
            for key in (
                "name", "company_name", "website", "job_title", "industry",
                "company_location", "company_size", "lead_source", "requirement",
            )
        },
        "score": result.get("score"),
    }
    digest = hashlib.sha256(
        json.dumps(cache_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return f"leadiq_ai_{digest}"


def show_result(
    lead: dict[str, Any],
    result: dict[str, Any],
    show_ai: bool = True,
) -> None:
    """Render one scored lead and its optional Gemini sales assistance."""
    st.subheader("Lead assessment")

    a, b, c, d = st.columns(4)
    a.metric("Lead score", f"{result['score']}/100")
    b.metric("Classification", result["classification"])
    c.metric("Confidence", result["confidence"])
    d.metric("Data completeness", f"{result['data_completeness']}%")

    st.progress(
        max(0.0, min(1.0, float(result["score"]) / 100)),
        text=f"Lead score: {result['score']} out of 100",
    )

    if result["data_completeness"] < 85:
        st.warning(
            "Qualification confidence is limited because some weighted "
            "information is missing. Treat this score as a preliminary fit "
            "assessment, not a confirmed likelihood of conversion."
        )

    left, right = st.columns(2)
    with left:
        st.markdown("#### Lead quality assessment")
        st.write(result.get("quality", "No quality assessment available."))
        st.markdown("#### Recommended next action")
        st.info(result.get("recommended_action", "Review the lead details."))
        st.markdown("#### Scoring explanation")
        st.write(result.get("explanation", "No scoring explanation available."))

    with right:
        st.markdown("#### Positive factors")
        for item in result.get("positive_factors", []):
            st.markdown(f"- ✅ {item}")
        st.markdown("#### Negative factors")
        for item in result.get("negative_factors", []):
            st.markdown(f"- ⚠️ {item}")
        missing_fields = result.get("missing_fields", [])
        if missing_fields:
            st.markdown("#### Missing information")
            st.write(", ".join(missing_fields))

    st.markdown("#### Explainable score breakdown")
    breakdown = result.get("breakdown", [])
    if breakdown:
        frame = pd.DataFrame(breakdown)
        if "rating" in frame.columns:
            frame["rating"] = frame["rating"].apply(
                lambda value: "—" if pd.isna(value) else f"{int(value)}/100"
            )
        if "weighted_points" in frame.columns:
            frame["weighted_points"] = frame["weighted_points"].apply(
                lambda value: "Excluded" if pd.isna(value) else f"{float(value):.2f}"
            )
        st.dataframe(
            frame.rename(
                columns={
                    "factor": "Scoring factor",
                    "weight": "Weight (%)",
                    "rating": "Factor rating",
                    "weighted_points": "Weighted points",
                    "status": "Data status",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No scoring breakdown was returned by the scoring engine.")

    if show_ai:
        with st.expander("✨ AI sales insights", expanded=False):
            cache_key = _ai_cache_key(lead, result)

            if st.button(
                "Generate sales insights",
                key=f"generate_{cache_key}",
                type="primary",
            ):
                with st.spinner("Generating grounded Gemini AI insights..."):
                    try:
                        ai_result = generate_ai_insights(lead, result)
                    except Exception as exc:
                        # Defensive boundary: the UI remains usable if the AI
                        # helper unexpectedly raises an exception.
                        ai_result = {
                            "available": False,
                            "summary": result.get(
                                "explanation", "AI insights are unavailable."
                            ),
                            "talking_points": [],
                            "email_draft": "",
                            "error": f"Unexpected AI error: {type(exc).__name__}",
                        }

                    if not isinstance(ai_result, dict):
                        ai_result = {
                            "available": False,
                            "summary": result.get(
                                "explanation", "AI insights are unavailable."
                            ),
                            "talking_points": [],
                            "email_draft": "",
                            "error": "AI function returned an invalid response.",
                        }

                    st.session_state[cache_key] = ai_result

            ai = st.session_state.get(cache_key)

            if not isinstance(ai, dict):
                st.caption(
                    "Click Generate sales insights to create a Gemini-powered "
                    "summary, talking points and outreach draft."
                )
            else:
                if ai.get("available", False):
                    st.success("Gemini AI insights generated successfully!")
                else:
                    st.warning(
                        "Gemini AI is unavailable. The deterministic scoring "
                        "and fallback explanation are still available."
                    )
                    if ai.get("error"):
                        st.error(f"Gemini API error: {ai['error']}")

                st.markdown("**Lead summary**")
                st.write(ai.get("summary") or "No summary returned.")

                points = ai.get("talking_points", [])
                if isinstance(points, list) and points:
                    st.markdown("**Suggested talking points**")
                    for point in points:
                        st.markdown(f"- {point}")

                draft = ai.get("email_draft", "")
                if isinstance(draft, str) and draft.strip():
                    st.markdown("**Suggested outreach email**")
                    st.text_area(
                        "Email draft",
                        value=draft,
                        height=220,
                        key=f"email_draft_{cache_key}",
                    )


# ---------------------------------------------------------------------------
# Lead Analyzer
# ---------------------------------------------------------------------------
if page == "Lead Analyzer":
    st.markdown("### Enter lead details")
    st.caption(
        "Submit complete or incomplete information. Missing scoring dimensions "
        "are excluded from the weighted average and reduce data completeness."
    )

    with st.form("lead_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            name = st.text_input("Contact name", placeholder="Rahul Sharma")
            company = st.text_input("Company name", placeholder="ABC Technologies")
            website = st.text_input("Website", placeholder="www.company.com")
            job = st.text_input("Job title", placeholder="Founder / CEO / Manager")

        with c2:
            industry = st.text_input("Industry", placeholder="IT Services")
            location = st.text_input("Company location", placeholder="Bangalore")
            size = st.selectbox(
                "Company size",
                [
                    "", "1 Employee", "2-10 Employees", "11-49 Employees",
                    "50-199 Employees", "200-999 Employees", "1000+ Employees",
                ],
            )
            source = st.selectbox(
                "Lead source",
                [
                    "", "Website", "Demo Request", "Referral", "Webinar",
                    "LinkedIn", "Organic Search", "Event", "Paid Ads",
                    "Social Media", "Cold Email", "Purchased List", "Other",
                ],
            )

        with c3:
            requirement = st.text_area(
                "Requirement / business need",
                placeholder="Looking for CRM software; request a demo...",
            )
            email = st.text_input("Email", placeholder="rahul@company.com")
            phone = st.text_input("Phone", placeholder="+91 9876543210")

        submitted = st.form_submit_button(
            "Analyze lead →", type="primary", use_container_width=True
        )

    if submitted:
        lead = normalize_lead(
            {
                "name": name,
                "company_name": company,
                "website": website,
                "job_title": job,
                "industry": industry,
                "company_location": location,
                "company_size": size,
                "lead_source": source,
                "requirement": requirement,
                "email": email,
                "phone": phone,
            }
        )
        errors = validate_lead(lead)
        if errors:
            for error in errors:
                st.error(error)
        else:
            st.session_state.current_lead = lead
            st.session_state.lead_result = score_lead(lead)

    if (
        st.session_state.lead_result is not None
        and st.session_state.current_lead is not None
    ):
        show_result(
            st.session_state.current_lead,
            st.session_state.lead_result,
        )


# ---------------------------------------------------------------------------
# Bulk Scoring
# ---------------------------------------------------------------------------
elif page == "Bulk Scoring":
    st.markdown("### Bulk lead scoring")
    st.write(
        "Upload a CSV file or load the included demo leads. Each row is scored "
        "using the same deterministic scoring engine as the Lead Analyzer."
    )

    with st.expander("CSV format and supported columns"):
        st.write(
            "Use columns such as name, company_name, website, job_title, "
            "industry, company_location, company_size, lead_source, "
            "requirement, email and phone. Unknown columns are not used by "
            "the scoring engine."
        )
        st.download_button(
            "Download sample CSV template",
            pd.DataFrame(SAMPLE_LEADS).to_csv(index=False).encode("utf-8"),
            "leadiq_sample_template.csv",
            "text/csv",
        )

    uploaded = st.file_uploader("Upload leads CSV", type=["csv"])

    if st.button("Load demo leads", use_container_width=True):
        st.session_state.bulk_df = pd.DataFrame(SAMPLE_LEADS)
        st.session_state.scored_df = None
        st.session_state.invalid_bulk_rows = []

    if uploaded is not None:
        try:
            uploaded_df = pd.read_csv(uploaded).fillna("")
            if uploaded_df.empty:
                st.error("The uploaded CSV contains no lead rows.")
            else:
                st.session_state.bulk_df = uploaded_df
                st.session_state.scored_df = None
        except Exception as exc:
            st.error(f"Could not read CSV: {type(exc).__name__}: {exc}")

    if st.session_state.bulk_df is not None:
        df = st.session_state.bulk_df.copy()
        st.markdown("#### Lead records")
        st.caption(f"{len(df)} records detected.")
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Score all leads", type="primary"):
            rows = []
            invalid_rows = []

            for row_index, row in df.iterrows():
                lead = normalize_lead(row.to_dict())
                errors = validate_lead(lead)

                if errors:
                    invalid_rows.append(
                        {
                            "row": int(row_index) + 1,
                            "name": lead.get("name", ""),
                            "errors": "; ".join(errors),
                        }
                    )
                    continue

                result = score_lead(lead)
                rows.append(
                    {
                        "name": lead.get("name", ""),
                        "company_name": lead.get("company_name", ""),
                        "score": result["score"],
                        "classification": result["classification"],
                        "confidence": result["confidence"],
                        "data_completeness": result["data_completeness"],
                        "missing_fields": ", ".join(
                            result.get("missing_fields", [])
                        ),
                        "recommended_action": result["recommended_action"],
                    }
                )

            if rows:
                scored_frame = pd.DataFrame(rows)
                st.session_state.scored_df = scored_frame.sort_values(
                    ["score", "data_completeness"],
                    ascending=[False, False],
                ).reset_index(drop=True)
            else:
                st.session_state.scored_df = pd.DataFrame()

            st.session_state.invalid_bulk_rows = invalid_rows

        if st.session_state.scored_df is not None:
            scored = st.session_state.scored_df

            if scored.empty:
                st.warning("No valid leads were available to score.")
            else:
                st.markdown("#### Bulk scoring summary")
                total = len(scored)
                hot = int((scored["classification"] == "Hot").sum())
                warm = int((scored["classification"] == "Warm").sum())
                cold = int((scored["classification"] == "Cold").sum())
                average = scored["score"].mean()

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Processed", total)
                m2.metric("Hot leads", hot)
                m3.metric("Warm leads", warm)
                m4.metric("Cold leads", cold)
                m5.metric("Average score", f"{average:.1f}/100")

                st.markdown("#### Ranked lead list")
                st.dataframe(
                    scored,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "score": st.column_config.ProgressColumn(
                            "Lead score",
                            min_value=0,
                            max_value=100,
                            format="%d",
                        )
                    },
                )

                st.download_button(
                    "Download scored leads CSV",
                    scored.to_csv(index=False).encode("utf-8"),
                    "leadiq_scored_leads.csv",
                    "text/csv",
                    use_container_width=True,
                )

            invalid = st.session_state.get("invalid_bulk_rows", [])
            if invalid:
                st.warning(
                    f"{len(invalid)} row(s) were skipped because record "
                    "validation failed."
                )
                st.dataframe(
                    pd.DataFrame(invalid),
                    use_container_width=True,
                    hide_index=True,
                )


# ---------------------------------------------------------------------------
# Lead Comparison
# ---------------------------------------------------------------------------
elif page == "Lead Comparison":
    st.markdown("### Compare and prioritize leads")
    st.write(
        "Load demo records or score a CSV in Bulk Scoring first. "
        "Select up to three leads to compare."
    )

    comparison_source = st.session_state.get("scored_df")

    if comparison_source is None or comparison_source.empty:
        if st.button("Load demo leads for comparison"):
            rows = []
            for sample in SAMPLE_LEADS:
                lead = normalize_lead(sample)
                errors = validate_lead(lead)
                if not errors:
                    result = score_lead(lead)
                    rows.append(
                        {
                            "name": lead.get("name", ""),
                            "company_name": lead.get("company_name", ""),
                            "score": result["score"],
                            "classification": result["classification"],
                            "confidence": result["confidence"],
                            "data_completeness": result["data_completeness"],
                            "recommended_action": result["recommended_action"],
                        }
                    )

            if rows:
                st.session_state.scored_df = pd.DataFrame(rows).sort_values(
                    "score", ascending=False
                ).reset_index(drop=True)
            else:
                st.session_state.scored_df = pd.DataFrame()
            st.rerun()
        else:
            st.info("No scored lead list is available yet.")
    else:
        options = comparison_source.apply(
            lambda row: (
                f"{row['name']} — {row['company_name']} ({row['score']}/100)"
            ),
            axis=1,
        ).tolist()

        selected = st.multiselect(
            "Choose leads to compare",
            options,
            default=options[: min(3, len(options))],
            max_selections=3,
        )

        if selected:
            comparison = comparison_source.copy()
            comparison["label"] = comparison.apply(
                lambda row: (
                    f"{row['name']} — {row['company_name']} ({row['score']}/100)"
                ),
                axis=1,
            )
            chosen = comparison[comparison["label"].isin(selected)].drop(
                columns=["label"]
            )
            st.dataframe(
                chosen,
                use_container_width=True,
                hide_index=True,
            )
            best = chosen.sort_values(
                ["score", "data_completeness"],
                ascending=False,
            ).iloc[0]
            st.success(
                f"Highest-priority selected lead: {best['name']} "
                f"({best['company_name']}) with {best['score']}/100. "
                f"Confidence: {best['confidence']}."
            )


# ---------------------------------------------------------------------------
# Scoring Methodology
# ---------------------------------------------------------------------------
elif page == "Scoring Methodology":
    st.markdown("### Transparent scoring methodology")
    st.write(
        "Each dimension is rated from 0 to 100 using explicit Python rules. "
        "The rating is multiplied by its weight. Available weights are "
        "normalized when data is missing, so an unknown value is not "
        "automatically treated as a negative signal."
    )

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Dimension": key.replace("_", " ").title(),
                    "Weight (%)": value,
                }
                for key, value in WEIGHTS.items()
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.latex(
        r"\text{Lead Score}="
        r"\frac{\sum(\text{Dimension Rating}\times\text{Dimension Weight})}"
        r"{\sum(\text{Available Dimension Weights})}\times100"
    )

    st.markdown("#### Classification thresholds")
    st.write("Hot: 75–100 · Warm: 45–74 · Cold: 0–44")

    st.markdown("#### Confidence")
    st.write(
        "Confidence reflects the proportion of weighted scoring dimensions "
        "with usable input: High ≥85%, Medium 60–84%, Low <60%. "
        "It is not a statistical probability of conversion."
    )

    st.warning(
        "The weights and rule mappings are an initial heuristic model for "
        "this assignment. In production, calibrate them against historical "
        "conversion outcomes and review for segment bias."
    )


# ---------------------------------------------------------------------------
# About & Help
# ---------------------------------------------------------------------------
else:
    st.markdown("### About LeadIQ")
    st.write(
        "LeadIQ is an explainable lead qualification prototype designed "
        "to help sales teams prioritize prospects consistently."
    )
    st.markdown("**Key design decisions**")
    st.markdown(
        "- Deterministic weighted scoring: identical inputs produce identical scores.\n"
        "- Missing fields: excluded from the denominator and reflected in confidence.\n"
        "- LLM boundary: AI can summarize and suggest outreach, but cannot alter the score or classification.\n"
        "- Fallback: core scoring works without an API key.\n"
        "- Batch workflow: CSV upload, ranking, summary metrics and export.\n"
        "- Lead comparison: compare up to three scored leads."
    )
    st.markdown("**To enable Gemini AI insights**")
    st.code(
        "# Create a .env file\n"
        "GEMINI_API_KEY=your_api_key_here\n"
        "GEMINI_MODEL=your_available_gemini_model"
    )
    st.caption(
        "Never commit your .env file or expose API keys in GitHub. "
        "Use a model name available to your Google AI Studio API key."
    )
