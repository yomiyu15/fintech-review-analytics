"""
Task 4: Derive satisfaction drivers, pain points, and recommendations from analyzed reviews.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from src.config import ANALYZED_REVIEWS_CSV, BANK_SHORT_NAMES, THEME_SUMMARY_JSON

DRIVER_KEYWORDS = [
    "fast", "easy", "simple", "smooth", "reliable", "excellent", "great",
    "love", "best", "convenient", "user friendly", "helpful", "quick",
]
PAIN_KEYWORDS = [
    "slow", "crash", "bug", "error", "fail", "failed", "otp", "login",
    "password", "stuck", "freeze", "terrible", "worst", "hate", "unable",
]

GENERAL_THEME = "General Feedback"


def load_analyzed_reviews(path=None) -> pd.DataFrame:
    path = path or ANALYZED_REVIEWS_CSV
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df["bank_short"] = df["bank"].map(BANK_SHORT_NAMES)
    return df


def _truncate(text: str, max_len: int = 140) -> str:
    text = re.sub(r"\s+", " ", str(text)).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _sample_quotes(
    df: pd.DataFrame,
    mask: pd.Series,
    n: int = 2,
) -> list[str]:
    subset = df.loc[mask, "review"].dropna()
    if subset.empty:
        return []
    samples = subset.sample(min(n, len(subset)), random_state=42)
    return [_truncate(t) for t in samples]


def _theme_evidence(
    df: pd.DataFrame,
    bank: str,
    theme: str,
    sentiment: str | None = None,
    max_rating: int | None = None,
    min_rating: int | None = None,
) -> dict[str, Any]:
    mask = (df["bank"] == bank) & (df["identified_theme"] == theme)
    if sentiment:
        mask &= df["sentiment_label"] == sentiment
    if max_rating is not None:
        mask &= df["rating"] <= max_rating
    if min_rating is not None:
        mask &= df["rating"] >= min_rating
    n = int(mask.sum())
    bank_n = int((df["bank"] == bank).sum())
    return {
        "theme": theme,
        "count": n,
        "share_of_bank_pct": round(n / bank_n * 100, 1) if bank_n else 0,
        "sample_quotes": _sample_quotes(df, mask),
    }


def _keyword_evidence(
    df: pd.DataFrame,
    bank: str,
    keywords: list[str],
    sentiment: str,
    label: str,
) -> dict[str, Any]:
    bank_df = df[df["bank"] == bank]
    pattern = "|".join(re.escape(k) for k in keywords)
    mask = bank_df["review"].str.contains(pattern, case=False, na=False, regex=True)
    if sentiment == "positive":
        mask &= bank_df["sentiment_label"] == "positive"
    else:
        mask &= bank_df["sentiment_label"] == "negative"
    n = int(mask.sum())
    return {
        "label": label,
        "count": n,
        "share_of_bank_pct": round(n / len(bank_df) * 100, 1) if len(bank_df) else 0,
        "sample_quotes": _sample_quotes(bank_df, mask),
    }


def extract_drivers_and_pains(df: pd.DataFrame, bank: str) -> dict[str, list[dict]]:
    """At least 2 drivers and 2 pain points per bank with evidence."""
    bank_df = df[df["bank"] == bank]
    drivers: list[dict] = []
    pains: list[dict] = []

    # Driver 1: positive themed UI & Design (Dashen/CBE strong)
    ui_pos = (bank_df["identified_theme"] == "UI & Design") & (
        bank_df["sentiment_label"] == "positive"
    )
    if ui_pos.sum() >= 3:
        ev = _theme_evidence(df, bank, "UI & Design", sentiment="positive")
        drivers.append(
            {
                "title": "Intuitive UI and ease of use",
                "summary": (
                    f"{ev['count']} positive UI & Design reviews "
                    f"({ev['share_of_bank_pct']}% of {BANK_SHORT_NAMES[bank]} reviews)."
                ),
                "evidence": ev,
            }
        )

    # Driver 2: Customer Support positive
    sup_pos = (bank_df["identified_theme"] == "Customer Support") & (
        bank_df["sentiment_label"] == "positive"
    )
    if sup_pos.sum() >= 3:
        ev = _theme_evidence(df, bank, "Customer Support", sentiment="positive")
        drivers.append(
            {
                "title": "Responsive customer support",
                "summary": (
                    f"{ev['count']} positive Customer Support mentions "
                    f"({ev['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": ev,
            }
        )

    # Driver 3: keyword-based (fast/easy) on 5-star
    kw_driver = _keyword_evidence(
        df, bank, ["fast", "easy", "smooth", "reliable"], "positive", "Speed and reliability"
    )
    if kw_driver["count"] >= 5:
        drivers.append(
            {
                "title": kw_driver["label"],
                "summary": (
                    f"{kw_driver['count']} positive reviews cite speed/ease/reliability "
                    f"({kw_driver['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": kw_driver,
            }
        )

    # Driver 4: high ratings overall
    if len(drivers) < 2:
        five_star = (bank_df["rating"] == 5).sum()
        avg = bank_df["rating"].mean()
        drivers.append(
            {
                "title": "Strong overall satisfaction (5-star reviews)",
                "summary": (
                    f"{five_star} five-star reviews; mean star rating {avg:.2f} "
                    f"({five_star / len(bank_df) * 100:.0f}% are 5-star)."
                ),
                "evidence": {
                    "count": int(five_star),
                    "share_of_bank_pct": round(five_star / len(bank_df) * 100, 1),
                    "sample_quotes": _sample_quotes(bank_df, bank_df["rating"] == 5),
                },
            }
        )

    # Pain 1: Transaction Performance negative
    txn_neg = (bank_df["identified_theme"] == "Transaction Performance") & (
        bank_df["sentiment_label"] == "negative"
    )
    if txn_neg.sum() >= 3:
        ev = _theme_evidence(df, bank, "Transaction Performance", sentiment="negative")
        pains.append(
            {
                "title": "Slow or failed transactions",
                "summary": (
                    f"{ev['count']} negative Transaction Performance reviews "
                    f"({ev['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": ev,
            }
        )

    # Pain 2: Stability & Crashes (especially BOA)
    crash_neg = (bank_df["identified_theme"] == "Stability & Crashes") & (
        bank_df["sentiment_label"] == "negative"
    )
    if crash_neg.sum() >= 3:
        ev = _theme_evidence(df, bank, "Stability & Crashes", sentiment="negative")
        pains.append(
            {
                "title": "App crashes and instability",
                "summary": (
                    f"{ev['count']} negative Stability & Crashes reviews "
                    f"({ev['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": ev,
            }
        )

    # Pain 3: Account Access / OTP
    acc_neg = (bank_df["identified_theme"] == "Account Access Issues") & (
        bank_df["sentiment_label"] == "negative"
    )
    if acc_neg.sum() >= 3:
        ev = _theme_evidence(df, bank, "Account Access Issues", sentiment="negative")
        pains.append(
            {
                "title": "Login, OTP, and account access failures",
                "summary": (
                    f"{ev['count']} negative Account Access Issues "
                    f"({ev['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": ev,
            }
        )

    # Pain 4: keyword OTP/login/crash
    kw_pain = _keyword_evidence(
        df, bank, ["otp", "login", "crash", "slow", "failed"], "negative", "OTP, login, and crashes"
    )
    if kw_pain["count"] >= 5 and len(pains) < 2:
        pains.append(
            {
                "title": kw_pain["label"],
                "summary": (
                    f"{kw_pain['count']} negative reviews mention OTP/login/crash/slow "
                    f"({kw_pain['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": kw_pain,
            }
        )

    # Pain 5: Feature Requests negative (unmet needs)
    feat_neg = (bank_df["identified_theme"] == "Feature Requests") & (
        bank_df["sentiment_label"] == "negative"
    )
    if feat_neg.sum() >= 3 and len(pains) < 2:
        ev = _theme_evidence(df, bank, "Feature Requests", sentiment="negative")
        pains.append(
            {
                "title": "Missing or inadequate features",
                "summary": (
                    f"{ev['count']} negative Feature Requests reviews "
                    f"({ev['share_of_bank_pct']}% of reviews)."
                ),
                "evidence": ev,
            }
        )

    if len(pains) < 2:
        low = bank_df[bank_df["rating"] <= 2]
        pains.append(
            {
                "title": "Low star ratings (1–2 stars)",
                "summary": f"{len(low)} reviews rated 1–2 stars ({len(low)/len(bank_df)*100:.1f}% of reviews).",
                "evidence": {
                    "count": len(low),
                    "share_of_bank_pct": round(len(low) / len(bank_df) * 100, 1),
                    "sample_quotes": _sample_quotes(bank_df, bank_df["rating"] <= 2),
                },
            }
        )

    return {
        "drivers": drivers[:4],
        "pains": pains[:4],
    }


def compare_banks(df: pd.DataFrame) -> dict[str, Any]:
    """Cross-bank comparison on sentiment, rating, and themes."""
    rows = []
    for bank in df["bank"].unique():
        sub = df[df["bank"] == bank]
        scored = sub[sub["sentiment_label"].isin(["positive", "negative", "neutral"])]
        rows.append(
            {
                "bank": bank,
                "bank_short": BANK_SHORT_NAMES[bank],
                "n_reviews": len(sub),
                "avg_rating": round(sub["rating"].mean(), 2),
                "pct_positive": round((sub["sentiment_label"] == "positive").mean() * 100, 1),
                "pct_negative": round((sub["sentiment_label"] == "negative").mean() * 100, 1),
                "pct_non_english": round((sub["sentiment_label"] == "non_english").mean() * 100, 1),
                "mean_sentiment_score": round(scored["sentiment_score"].mean(), 3)
                if not scored.empty
                else None,
                "top_theme": sub.loc[
                    sub["identified_theme"] != GENERAL_THEME, "identified_theme"
                ]
                .value_counts()
                .idxmax()
                if (sub["identified_theme"] != GENERAL_THEME).any()
                else GENERAL_THEME,
            }
        )
    themed = df[df["identified_theme"] != GENERAL_THEME]
    theme_by_bank = (
        themed.groupby(["bank", "identified_theme"])
        .size()
        .reset_index(name="count")
        .sort_values(["bank", "count"], ascending=[True, False])
    )
    return {"summary": rows, "theme_counts": theme_by_bank.to_dict(orient="records")}


def propose_recommendations(
    bank: str,
    drivers: list[dict],
    pains: list[dict],
) -> list[dict[str, str]]:
    """At least 2 concrete product/support improvements per bank."""
    short = BANK_SHORT_NAMES[bank]
    recs: list[dict[str, str]] = []

    pain_titles = {p["title"].lower() for p in pains}

    if any("transaction" in t or "slow" in t for t in pain_titles):
        recs.append(
            {
                "priority": "P1",
                "recommendation": (
                    f"Invest in transfer/payment performance: add end-to-end transaction "
                    f"tracing, proactive push notifications on pending/failed payments, "
                    f"and a dedicated \"payment status\" screen for {short} users."
                ),
                "grounds": "Transaction Performance is a top negative theme in review data.",
            }
        )
    if any("crash" in t or "stability" in t for t in pain_titles):
        recs.append(
            {
                "priority": "P1",
                "recommendation": (
                    f"Launch a stability sprint for {short}: crash reporting (Firebase/Crashlytics), "
                    f"device/OS matrix testing, and hotfix channel for force-close issues."
                ),
                "grounds": "Stability & Crashes appears frequently in negative reviews (esp. BOA).",
            }
        )
    if any("otp" in t or "login" in t or "access" in t for t in pain_titles):
        recs.append(
            {
                "priority": "P1",
                "recommendation": (
                    f"Redesign OTP/login flow for {short}: SMS fallback, clearer error messages, "
                    f"and in-app \"resend OTP\" with rate-limit transparency."
                ),
                "grounds": "Account Access Issues and OTP/login keywords in negative reviews.",
            }
        )
    if any("feature" in t for t in pain_titles):
        recs.append(
            {
                "priority": "P2",
                "recommendation": (
                    f"Publish a public {short} mobile roadmap (budget tools, statements, notifications) "
                    f"and tie releases to top Feature Request themes."
                ),
                "grounds": "Negative Feature Request reviews signal unmet product expectations.",
            }
        )

    driver_titles = {d["title"].lower() for d in drivers}
    if any("ui" in t or "ease" in t for t in driver_titles):
        recs.append(
            {
                "priority": "P2",
                "recommendation": (
                    f"Protect {short}'s UI strengths: usability testing on major flows, "
                    f"dark mode, and accessibility (font size, Amharic/English toggle)."
                ),
                "grounds": "UI & Design is a documented satisfaction driver.",
            }
        )
    if any("support" in t for t in driver_titles):
        recs.append(
            {
                "priority": "P3",
                "recommendation": (
                    f"Scale in-app chat and branch callback for {short}; promote support "
                    f"channels where positive Customer Support reviews cluster."
                ),
                "grounds": "Customer Support cited positively in themed reviews.",
            }
        )

    if len(recs) < 2:
        avg_rating = None  # filled by caller if needed
        recs.append(
            {
                "priority": "P2",
                "recommendation": (
                    f"Run quarterly {short} \"review listening\" sessions using Play Store "
                    f"themes to prioritize backlog items."
                ),
                "grounds": "Sustains data-driven product decisions from ongoing review mining.",
            }
        )
        recs.append(
            {
                "priority": "P3",
                "recommendation": (
                    f"Add Amharic in-app FAQ and support content for {short} to reduce "
                    f"non_english review volume and improve access for local-language users."
                ),
                "grounds": "Non-English reviews cannot receive English-only sentiment scores.",
            }
        )

    return recs[:4]


def build_full_insights(df: pd.DataFrame | None = None) -> dict[str, Any]:
    """Compile drivers, pains, comparisons, and recommendations for all banks."""
    df = df if df is not None else load_analyzed_reviews()
    banks = sorted(df["bank"].unique())
    per_bank = {}
    for bank in banks:
        dp = extract_drivers_and_pains(df, bank)
        per_bank[bank] = {
            **dp,
            "recommendations": propose_recommendations(bank, dp["drivers"], dp["pains"]),
        }
    return {
        "comparison": compare_banks(df),
        "per_bank": per_bank,
        "ethics_notes": ethics_section(),
    }


def ethics_section() -> list[str]:
    return [
        "**Negativity bias:** Play Store reviewers often post after a bad experience; "
        "sentiment and themes may over-represent problems versus silent satisfied users.",
        "**English-only sentiment:** Amharic and mixed-language reviews are labeled "
        "`non_english` without a transformer score; English-only scraping (`lang=en`) "
        "under-samples Amharic feedback.",
        "**Temporal sampling:** Reviews span roughly one year (scrape window); seasonal "
        "campaigns or app releases may skew theme counts.",
        "**Keyword themes:** Rule-based themes miss nuance; sarcasm and context can be misclassified.",
        "**Survivorship:** Users who uninstall without reviewing are invisible in this dataset.",
    ]


def save_insights_json(data: dict, path=None) -> None:
    from src.config import INSIGHTS_SUMMARY_JSON

    path = path or INSIGHTS_SUMMARY_JSON
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
