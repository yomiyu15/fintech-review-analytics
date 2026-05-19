#!/usr/bin/env python
"""
Task 4: Generate insights, visualizations, markdown report, and PDF.

Usage:
    python scripts/generate_insights_report.py
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import (
    BANK_SHORT_NAMES,
    INSIGHTS_REPORT_MD,
    INSIGHTS_REPORT_PDF,
    INSIGHTS_SUMMARY_JSON,
    REPORT_FIGURES_DIR,
    REPORTS_DIR,
    THEME_SUMMARY_JSON,
)
from src.insights import build_full_insights, load_analyzed_reviews

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

PALETTE = {"positive": "#2ecc71", "negative": "#e74c3c", "neutral": "#95a5a6", "non_english": "#3498db"}
BANK_ORDER = ["Commercial Bank of Ethiopia", "Bank of Abyssinia", "Dashen Bank"]


def _bank_labels(df: pd.DataFrame) -> list[str]:
    return [BANK_SHORT_NAMES.get(b, b[:12]) for b in BANK_ORDER if b in df["bank"].unique()]


def plot_sentiment_by_bank(df: pd.DataFrame, out_dir: Path) -> Path:
    """Stacked bar: sentiment distribution per bank."""
    counts = (
        df.groupby(["bank", "sentiment_label"])
        .size()
        .unstack(fill_value=0)
        .reindex(BANK_ORDER)
    )
    counts.index = [_bank_labels(df)[i] for i in range(len(counts))]
    cols = [c for c in ["positive", "negative", "neutral", "non_english"] if c in counts.columns]
    counts = counts[cols]
    pct = counts.div(counts.sum(axis=1), axis=0) * 100

    fig, ax = plt.subplots(figsize=(9, 5))
    bottom = pd.Series(0.0, index=pct.index)
    for col in cols:
        ax.bar(pct.index, pct[col], bottom=bottom, label=col.replace("_", " ").title(), color=PALETTE.get(col))
        bottom += pct[col]
    ax.set_ylabel("Share of reviews (%)")
    ax.set_xlabel("Bank")
    ax.set_title("Sentiment Distribution by Bank")
    ax.legend(title="Sentiment", loc="upper right")
    ax.set_ylim(0, 100)
    plt.tight_layout()
    path = out_dir / "01_sentiment_by_bank.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_rating_distribution(df: pd.DataFrame, out_dir: Path) -> Path:
    """Boxplot of star ratings per bank."""
    plot_df = df.copy()
    plot_df["bank_short"] = plot_df["bank"].map(BANK_SHORT_NAMES)
    order = [BANK_SHORT_NAMES[b] for b in BANK_ORDER]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=plot_df, x="bank_short", y="rating", order=order, hue="bank_short", legend=False, palette="Set2", ax=ax)
    ax.set_xlabel("Bank")
    ax.set_ylabel("Star rating")
    ax.set_title("Rating Distribution per Bank")
    ax.set_ylim(0.5, 5.5)
    plt.tight_layout()
    path = out_dir / "02_rating_boxplot.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_theme_frequency(df: pd.DataFrame, out_dir: Path) -> Path:
    """Horizontal bar: top themes per bank (excl. General Feedback)."""
    themed = df[df["identified_theme"] != "General Feedback"].copy()
    themed["bank_short"] = themed["bank"].map(BANK_SHORT_NAMES)
    top = (
        themed.groupby(["bank_short", "identified_theme"])
        .size()
        .reset_index(name="count")
    )
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
    for ax, short in zip(axes, [BANK_SHORT_NAMES[b] for b in BANK_ORDER]):
        sub = top[top["bank_short"] == short].nlargest(6, "count")
        if sub.empty:
            ax.set_visible(False)
            continue
        ax.barh(sub["identified_theme"], sub["count"], color="#5dade2")
        ax.set_title(short)
        ax.invert_yaxis()
        ax.set_xlabel("Review count")
    fig.suptitle("Top Themes per Bank (excluding General Feedback)", y=1.02)
    plt.tight_layout()
    path = out_dir / "03_theme_frequency.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_sentiment_trend(df: pd.DataFrame, out_dir: Path) -> Path:
    """Monthly % positive sentiment (English-scored reviews)."""
    scored = df[df["sentiment_label"].isin(["positive", "negative", "neutral"])].copy()
    scored["month"] = scored["date"].dt.to_period("M").astype(str)
    trend = (
        scored.groupby(["month", "bank"])
        .apply(lambda g: (g["sentiment_label"] == "positive").mean() * 100, include_groups=False)
        .reset_index(name="pct_positive")
    )
    trend["bank_short"] = trend["bank"].map(BANK_SHORT_NAMES)

    fig, ax = plt.subplots(figsize=(10, 5))
    for bank in BANK_ORDER:
        sub = trend[trend["bank"] == bank]
        if sub.empty:
            continue
        ax.plot(
            sub["month"],
            sub["pct_positive"],
            marker="o",
            label=BANK_SHORT_NAMES[bank],
            linewidth=2,
        )
    ax.set_xlabel("Month")
    ax.set_ylabel("% positive (English-scored reviews)")
    ax.set_title("Sentiment Trend Over Time")
    ax.legend(title="Bank")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    path = out_dir / "04_sentiment_trend.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_avg_rating_comparison(df: pd.DataFrame, out_dir: Path) -> Path:
    """Bar chart: mean star rating per bank."""
    means = df.groupby("bank")["rating"].mean().reindex(BANK_ORDER)
    labels = [BANK_SHORT_NAMES[b] for b in means.index]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, means.values, color=["#1abc9c", "#9b59b6", "#e67e22"])
    ax.set_ylabel("Mean star rating")
    ax.set_xlabel("Bank")
    ax.set_title("Average Star Rating by Bank")
    ax.set_ylim(0, 5)
    for bar, val in zip(bars, means.values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05, f"{val:.2f}", ha="center")
    plt.tight_layout()
    path = out_dir / "05_avg_rating.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _format_item_list(items: list[dict], kind: str) -> str:
    lines = []
    for i, item in enumerate(items[:4], 1):
        lines.append(f"### {kind} {i}: {item['title']}\n")
        lines.append(f"{item['summary']}\n")
        ev = item.get("evidence", {})
        if ev.get("sample_quotes"):
            lines.append("**Sample reviews:**\n")
            for q in ev["sample_quotes"][:2]:
                lines.append(f"> \"{q}\"\n")
        lines.append("")
    return "\n".join(lines)


def write_markdown_report(
    df: pd.DataFrame,
    insights: dict,
    figure_paths: list[Path],
) -> str:
    """Medium-style markdown report body."""
    lines = [
        "# Fintech Mobile Banking: Insights & Recommendations",
        "",
        "*Omega Consultancy — Play Store review analysis for CBE, Bank of Abyssinia, and Dashen Bank.*",
        "",
        f"**Dataset:** {len(df):,} cleaned reviews | "
        f"**Period:** {df['date'].min().date()} to {df['date'].max().date()} | "
        f"**Source:** Google Play (Ethiopia)",
        "",
        "---",
        "",
        "## Executive summary",
        "",
    ]
    comp = insights["comparison"]["summary"]
    best = max(comp, key=lambda x: x["avg_rating"])
    worst = min(comp, key=lambda x: x["avg_rating"])
    lines.append(
        f"- **Highest rated:** {best['bank_short']} (mean {best['avg_rating']} stars).\n"
        f"- **Lowest rated:** {worst['bank_short']} (mean {worst['avg_rating']} stars).\n"
        f"- **Sentiment:** DistilBERT on English reviews; Amharic/mixed labeled `non_english`.\n"
        f"- **Themes:** TF-IDF + keyword rules across six business categories.\n"
    )
    lines.extend(["", "---", "", "## Cross-bank comparison", ""])
    lines.append("| Bank | Reviews | Avg rating | % Positive | % Negative | Top themed issue |")
    lines.append("|------|---------|------------|------------|------------|------------------|")
    for row in comp:
        lines.append(
            f"| {row['bank_short']} | {row['n_reviews']} | {row['avg_rating']} | "
            f"{row['pct_positive']}% | {row['pct_negative']}% | {row['top_theme']} |"
        )

    for fig_path in figure_paths:
        name = fig_path.stem.replace("_", " ").title()
        rel = f"figures/{fig_path.name}"
        lines.extend(["", f"![{name}]({rel})", ""])

    for bank in BANK_ORDER:
        if bank not in insights["per_bank"]:
            continue
        short = BANK_SHORT_NAMES[bank]
        block = insights["per_bank"][bank]
        lines.extend(
            [
                "",
                "---",
                "",
                f"## {bank} ({short})",
                "",
                "### Satisfaction drivers",
                "",
                _format_item_list(block["drivers"], "Driver"),
                "### Pain points",
                "",
                _format_item_list(block["pains"], "Pain point"),
                "### Recommendations",
                "",
            ]
        )
        for rec in block["recommendations"]:
            lines.append(
                f"- **[{rec['priority']}]** {rec['recommendation']}  \n"
                f"  *Evidence:* {rec['grounds']}\n"
            )

    lines.extend(["", "---", "", "## Ethics and limitations", ""])
    for note in insights["ethics_notes"]:
        lines.append(f"- {note.replace('**', '')}")

    lines.extend(
        [
            "",
            "---",
            "",
            "*Report generated by `scripts/generate_insights_report.py` (Task 4).*",
        ]
    )
    return "\n".join(lines)


def _ascii_safe(text: str) -> str:
    """fpdf core fonts are Latin-1; normalize common Unicode punctuation."""
    replacements = {
        "\u2014": "-",
        "\u2013": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def write_pdf(md_path: Path, pdf_path: Path, figure_paths: list[Path]) -> None:
    """Build PDF from markdown sections and embedded figures (fpdf2)."""
    from fpdf import FPDF

    text = _ascii_safe(md_path.read_text(encoding="utf-8"))

    class ReportPDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(100, 100, 100)
            self.cell(0, 8, "Fintech Review Analytics - Task 4 Insights", align="R", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 8, f"Page {self.page_no()}", align="C")

        def chapter_title(self, title: str):
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(30, 30, 30)
            self.multi_cell(0, 8, _ascii_safe(title))
            self.ln(2)

        def body_text(self, body: str):
            self.set_font("Helvetica", "", 10)
            self.set_text_color(50, 50, 50)
            self.multi_cell(0, 5, _ascii_safe(body))
            self.ln(2)

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.chapter_title("Fintech Mobile Banking: Insights & Recommendations")
    pdf.body_text(
        "Omega Consultancy analysis of Google Play reviews for CBE, BOA, and Dashen Bank. "
        "See insights_report.md for full narrative; this PDF summarizes findings with charts."
    )

    for fig in figure_paths:
        pdf.add_page()
        title = fig.stem.replace("_", " ").title()
        pdf.chapter_title(title)
        pdf.image(str(fig), x=10, w=190)

    # Text sections from markdown (simplified parse)
    pdf.add_page()
    pdf.chapter_title("Bank highlights")
    for bank in BANK_ORDER:
        section = []
        capture = False
        for line in text.splitlines():
            if line.startswith(f"## {bank}"):
                capture = True
                continue
            if capture and line.startswith("## ") and bank not in line:
                break
            if capture and line.strip() and not line.startswith("!["):
                clean = line.replace("**", "").replace(">", "").strip()
                if clean.startswith("#"):
                    clean = clean.lstrip("#").strip()
                if clean:
                    section.append(clean)
        if section:
            pdf.chapter_title(BANK_SHORT_NAMES.get(bank, bank))
            pdf.body_text("\n".join(section[:40]))

    pdf.add_page()
    pdf.chapter_title("Ethics and limitations")
    ethics_started = False
    for line in text.splitlines():
        if "Ethics and limitations" in line:
            ethics_started = True
            continue
        if ethics_started and line.startswith("---"):
            break
        if ethics_started and line.startswith("- "):
            pdf.body_text(line[2:].replace("**", ""))

    pdf.output(str(pdf_path))


def main() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    df = load_analyzed_reviews()
    insights = build_full_insights(df)
    INSIGHTS_SUMMARY_JSON.write_text(json.dumps(insights, indent=2, default=str), encoding="utf-8")
    log.info("Saved %s", INSIGHTS_SUMMARY_JSON)

    figures = [
        plot_sentiment_by_bank(df, REPORT_FIGURES_DIR),
        plot_rating_distribution(df, REPORT_FIGURES_DIR),
        plot_theme_frequency(df, REPORT_FIGURES_DIR),
        plot_sentiment_trend(df, REPORT_FIGURES_DIR),
        plot_avg_rating_comparison(df, REPORT_FIGURES_DIR),
    ]
    log.info("Saved %d figures to %s", len(figures), REPORT_FIGURES_DIR)

    md = write_markdown_report(df, insights, figures)
    INSIGHTS_REPORT_MD.write_text(md, encoding="utf-8")
    log.info("Saved %s", INSIGHTS_REPORT_MD)

    write_pdf(INSIGHTS_REPORT_MD, INSIGHTS_REPORT_PDF, figures)
    log.info("Saved %s", INSIGHTS_REPORT_PDF)

    for bank in BANK_ORDER:
        block = insights["per_bank"].get(bank, {})
        log.info(
            "%s: %d drivers, %d pains, %d recommendations",
            BANK_SHORT_NAMES[bank],
            len(block.get("drivers", [])),
            len(block.get("pains", [])),
            len(block.get("recommendations", [])),
        )


if __name__ == "__main__":
    main()
