# LeadIQ – AI-Powered Lead Scoring System

## Overview

LeadIQ is an AI-powered lead intelligence application designed to help sales teams evaluate, prioritize, and understand potential business leads.

The application combines a deterministic, rule-based scoring engine with Gemini AI to generate explainable lead assessments and actionable sales insights.

It helps answer three important questions:

- How valuable is this lead?
- Why did the lead receive this score?
- What should the sales team do next?

## Key Features

### 1. Lead Analyzer
- Enter individual lead details.
- Calculate a lead score from 0 to 100.
- Classify leads as Hot, Warm, or Cold.
- Display confidence and data completeness.
- Identify positive and negative scoring factors.
- Highlight missing information.
- Recommend the next sales action.

### 2. AI-Generated Sales Insights
- Generate readable lead summaries using Google Gemini.
- Suggest relevant sales talking points and qualification questions.
- Generate personalized follow-up email drafts.
- Provide deterministic fallback explanations if Gemini is unavailable.

### 3. Bulk Lead Scoring
- Upload lead information through CSV files.
- Analyze multiple leads in one operation.
- Rank leads based on their scores.
- Display scoring summaries.
- Export scored lead results.

### 4. Lead Comparison
- Compare multiple leads.
- Review their scores, classifications, and confidence.
- Identify stronger sales opportunities.

### 5. Scoring Methodology
- View scoring dimensions and their weights.
- Understand how lead scores are calculated.
- Review classification and confidence rules.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| User Interface | Streamlit |
| AI Integration | Google Gemini API |
| Data Processing | Pandas |
| Environment Management | Python Virtual Environment |
| Testing | Pytest |

## Scoring Methodology

LeadIQ uses a weighted deterministic scoring model.

| Scoring Dimension | Weight |
|---|---:|
| Decision Authority | 20% |
| Purchase Intent | 25% |
| Company Size | 15% |
| Industry Fit | 15% |
| Lead Source | 10% |
| Contactability | 15% |
| **Total** | **100%** |

### Lead Classification

| Score | Classification |
|---|---|
| 75–100 | Hot |
| 45–74 | Warm |
| 0–44 | Cold |

### Confidence Levels

| Data Completeness | Confidence |
|---|---|
| 85% and above | High |
| 60%–84% | Medium |
| Below 60% | Low |

Missing scoring dimensions are excluded from the available weighted total, and the remaining weights are normalized.

The deterministic scoring engine is the sole authority for the score, classification, confidence, and recommended action.

Gemini is used only to generate readable explanations and sales assistance. It does not calculate or modify lead scores.

## Project Structure

```text
leadiq_project/
│
├── app.py
├── agents/
│   └── explanation_agent.py
│
├── core/
│   ├── scoring_engine.py
│   ├── confidence_engine.py
│   └── lead_validator.py
│
├── utils/
│   └── demo_data.py
│
├── sample_data/
│   └── sample_leads.csv
│
├── tests/
│   └── test_scoring.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- pip
- Google Gemini API key

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd leadiq_project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.8-flash
```

Replace the placeholder with your own API key.

Never commit your actual `.env` file or expose your API key publicly.

### 6. Run the application

```bash
streamlit run app.py
```

The application will open in your browser.

## Running Tests

Run the automated test suite:

```bash
python -m pytest -v
```

### Test Coverage

The current test suite verifies:

1. Deterministic scoring for identical inputs.
2. Score boundaries between 0 and 100.
3. Correct classification of a sample lead.
4. Handling of missing lead information.
5. Invalid email validation.
6. Rejection of empty lead submissions.

**Latest recorded result:** 6 tests passed.

## AI Integration

LeadIQ integrates Google Gemini through the Google Gen AI Python SDK.

Gemini generates:
- Lead summaries.
- Sales talking points.
- Qualification questions.
- Follow-up email drafts.

The application retains its deterministic scoring and fallback explanations when AI services are unavailable.

## Future Enhancements

- CRM platform integrations.
- Advanced lead conversion prediction.
- Historical lead performance analytics.
- Customizable industry-specific scoring weights.
- Lead engagement tracking.
- Advanced sales pipeline analytics.

## Project Objective

The objective of LeadIQ is to make lead qualification more explainable, consistent, and actionable by combining transparent scoring logic with generative AI assistance.

---

**Project:** LeadIQ – AI-Powered Lead Scoring System  
**Category:** Artificial Intelligence / Machine Learning / Generative AI  
**Interface:** Streamlit
