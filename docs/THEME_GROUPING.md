# Theme Grouping Logic (Task 2)

## Approach

We use **rule-based theme assignment** supported by **TF-IDF keywords** per bank. This maps directly to Omega Consultancy business scenarios (login/OTP, slow transfers, crashes, feature requests).

## Business themes (6 categories)

| Theme | Business meaning | Example keywords |
|-------|------------------|------------------|
| **Account Access Issues** | Login, OTP, PIN, biometrics | `login`, `otp`, `password`, `fingerprint` |
| **Transaction Performance** | Slow transfers, pending payments | `slow`, `transfer`, `loading`, `pending` |
| **UI & Design** | Usability and look & feel | `ui`, `easy`, `navigation`, `design` |
| **Customer Support** | Branch, agents, helpline | `support`, `service`, `help`, `branch` |
| **Feature Requests** | New capabilities users want | `feature`, `budget`, `notification`, `add` |
| **Stability & Crashes** | Reliability problems | `crash`, `bug`, `freeze`, `not working` |

## Assignment algorithm (`src/thematic_analysis.py`)

1. Normalize review text (lowercase, remove punctuation).
2. For each theme, count how many of its keywords appear in the text.
3. Assign the theme with the **highest hit count**.
4. If no keyword matches → **General Feedback**.

Themes are applied to **all reviews** (English and Amharic/mixed), because keywords can appear in mixed-language text (e.g. English "OTP" in an Amharic review).

## TF-IDF role

- **Tokenization:** NLTK `word_tokenize` (fallback: split), English stop-word removal.
- **Optional lemmatization:** spaCy `en_core_web_sm` when installed.
- **Vectorizer:** `TfidfVectorizer` with unigrams + bigrams (`ngram_range=(1,2)`), `min_df=2`.
- **Output:** Top 10–15 terms per bank for reports and validation of theme choice.

## Optional extensions (not required for minimum)

- LDA / NMF topic modeling on lemmatized corpus.
- Zero-shot classification with Hugging Face for theme labels.

## Per-bank expectation (KPI)

Each bank should show **≥3 distinct themes** in `theme_summary.json` after running the pipeline.
