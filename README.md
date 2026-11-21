# FUFLEX Exam Fetcher

> [!WARNING]
> **Use at your own risk.** Automated access to `fuflex.site` may violate the site's terms of service and result in rate-limiting, IP blocks, or account suspension. You are solely responsible for how you use this tool and for safeguarding your credentials.

A Python utility (`fetch_exam.py`) that exports exam metadata, revealed answers, and question images from `fuflex.site` using an authenticated [Browserbase `browse` CLI](https://docs.browserbase.com/) session. Uses the Python standard library only.

## Requirements

- **Python 3.10+** (no third-party Python packages required)
- **Node.js & npm**
- **Browserbase `browse` CLI** and a **Browserbase API key** (`https://www.browserbase.com/settings`)

### Setup

```bash
npm install -g browse
export BROWSERBASE_API_KEY="bb_live_..."
browse doctor
```

## Configuration

Values are resolved in order: **shell environment variables → `.env` file → interactive prompts**.

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `BROWSERBASE_API_KEY` | Browserbase API key for `browse --remote` | *Required* |
| `FUFLEX_EXAM_ID` | Exam ID from the exam URL (e.g. `3671`) | *Required* |
| `FUFLEX_SUBJECT` | Subject code from the exam URL (e.g. `APO201C`) | *Required* |
| `FUFLEX_TOKEN` | `fuflex_token` from `localStorage` | *Required* |
| `FUFLEX_VISITOR_ID` | `fuflex_visitor_id` from `localStorage` | *Required* |
| `FUFLEX_FX_TRUST` | `fx_trust` cookie | *Required* |
| `FUFLEX_FX_DID` | `fx_did` cookie | *Required* |
| `FUFLEX_FX_AUTH` | `fx_auth` cookie (reuses `FUFLEX_TOKEN` if left blank at prompt) | *Optional* |
| `FUFLEX_OUTPUT_DIR` | Output directory for exported files | `.` |
| `FUFLEX_SESSION` | Named `browse` session | `fuflex` |

To obtain your FUFLEX session values, sign in to `fuflex.site`, open browser DevTools (**Application → Local Storage** and **Application → Cookies**), and copy the corresponding entries. Keep `.env` out of version control.

## Usage

### Local

```bash
python3 fetch_exam.py
```

Override values for a single run via inline environment variables:

```bash
FUFLEX_EXAM_ID=3671 FUFLEX_SUBJECT=APO201C FUFLEX_OUTPUT_DIR=./exam_3671 python3 fetch_exam.py
```

### Docker

```bash
docker build -t fuflex-fetcher .
docker run --rm -it \
  --env-file .env \
  -e FUFLEX_OUTPUT_DIR=/output \
  -v "$(pwd)/output:/output" \
  fuflex-fetcher
```

## Output

Files are written to `FUFLEX_OUTPUT_DIR`:

```text
<FUFLEX_OUTPUT_DIR>/
├── exam_<ID>_questions.json   # Raw API response
├── exam_<ID>_questions.md     # Questions, answers, and image links
└── images/
    ├── Q01.png
    └── ...
```

Existing images in `images/` are skipped on re-runs, and the remote `browse` session is always stopped on exit.

## Troubleshooting

- **`browse: command not found`**: Ensure npm's global `bin` directory is in `PATH`, or run `npm install -g browse`.
- **Browserbase session errors (`401` / startup failure)**: Verify `BROWSERBASE_API_KEY` and run `browse doctor --json`.
- **Empty results or auth errors**: Refresh your FUFLEX cookies/token in `.env` after signing in again.
- **Stale session**: Run `browse stop --force --session fuflex`.

## License

Licensed under the [Apache License 2.0](LICENSE).
