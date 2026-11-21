#!/usr/bin/env python3
"""Fetch FUFLEX exam questions and images using an authenticated `browse` session."""

import base64
import getpass
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.parse import quote


def load_dotenv(env_path: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ without overwriting existing vars."""
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        if key:
            os.environ.setdefault(key, value)


def resolve_value(
    label: str,
    env_var: str | None = None,
    default: str | None = None,
    secret: bool = False,
) -> str:
    """Resolve a value from environment variables or an interactive prompt."""
    if env_var:
        env_val = os.environ.get(env_var, "").strip()
        if env_val:
            return env_val

    env_hint = f" (or set {env_var})" if env_var else ""
    suffix = f" [{default}]" if default else ""
    while True:
        raw = (
            getpass.getpass(f"{label}{env_hint}{suffix}: ")
            if secret
            else input(f"{label}{env_hint}{suffix}: ")
        ).strip()
        value = raw or (default or "")
        if value:
            return value
        print(f"{label} is required.")


def run_browse(args: list[str]) -> str:
    """Run a `browse` CLI command and return stdout."""
    proc = subprocess.run(
        ["browse", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def eval_js(session: str, js: str):
    """Evaluate JavaScript in the `browse` session and return the parsed `result`."""
    out = run_browse(["eval", "--session", session, js])
    start = out.find("{")
    if start == -1:
        raise RuntimeError(f"Unexpected `browse eval` output: {out!r}")
    payload = json.loads(out[start:])
    return payload.get("result")


def build_auth_js(
    fuflex_token: str,
    visitor_id: str,
    fx_trust: str,
    fx_did: str,
    fx_auth: str,
) -> str:
    """Build the JS snippet that populates localStorage and cookies."""
    cookies = [
        f"fx_trust={fx_trust}; path=/; domain=.fuflex.site; secure; samesite=lax",
        f"fx_did={fx_did}; path=/; domain=.fuflex.site; secure; samesite=lax",
        f"fx_auth={fx_auth}; path=/; domain=.fuflex.site; secure; samesite=lax",
    ]
    return f"""(() => {{
      localStorage.setItem("fuflex_token", {json.dumps(fuflex_token)});
      localStorage.setItem("fuflex_visitor_id", {json.dumps(visitor_id)});
      for (const c of {json.dumps(cookies)}) {{
        document.cookie = c;
      }}
      return "ok";
    }})()"""


def fetch_questions(session: str, exam_id: str) -> list[dict]:
    """Fetch exam question metadata from the authenticated browser session."""
    js = f"""(async () => {{
      const token = localStorage.getItem("fuflex_token");
      const headers = token ? {{ Authorization: "Bearer " + token }} : {{}};
      const res = await fetch("/api/exams/{exam_id}/questions?revealAnswers=true", {{ headers }});
      const data = await res.json();
      if (!res.ok) {{
        throw new Error(data?.message || "Failed to fetch questions");
      }}
      return data.data || [];
    }})()"""
    return eval_js(session, js) or []


def download_missing_images(
    session: str,
    questions: list[dict],
    images_dir: Path,
    batch_size: int = 10,
) -> None:
    """Download question PNGs in batches via the browser session."""
    images_dir.mkdir(parents=True, exist_ok=True)
    missing = [
        q
        for q in questions
        if q.get("imageUrl")
        and not (images_dir / f"Q{q['questionNumber']:02d}.png").exists()
    ]
    if not missing:
        print("All question images already exist.")
        return

    for i in range(0, len(missing), batch_size):
        batch = missing[i : i + batch_size]
        urls = [q["imageUrl"] for q in batch]
        js = f"""(async () => {{
          const urls = {json.dumps(urls)};
          const out = [];
          for (const u of urls) {{
            const res = await fetch(u);
            if (!res.ok) throw new Error("Image fetch failed: " + res.status);
            const buf = await res.arrayBuffer();
            const bytes = new Uint8Array(buf);
            let bin = "";
            for (let j = 0; j < bytes.length; j += 0x8000) {{
              bin += String.fromCharCode(...bytes.subarray(j, j + 0x8000));
            }}
            out.push(btoa(bin));
          }}
          return out;
        }})()"""
        encoded_list = eval_js(session, js)
        for q, b64 in zip(batch, encoded_list):
            target = images_dir / f"Q{q['questionNumber']:02d}.png"
            target.write_bytes(base64.b64decode(b64))
        print(f"Downloaded images {i + 1}-{i + len(batch)} of {len(missing)}")


def write_markdown(questions: list[dict], exam_id: str, subject: str, out_path: Path) -> None:
    """Write a readable Markdown summary of questions, answers, and image links."""
    lines = [f"# {subject} (Exam #{exam_id})\n"]
    for q in questions:
        num = q.get("questionNumber")
        prompt = (q.get("questionPrompt") or "").strip()
        ans = q.get("answer")
        lines.append(f"## Question {num}")
        if prompt:
            lines.append(f"{prompt}\n")
        if ans:
            lines.append(f"- **Answer:** {ans}")
        lines.append(f"- **Image:** [Q{num:02d}.png](images/Q{num:02d}.png)\n")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    env_path = Path(".env")
    if not env_path.is_file():
        script_env = Path(__file__).resolve().parent / ".env"
        if script_env.is_file():
            env_path = script_env
    load_dotenv(env_path)

    exam_id = resolve_value("Exam ID (e.g. 3671)", env_var="FUFLEX_EXAM_ID")
    subject = resolve_value("Subject code (e.g. APO201C)", env_var="FUFLEX_SUBJECT")

    auth_envs = ("FUFLEX_TOKEN", "FUFLEX_VISITOR_ID", "FUFLEX_FX_TRUST", "FUFLEX_FX_DID")
    if any(not os.environ.get(k, "").strip() for k in auth_envs):
        print("\nEnter your FUFLEX browser session values (input is hidden for tokens/cookies):")

    fuflex_token = resolve_value("fuflex_token (localStorage)", env_var="FUFLEX_TOKEN", secret=True)
    visitor_id = resolve_value("fuflex_visitor_id (localStorage)", env_var="FUFLEX_VISITOR_ID")
    fx_trust = resolve_value("fx_trust (cookie)", env_var="FUFLEX_FX_TRUST", secret=True)
    fx_did = resolve_value("fx_did (cookie)", env_var="FUFLEX_FX_DID", secret=True)
    fx_auth = resolve_value(
        "fx_auth (cookie, press Enter to reuse fuflex_token)",
        env_var="FUFLEX_FX_AUTH",
        default=fuflex_token,
        secret=True,
    )

    output_dir = os.environ.get("FUFLEX_OUTPUT_DIR", ".").strip() or "."
    session = os.environ.get("FUFLEX_SESSION", "fuflex").strip() or "fuflex"

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    url = f"https://www.fuflex.site/exams/{exam_id}/images?subject={quote(subject)}"

    print(f"\nOpening remote browser session '{session}'...")
    run_browse(["open", url, "--session", session, "--remote"])
    try:
        eval_js(session, build_auth_js(fuflex_token, visitor_id, fx_trust, fx_did, fx_auth))
        run_browse(["reload", "--session", session])
        time.sleep(2)

        questions = fetch_questions(session, exam_id)
        json_path = out_dir / f"exam_{exam_id}_questions.json"
        md_path = out_dir / f"exam_{exam_id}_questions.md"
        json_path.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
        write_markdown(questions, exam_id, subject, md_path)
        print(f"Saved {len(questions)} questions to {json_path} and {md_path}")

        download_missing_images(session, questions, out_dir / "images")
    finally:
        print(f"Stopping browser session '{session}'...")
        subprocess.run(["browse", "stop", "--session", session], check=False)


if __name__ == "__main__":
    main()
