# Credit Card Benefit Tracker

Simple local-first Streamlit app for tracking credit card benefits.

## Why This Version

This MVP uses Python, Streamlit, pandas, and CSV files. It does not use Next.js, React, npm, Prisma, Tailwind, or cloud services.

Recommended storage approach: **Option B**.

The app imports your Excel tracker once, preserves the original file as `data/original_tracker.xlsx`, and creates simpler local CSV files:

- `data/cards.csv`
- `data/benefits.csv`
- `data/usage.csv`

This is simpler and safer than writing directly back to Excel.

## Run

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

Start the app:

```powershell
py -m streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Excel Import

If your Excel tracker is not already in the project folder, open the app and use the **Import Excel** tab.

The importer tries to detect columns such as:

- owner / cardholder
- card name
- issuer
- benefit name
- category
- cycle / frequency
- status
- benefit amount
- used amount
- remaining amount
- expiration / due date
- notes

If the workbook is messy, the app still preserves the original Excel file and reports which columns were mapped or skipped.

## Current Workbook Mapping

The app is structured around `credit_card_benefit_tracker_template_v2 (1).xlsx`.

Mapped sheets:

- `Cards` -> `data/cards.csv`
- `Current Cycle Tracker` -> `data/benefits.csv`
- `Benefits Master` -> enriches benefits with card ID, category, realistic value, source URL, and review fields
- `Benefit Usage Log` -> `data/usage.csv`

Preserved but not used as working tables:

- `Dashboard`
- `Lists`
- `Sources`

## Main Views

Use the sidebar to switch between app sections. This keeps Streamlit from rendering every section at once and makes quick updates more responsive.

- **Home**: action-oriented dashboard with expiring, unused, and partially used benefit lanes.
- **Cards**: visual card-style browsing grouped by credit card, with active count, remaining value, progress, and collapsed benefits.
- **Categories**: benefit browsing grouped by category, with simple visual labels and summary counters.
- **Edit Benefits**: raw editable table for bulk cleanup when needed.

Quick actions update `data/benefits.csv` locally.

## Card Images

The By Card view checks `data/card_images/` for local card art before using the built-in representative card face.

Open **Dashboard -> By Card -> Manage card images** to:

- upload a card image
- or paste a direct image URL and cache it locally

Supported filenames:

- `card_id.png`, `card_id.jpg`, `card_id.jpeg`, or `card_id.webp`
- or a lowercase card-name filename with spaces replaced by underscores

Example:

```text
data/card_images/amex_gold_p1.png
data/card_images/chase_sapphire_reserve_p1.png
```

If no image is found, the app uses a card-specific local fallback style for Amex Gold, Amex Platinum, Chase Sapphire, United, Marriott, Hyatt, Hilton, U.S. Bank, and generic cards.
