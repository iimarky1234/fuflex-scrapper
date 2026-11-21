# FUFLEX Exam Fetcher (`fetch_exam.py`)

> [!WARNING]
> **Use at your own risk.** Automated access to `fuflex.site` may violate the site's terms of service and could result in rate-limiting, IP blocks, or account suspension. You are solely responsible for how you use this script and for keeping your session tokens and API keys secure.

`fetch_exam.py` downloads exam question metadata, revealed answers (when available), and question PNG images from `fuflex.site` using an authenticated [Browserbase `browse` CLI](https://docs.browserbase.com/) remote browser session.

It uses only the Python standard library (no `pip` packages needed) and supports configuration via **CLI flags**, **environment variables**, a **`.env` file**, or **interactive prompts**.

---

## Prerequisites & Dependency Setup

### 1. Python 3.10+

Verify your Python version:

```bash
python3 --version
```

`fetch_exam.py` uses only standard library modules (`argparse`, `base64`, `getpass`, `json`, `os`, `pathlib`, `subprocess`, `time`, `urllib.parse`), so no `pip install` or virtual environment is required.

### 2. Node.js & npm

The `browse` CLI is distributed via npm and requires Node.js. Check if Node.js and npm are installed:

```bash
node --version
npm --version
```

If not installed, install Node.js from [https://nodejs.org](https://nodejs.org) (or via your system package manager / `nvm`).

### 3. Browserbase `browse` CLI

Install the `browse` CLI globally:

```bash
npm install -g browse
```

Verify installation:

```bash
which browse
browse --help
```

### 4. Browserbase API Key

Because `fetch_exam.py` runs `browse open ... --remote`, you need a Browserbase API key:

1. Create or sign in to an account at [https://www.browserbase.com](https://www.browserbase.com).
2. Copy your API key from **Settings → API Keys** (`https://www.browserbase.com/settings`).
3. Export `BROWSERBASE_API_KEY` in your shell (or add it to your `.env` file):

```bash
export BROWSERBASE_API_KEY="bb_live_..."
```

4. Verify your setup with `browse doctor`:

```bash
browse doctor
```

You should see `runtime`, `browserbase`, and `target` (`remote`) all report `ok`.

---

## Getting Your FUFLEX Session Values

Before running the script, sign in to [https://www.fuflex.site](https://www.fuflex.site) in your browser and open **DevTools** (`F12` or `Ctrl+Shift+I` / `Cmd+Option+I`):

1. **Local Storage** (`Application` → `Storage` → `Local Storage` → `https://www.fuflex.site`):
   - `fuflex_token`
   - `fuflex_visitor_id`
2. **Cookies** (`Application` → `Storage` → `Cookies` → `https://www.fuflex.site`):
   - `fx_trust`
   - `fx_did`
   - `fx_auth` (usually the same JWT as `fuflex_token`)
3. **Exam ID & Subject Code** from the exam URL:
   - Example URL: `https://www.fuflex.site/exams/3671/images?subject=APO201C`
   - Exam ID: `3671`
   - Subject code: `APO201C`

> **Security note:** Treat your tokens, cookies, and `BROWSERBASE_API_KEY` as secrets. Do not share them or commit `.env` to version control.

---

## Configuration & Precedence

`fetch_exam.py` resolves values in the following priority order (highest to lowest):

1. **CLI flags** (`--exam-id`, `--subject`)
2. **Shell environment variables**
3. **`.env` file** (`./.env` by default, falling back to `.env` next to `fetch_exam.py`, or a custom path via `--env-file`)
4. **Interactive prompts** (sensitive values are masked with `getpass`)

### Supported Environment Variables

| Variable | Description | Required |
| --- | --- | --- |
| `BROWSERBASE_API_KEY` | Browserbase API key used by `browse --remote` | Yes (for `browse`) |
| `FUFLEX_EXAM_ID` | Numeric exam ID (e.g. `3671`) | Yes (or `--exam-id`) |
| `FUFLEX_SUBJECT` | Subject code (e.g. `APO201C`) | Yes (or `--subject`) |
| `FUFLEX_TOKEN` | `fuflex_token` from `localStorage` | Yes |
| `FUFLEX_VISITOR_ID` | `fuflex_visitor_id` from `localStorage` | Yes |
| `FUFLEX_FX_TRUST` | `fx_trust` cookie | Yes |
| `FUFLEX_FX_DID` | `fx_did` cookie | Yes |
| `FUFLEX_FX_AUTH` | `fx_auth` cookie (defaults to `fuflex_token` if left blank at prompt) | Optional if prompting |

### Option A: Using a `.env` File (Recommended)

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Or create `.env` manually in the project directory:

```env
BROWSERBASE_API_KEY="bb_live_..."

FUFLEX_EXAM_ID=3671
FUFLEX_SUBJECT=APO201C

FUFLEX_TOKEN="eyJhbGciOi..."
FUFLEX_VISITOR_ID="your_visitor_id"
FUFLEX_FX_TRUST="your_fx_trust_cookie"
FUFLEX_FX_DID="your_fx_did_cookie"
FUFLEX_FX_AUTH="eyJhbGciOi..."
```

> If you put `BROWSERBASE_API_KEY` inside `.env`, `fetch_exam.py` loads it into `os.environ` before spawning `browse`, so `browse` will automatically inherit it.

If you use Git, make sure `.env` is ignored:

```bash
echo ".env" >> .gitignore
```

### Option B: Shell Environment Variables

```bash
export BROWSERBASE_API_KEY="bb_live_..."
export FUFLEX_EXAM_ID="3671"
export FUFLEX_SUBJECT="APO201C"
export FUFLEX_TOKEN="..."
export FUFLEX_VISITOR_ID="..."
export FUFLEX_FX_TRUST="..."
export FUFLEX_FX_DID="..."
export FUFLEX_FX_AUTH="..."
```

### Option C: Interactive Prompts

Simply run the script without setting environment variables or `.env`, and it will prompt you for each missing value (with hidden input for tokens and cookies).

---

## Usage

### Basic Run (using `.env` or interactive prompts)

```bash
python3 fetch_exam.py
```

### Override Exam ID / Subject via CLI Flags

```bash
python3 fetch_exam.py --exam-id 3671 --subject APO201C
```

### Save to a Specific Output Directory

```bash
python3 fetch_exam.py --exam-id 3671 --subject APO201C --output-dir ./exam_3671
```

### Use a Custom `.env` File or `browse` Session Name

```bash
python3 fetch_exam.py --env-file ~/.fuflex.env --session fuflex-exam-3671
```

### All CLI Options

| Flag | Default | Description |
| --- | --- | --- |
| `--exam-id` | *(from env / prompt)* | Exam ID (e.g. `3671`) |
| `--subject` | *(from env / prompt)* | Subject code (e.g. `APO201C`) |
| `--output-dir` | `.` | Directory where JSON, Markdown, and `images/` are written |
| `--session` | `fuflex` | Named `browse` session to isolate browser state |
| `--env-file` | `./.env` | Path to a `.env` file |

---

## Running with Docker

If you prefer not to install Node.js, Python, or `browse` locally, you can run `fetch_exam.py` using the included `Dockerfile`.

Build the image:

```bash
docker build -t fuflex-fetcher .
```

Run with a `.env` file (saving outputs to `./output` on your host):

```bash
docker run --rm -it \
  --env-file .env \
  -v "$(pwd)/output:/output" \
  fuflex-fetcher
```

Or pass flags and environment variables directly (any missing values will be prompted interactively):

```bash
docker run --rm -it \
  -e BROWSERBASE_API_KEY="bb_live_..." \
  -v "$(pwd)/output:/output" \
  fuflex-fetcher --exam-id 3671 --subject APO201C --output-dir /output
```

---

## Output Files

Running the script for exam `3671` writes the following into `--output-dir`:

```text
.
├── exam_3671_questions.json   # Raw API JSON from /api/exams/3671/questions?revealAnswers=true
├── exam_3671_questions.md     # Markdown summary of question prompts, answers, and image links
└── images/
    ├── Q01.png
    ├── Q02.png
    └── ...
```

- **Resumable downloads:** Images that already exist in `images/` (`Q01.png`, `Q02.png`, ...) are skipped automatically on re-runs.
- **Automatic cleanup:** The script always runs `browse stop --session <session>` in a `finally` block so the remote Browserbase session is closed even if an error occurs.

---

## Troubleshooting

- **`browse: command not found`**
  Make sure npm's global bin directory is on your `PATH`, or reinstall with `npm install -g browse`.
- **`401 Unauthorized` or Browserbase session fails to start**
  Verify `BROWSERBASE_API_KEY` is valid and run `browse doctor --json` for diagnostics.
- **Empty questions list or auth error**
  Your `fuflex_token`, `fx_auth`, or `fx_trust` may have expired (or your session may have been logged out on another device). Sign in again in your browser and refresh the values in `.env`.
- **Stale `browse` daemon / session**
  Force-stop the session and retry:
  ```bash
  browse stop --force --session fuflex
  ```

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
