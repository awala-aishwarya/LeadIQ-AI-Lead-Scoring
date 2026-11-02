# LeadIQ – AI-Powered Lead Scoring Agent

An explainable lead qualification application built with Python and Streamlit. It scores leads using a deterministic weighted rules engine and optionally uses an LLM to create grounded sales explanations and outreach suggestions. The LLM never generates or modifies the numeric score.

## Features
- Lead score from 0–100 and Hot / Warm / Cold classification
- Explainable weighted score breakdown and positive/negative factors
- Missing-data handling and separate confidence indicator
- Optional OpenAI-powered sales insights with deterministic fallback
- CSV batch scoring, ranking and export
- Input validation and automated tests

## Architecture
- `app.py`: Streamlit interface and workflows
- `core/scoring_engine.py`: deterministic weighted scoring rules
- `core/lead_validator.py`: normalization and validation
- `core/classification.py`: reusable classification thresholds
- `core/confidence_engine.py`: confidence helper
- `agents/explanation_agent.py`: optional LLM explanation layer
- `tests/`: automated tests
- `sample_data/`: sample CSV leads

## Scoring methodology
Each dimension is rated from 0 to 100 and multiplied by its weight:

| Dimension | Weight |
|---|---:|
| Decision-making authority | 20% |
| Purchase intent | 25% |
| Company size fit | 15% |
| Industry relevance | 15% |
| Lead source quality | 10% |
| Contactability | 15% |
| **Total** | **100%** |

Final score = sum(rating × weight) / sum(available weights) × 100. Missing dimensions are excluded from both numerator and denominator; the available weights are normalized. This avoids treating unknown information as a negative signal. Data completeness is the sum of available weights and is used as a confidence proxy, not as a probability of conversion.

Classification: Hot ≥75, Warm 45–74, Cold <45. Confidence: High ≥85% completeness, Medium 60–84%, Low <60%.

The rules and weights are initial heuristic assumptions for the assessment. A production deployment should calibrate them against historical lead-to-customer conversion data, sales feedback and fairness checks.

## Run locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Configure OpenAI insights
# Copy .env.example to .env and add your API key.
# The app works without this key; AI insights use a rule-based fallback.

# 4. Start the app
streamlit run app.py
```

## Run tests

```bash
pytest -q
```

## CSV format
Use the column names in `sample_data/sample_leads.csv`. Missing columns are treated as blank. Upload a CSV in the Bulk Scoring workspace and export the ranked results.

## LLM safety boundary
The scoring result is computed before the LLM call and passed to the LLM as fixed context. The prompt explicitly prohibits changing the score or classification. If the API key is absent or the request fails, the application displays the deterministic explanation and next action instead.

## Limitations and future improvements
- The scoring rules are heuristic and should be validated on a labeled historical dataset.
- Company size and industry fit depend on the target product's ideal customer profile; configure these mappings for the actual business.
- Website and company details are accepted as supplied; the prototype does not crawl websites or verify identities.
- Add CRM integrations, audit logging, model monitoring and role-based access before production use.
