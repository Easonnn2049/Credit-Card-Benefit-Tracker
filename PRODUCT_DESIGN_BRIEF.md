# Product Design Brief: Local Credit Card Benefit Tracker

## 1. Product Vision

This app is a local-first credit card benefit tracker built for personal use.

The product should not feel like a spreadsheet viewer. It should feel like a lightweight personal command center that helps the user quickly answer:

> Which credit card benefits should I use next?
> Which benefits are expiring soon?
> Which benefits have I already completed?
> Which cards still have unused value?

The main product goal is not to track spending, budgets, balances, credit scores, or bank account data. The main goal is to make credit card benefits easier to use before they expire.

---

## 2. Target User

The primary user is an individual managing multiple credit cards across one or more cardholders.

The user may have cards with:

- Monthly credits
- Quarterly credits
- Semi-annual credits
- Annual credits
- One-time benefits
- Dining, travel, airline, hotel, rideshare, grocery, shopping, entertainment, or miscellaneous benefits

The user wants a private, local-first tool that is easier to scan and use than Excel.

---

## 3. Core Product Principle

The app should be:

> Scan first, drill down second.

Default views should show only the most important information. Detailed information should be hidden until the user expands or clicks into a benefit.

Avoid showing every field at once.

---

## 4. Product Positioning

This app is a:

> Local-first credit card benefit command center.

It is not:

- A budgeting app
- A bank sync app
- A credit score app
- A full personal finance app
- A spreadsheet replacement with prettier tables
- A clone of any commercial app

The app may borrow general product patterns from mature rewards and benefit tracking apps, but should not copy any proprietary UI, branding, layout, logos, or protected design.

---

## 5. Key User Questions

The app should help the user answer these questions quickly:

1. What benefits need my attention now?
2. What benefits are expiring soon?
3. Which benefits have I not used yet?
4. Which benefits have I partially used?
5. Which benefits have I already completed?
6. Which card still has unused benefit value?
7. Which benefits can I ignore or hide because I do not care about them?
8. What is the remaining value I can still capture?

---

## 6. Design Philosophy

### 6.1 Action-Oriented Dashboard

The home dashboard should feel like an action list, not a report.

Prioritize:

- Expiring soon
- Not used
- Partially used
- High-value remaining benefits
- Benefits due this month or quarter

Deprioritize:

- Completed benefits
- Ignored benefits
- Long notes
- Historical detail
- Dense metadata

---

### 6.2 Progressive Disclosure

Use a hierarchy:

```text
Dashboard summary
→ Credit card row
→ Compact benefit row
→ Expanded benefit detail

The user should not see every benefit detail by default.

For each benefit, collapsed view should show only:

Benefit name
Status
Due date / countdown
Small progress indicator

Expanded view can show:

Used amount
Remaining amount
Total value
Expiration date
Notes
Slider
Quick action buttons
6.3 Reduce Text Density

Avoid dense text-heavy layouts.

Do not show long notes, descriptions, raw dates, multiple amounts, and metadata all at the same visual level.

Use:

Card sections
Status badges
Deadline badges
Progress bars
Sliders
Expanders
Tabs
Clear spacing
Visual grouping

Long notes should usually be hidden inside an expander or details section.

6.4 Visual Hierarchy

Every screen should have a clear hierarchy.

Important information should be visually prominent:

Benefit name: larger / bolder
Due date: prominent badge or deadline marker
Status: badge
Usage progress: progress bar or slider
Notes: secondary and collapsed
Metadata: smaller and less visually dominant

The user should not need to read every line to understand priority.

6.5 Five-Second Test

A user should be able to open the app and within five seconds understand:

Which benefits need action
Which benefits are expiring soon
Which cards still have meaningful value left

If the user must carefully read many rows of text, the design is too dense.

7. Core Views
7.1 Home Dashboard

The dashboard should show a high-level command center.

Recommended sections:

Summary counters
Active benefits
Expiring soon
Completed this cycle
Ignored / hidden
Estimated value remaining
Priority action section
Expiring soon
Not used
Partially used
Optional value summary
Total available value
Total used value
Remaining value

The dashboard should not be a giant table.

7.2 Cards View

The Cards View should group benefits by credit card.

Each credit card should appear as a clean card row or card tile.

Each card should show:

Card image if available
Card name
Owner / cardholder
Number of active benefits
Remaining benefit value
Overall usage progress
Expand / show benefits control

The card-level design should be easy to scan.

7.3 Benefit List Within a Card

Inside an expanded credit card, each benefit should be compact by default.

Collapsed benefit row should show:

Benefit name
Benefit category
Status badge
Due date / countdown
Small progress indicator

Do not show full details by default.

7.4 Benefit Detail View

When a benefit is expanded, show detailed information and controls.

Expanded benefit detail should include:

Expiration date / due date
Used amount
Remaining amount
Total benefit value
Status
Notes
Usage slider
Quick action buttons

Quick actions should include:

Mark as Used
Mark as Partially Used
Mark as Not Used
Ignore / Hide
7.5 Category View

The Category View should group benefits by benefit type.

Example categories:

Dining
Airline
Hotel / Travel
Uber / Rideshare
Grocery / Instacart
Shopping
Entertainment
Other

Category sections should use simple icons, labels, or visual grouping.

The category view should help the user answer:

I am about to make a dining/travel/grocery purchase. Which benefit should I use?

7.6 Completed / Ignored View

Completed and ignored benefits should not dominate the main active dashboard.

They should be recoverable in a separate section, toggle, or tab.

Examples:

Show completed benefits
Show ignored benefits
Restore ignored benefit
8. Status Model

The app should support these benefit statuses:

Not Used
Partially Used
Used
Ignored / Hidden

Behavior:

Not Used: active and should appear in main views.
Partially Used: active and should appear in main views.
Used: should be hidden from main active view by default, but recoverable.
Ignored / Hidden: should be hidden from main active view, but recoverable.
9. Due Date Logic

Due dates are high-priority information.

Due dates should not be buried in normal body text.

Use one or more of:

Deadline badge
Countdown text
Due soon label
Overdue label
Date chip
Timeline marker

Recommended due-date states:

Overdue
Due today
Due in X days
Due this month
Due later
No due date

Expiring soon should be visually distinct.

10. Progress and Usage Logic

Benefit value should be shown visually when possible.

Use:

Progress bars
Sliders
Used / remaining value
Percentage complete

For benefits with a total value:

progress = used_amount / total_value
remaining = total_value - used_amount

If progress reaches 100%, mark the benefit as Used.

If progress is between 0% and 100%, mark as Partially Used.

If progress is 0%, mark as Not Used unless manually ignored.

11. Interaction Principles

Interactions should be low-friction.

The user should be able to quickly:

Expand a card
Expand a benefit
Update usage amount
Mark a benefit as used
Hide a benefit
Restore a hidden benefit

Avoid requiring the user to edit raw tables for common actions.

Common actions should be buttons, sliders, toggles, or simple forms.

12. Visual Asset Principles

Credit card images should use a reliable local image system.

Preferred approach:

assets/card_images/
data/card_image_mapping.csv

The app should:

Look up card images by card name
Display local images if available
Use a graceful fallback if missing
Never break if an image is unavailable

Do not depend on unstable hotlinked images.

Do not spend excessive time scraping the web.

13. Data Principles

The app should remain local-first.

Data should come from:

Existing Excel tracker as initial source
Local CSV / JSON / SQLite as working storage

The original Excel file should be preserved.

Do not overwrite the original Excel file unless explicitly requested.

Working data should be easy to inspect, edit, back up, and recover.

14. Technical Constraints

The app should remain:

Python
Streamlit
Local-first
Simple to run
Beginner-friendly

Do not migrate to:

Next.js
React
npm
Prisma
Tailwind
Cloud architecture
Authentication
Bank sync

Unless explicitly requested.

The app should continue to run with:

streamlit run app.py
15. Engineering Style

Prefer small, incremental changes.

Before large changes, propose a plan.

When making changes:

Identify the files to change.
Explain the intended UI or logic change.
Keep changes localized when possible.
Avoid unnecessary abstractions.
Preserve existing data.
Do not rebuild the entire app unless necessary.
If errors occur, diagnose the minimum fix.
16. UX Review Checklist

Before finalizing any UI change, evaluate the result against this checklist:

Five-second test

Can the user quickly tell what needs attention?

Scan test

Can the user scan the page without reading every line?

Action test

Can the user quickly mark a benefit as used, partial, unused, or ignored?

Noise test

Are completed and ignored benefits hidden from the main active view?

Drill-down test

Are details hidden until the user expands a benefit?

Due-date test

Are expiring benefits visually obvious?

Progress test

Is used vs remaining value visible without reading dense text?

Beginner test

Can a non-engineer understand and use the interface?

17. Product Quality Bar

A good version of this app should feel:

Clean
Visual
Practical
Lightweight
Action-oriented
Easy to scan
Easy to update
Not spreadsheet-like

A poor version of this app feels:

Text-heavy
Table-heavy
Overly technical
Visually flat
Hard to scan
Too much metadata by default
Requires reading every line
Hides important due dates
Shows completed items too prominently
18. North Star

The north star is:

The user should always know which credit card benefit to use next, without having to read through a spreadsheet.