English | [简体中文](README.md)

# Wuhai Government Procurement Opportunities Skill

> Collects bidding announcements and procurement intentions from the **Inner Mongolia Government Procurement Network** for Wuhai in real time, with optional AI scoring and ranking against your company's business scope, so you can quickly spot bid opportunities worth pursuing.

## Features

- **Two information types**: bidding announcements (open tender / inquiry / competitive consultation) and public procurement intentions (advance notices released before formal tenders)
- **Four query modes**: for each type, both a raw list (JSON) and an AI-scored ranking version are provided
- **Zero third-party dependencies**: built only on the Python standard library (urllib); no `pip install` required
- **Real-time collection**: calls the official website's list API directly, so the data stays in sync with the source
- **Automatic filtering**: closed/expired items are removed automatically, and the remaining days (or months) are calculated for each item
- **Smart scoring**: the ranked versions read the company business scope from `config/company.txt`, and the agent scores every item 0–100 by relevance and sorts the results
- **Field extraction**: automatically extracts the budget (in 10,000 CNY) and the expected procurement month from intention descriptions, and strips official boilerplate text

## When to trigger

Use this skill when the user asks things like:

- What bidding announcements / procurement information has Wuhai published recently?
- Are there any projects / opportunities that fit our company?
- Check the latest procurement intentions / bidding announcements
- What bids can we go after? What projects can we take?
- Recommend projects ranked by relevance to our business scope

Trigger keywords (Chinese): 招标公告 (bidding announcements), 采购意向 (procurement intentions), 政府采购 (government procurement), 商机 (business opportunities), 投标 (bidding), 标书 (tender documents), 乌海招标 (Wuhai bids).

## Project structure

```
.
├── SKILL.md                  # Skill manifest (trigger rules and usage instructions read by the agent)
├── config/
│   └── company.txt           # Company business scope (basis for AI scoring; edit for your own company)
├── scripts/
│   ├── _core.py              # Core collection module (zero dependencies, based on urllib)
│   ├── bids.py               # Bidding announcements, original order (JSON output)
│   ├── bids_ranked.py        # Bidding announcements (AI-scored ranking version)
│   ├── intentions.py         # Procurement intentions, original order (JSON output)
│   └── intentions_ranked.py  # Procurement intentions (AI-scored ranking version)
└── auto_upload_github.py     # (Optional) local helper that commits and pushes the project to GitHub
```

## Requirements

- Python 3 (standard library only; no third-party packages needed)
- Network access to https://www.ccgp-neimenggu.gov.cn

## Installation

Clone or download this repository into your agent's skills directory, so that `SKILL.md` sits at the skill root:

```bash
git clone https://github.com/anancat63/bidding-info-skill-v1.1.git
```

Once an agent discovers this repository online, it can be loaded following the agent's own skill installation flow. The runtime requirement (`bins: ["python3"]`) is declared in the `SKILL.md` front matter.

## Usage

### Four query modes

| User intent | Command |
|-------------|---------|
| Bidding announcements, no ranking | `python3 {baseDir}/scripts/bids.py` |
| Bidding announcements, ranked by business fit | `python3 {baseDir}/scripts/bids_ranked.py` |
| Procurement intentions, no ranking | `python3 {baseDir}/scripts/intentions.py` |
| Procurement intentions, ranked by business fit | `python3 {baseDir}/scripts/intentions_ranked.py` |

`{baseDir}` is a placeholder for the skill root directory; when running in a terminal, replace it with the actual path.

### CLI arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--top N` | Take only the first N items; `0` means all | `0` |
| `--page-size N` | Number of items fetched from the official website | `20` |
| `--region CODE` | Administrative division code; Wuhai is `150301` | `150301` |

Examples:

```bash
# Only the first 10 bidding announcements
python3 scripts/bids.py --top 10

# Fetch 50 procurement intentions and let the AI rank them by business fit
python3 scripts/intentions_ranked.py --page-size 50
```

The scripts can also run standalone in a terminal, without an agent: the non-ranked versions print JSON; the ranked versions print a "scoring task + company business scope + numbered item list" text for an AI to read and score.

## Output

**Bidding announcements (`bids.py`, JSON)**: total count on the official website, number of returned items, and for each item the title, region, procurement method, publish date, deadline, days remaining, and detail link.

**Procurement intentions (`intentions.py`, JSON)**: title, region, purchaser, publish date, expected procurement time, budget (10,000 CNY), project description, and detail link.

**Ranked versions (`*_ranked.py`)**: they print the company business scope, scoring rules, and a numbered item list. The agent then scores every item and renders a Markdown table. Scoring bands:

| Score | Meaning | Recommendation |
|-------|---------|----------------|
| 80–100 | Highly relevant — core business | Pursue immediately |
| 60–79 | Fairly relevant — the company can deliver it | Prioritize |
| 40–59 | Partially related | Keep in the pipeline |
| 0–39 | Weakly related | Don't invest effort |

When rendering results, items closing within 3 days are marked 🔴 urgent and items within 7 days are marked 🟡 watch. Closed/expired items are already filtered out by the scripts and will never appear.

## Customization

- **Company business scope**: edit `config/company.txt` and write in your own company's main business; the ranked versions read it automatically as the scoring basis. The current file contains the business scope of "Wuhai Digital Industry Development Group", focused on software development, information system integration, artificial intelligence, big data, the Internet of Things, cybersecurity, digital video surveillance, and similar areas.
- **Region**: pass another administrative division code with `--region` (the skill has only been tested under the coding system of the Inner Mongolia Government Procurement Network; Wuhai = `150301`).

## Scope and limitations

- The data source is **limited to** the Inner Mongolia Government Procurement Network (ccgp-neimenggu.gov.cn);
- The region is **limited to Wuhai** (regionCode=150301); other provinces and cities are not supported;
- Keyword search is not supported — items can only be fetched in the official list order;
- Data is collected in real time. Network errors or changes to the official API may cause failures; please retry later or check whether the upstream API has changed.

## Disclaimer

This skill only collects and organizes **public information** from government procurement websites, for opportunity discovery and internal reference. It does not guarantee the completeness or timeliness of the data. Bidding decisions must be based on the official announcements and tender documents published on the official website.
