"""Shared infrastructure: paths, ledger, payload-on-disk send funnel.

Hard rules enforced here (DESIGN.md):
- No live API call before its payload exists on disk: every send goes through
  send_call(), which appends the exact request body to a payload log with
  fsync BEFORE posting.
- No call once the ledger reaches the cap: send_call() checks the ledger
  before every single post.
- The API key is loaded from .env and never logged; headers are never written
  to any file.
"""
from __future__ import annotations

import asyncio
import datetime
import json
import os
import pathlib
import random

import httpx
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

LEDGER_PATH = ROOT / "ledger.json"

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504, 520, 522, 524}


def utcnow() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_jsonl(path, obj) -> None:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path):
    path = pathlib.Path(path)
    if not path.exists():
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def append_status(text: str) -> None:
    """Append a timestamped entry to STATUS.md."""
    p = ROOT / "STATUS.md"
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"\n## [{utcnow()}] {text}\n")


class BudgetExceeded(RuntimeError):
    pass


class ApiCallError(RuntimeError):
    def __init__(self, status, detail):
        super().__init__(f"API error {status}: {detail}")
        self.status = status
        self.detail = detail


class Ledger:
    """Spend ledger. Hard cap enforced before every call. Atomic writes."""

    def __init__(self, path=LEDGER_PATH):
        self.path = pathlib.Path(path)
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    @property
    def spent(self) -> float:
        return self.data["spent_usd"]

    @property
    def cap(self) -> float:
        return self.data["cap_usd"]

    def remaining(self) -> float:
        return self.cap - self.spent

    def check(self) -> None:
        if self.spent >= self.cap:
            raise BudgetExceeded(
                f"ledger at ${self.spent:.4f} >= cap ${self.cap:.2f}; no further calls"
            )

    def add(self, cost, model_key: str, purpose: str, estimated: bool = False) -> None:
        cost = float(cost or 0.0)
        self.data["spent_usd"] = round(self.data["spent_usd"] + cost, 6)
        self.data["calls"] += 1
        self.data["by_purpose"][purpose] = round(
            self.data["by_purpose"].get(purpose, 0.0) + cost, 6
        )
        self.data["by_model"][model_key] = round(
            self.data["by_model"].get(model_key, 0.0) + cost, 6
        )
        if estimated:
            self.data["estimated_cost_calls"] += 1
        self.data["updated"] = utcnow()
        self._save()

    def note_mismatch(self, entry: dict) -> None:
        self.data["provider_mismatches"].append(entry)
        self._save()

    def _save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)


def headers() -> dict:
    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing from environment")
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-Title": "quiet-quitting-study1",
    }


async def send_call(
    client: httpx.AsyncClient,
    request_body: dict,
    payload_log,
    purpose: str,
    model_key: str,
    ledger: Ledger,
    pricing: dict | None = None,
    max_retries: int = 5,
    timeout: float = 300.0,
) -> dict:
    """The single live-call funnel.

    1. Append the exact request body to payload_log (fsync) — payload on disk
       before any send.
    2. Check the ledger cap.
    3. POST with retries on transient failures.
    4. Record cost (response.usage.cost when present, else pricing estimate).
    """
    append_jsonl(payload_log, {"ts": utcnow(), "purpose": purpose, "model_key": model_key,
                               "request": request_body})
    last_detail = None
    for attempt in range(max_retries):
        ledger.check()
        try:
            r = await client.post(
                f"{BASE_URL}/chat/completions",
                json=request_body,
                headers=headers(),
                timeout=timeout,
            )
        except (httpx.TimeoutException, httpx.TransportError) as e:
            last_detail = f"transport: {type(e).__name__}"
            await asyncio.sleep(min(60, 2 ** attempt + random.random()))
            continue
        if r.status_code == 200:
            try:
                data = r.json()
            except Exception:
                last_detail = "unparseable 200 body"
                await asyncio.sleep(min(60, 2 ** attempt + random.random()))
                continue
            err = data.get("error")
            if err:
                code = err.get("code", 0)
                last_detail = f"in-body error {code}: {str(err.get('message'))[:300]}"
                if int(code or 0) in RETRYABLE_STATUS:
                    await asyncio.sleep(min(60, 2 ** attempt + random.random()))
                    continue
                raise ApiCallError(code, last_detail)
            usage = data.get("usage") or {}
            cost = usage.get("cost")
            estimated = False
            if cost is None and pricing:
                cost = (usage.get("prompt_tokens", 0) * float(pricing.get("prompt", 0))
                        + usage.get("completion_tokens", 0) * float(pricing.get("completion", 0)))
                estimated = True
            ledger.add(cost or 0.0, model_key, purpose, estimated=estimated)
            return data
        if r.status_code in RETRYABLE_STATUS:
            last_detail = f"http {r.status_code}: {r.text[:300]}"
            # Honor Retry-After when present
            ra = r.headers.get("retry-after")
            delay = min(60, float(ra)) if ra and ra.replace(".", "", 1).isdigit() else min(
                60, 2 ** attempt + random.random()
            )
            await asyncio.sleep(delay)
            continue
        raise ApiCallError(r.status_code, r.text[:500])
    raise ApiCallError(-1, f"retries exhausted: {last_detail}")


def get_json(path_suffix: str, timeout: float = 60.0) -> dict:
    """Synchronous authenticated GET against the OpenRouter API (no cost)."""
    r = httpx.get(f"{BASE_URL}/{path_suffix}", headers=headers(), timeout=timeout)
    r.raise_for_status()
    return r.json()
