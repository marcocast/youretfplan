#!/usr/bin/env python3
"""Daily export of youretfplan.com usage data into growth/data/.

Runs in GitHub Actions (see .github/workflows/export.yml), which can reach the
Cloudflare API. Reads:
  - D1 database `youretfplan`: anonymous funnel steps and feedback (worker/index.js)
  - Cloudflare Web Analytics (RUM): visits by day, page, referrer, country, device

Writes:
  - growth/data/latest.json             full snapshot of the last 35 days
  - growth/data/daily/YYYY-MM-DD.json   the same snapshot, kept per day
  - growth/data/feedback.jsonl          every feedback entry, appended (no visitor ids)
  - growth/data/state.json              last exported feedback id

Errors from either source are written into the snapshot under "errors" instead of
failing the job, so problems are visible in the repo.

Env: CF_API_TOKEN, CF_ACCOUNT_ID, D1_DATABASE_ID, CF_SITE_TAG
"""
import datetime as dt
import json
import os
import pathlib
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "growth" / "data"
API = "https://api.cloudflare.com/client/v4"
FUNNEL = ["view", "hook", "plan", "calc_seen", "active", "explore", "start_seen", "faq", "bottom", "feedback", "share"]

TOKEN = os.environ.get("CF_API_TOKEN", "")
ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "")
D1 = os.environ.get("D1_DATABASE_ID", "")
SITE_TAG = os.environ.get("CF_SITE_TAG", "")


def call(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        API + path,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:2000]
        raise RuntimeError(f"HTTP {e.code} on {path}: {body}") from None


def d1(sql: str, params=None) -> list:
    out = call(f"/accounts/{ACCOUNT}/d1/database/{D1}/query", {"sql": sql, "params": params or []})
    if not out.get("success"):
        raise RuntimeError(f"D1 error: {out.get('errors')}")
    return out["result"][0]["results"]


RUM_QUERY = """
query ($accountTag: string, $byDay: AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject,
       $recent: AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject) {
  viewer {
    accounts(filter: {accountTag: $accountTag}) {
      byDay: rumPageloadEventsAdaptiveGroups(limit: 100, filter: $byDay) {
        count
        sum { visits }
        dimensions { date }
      }
      byPath: rumPageloadEventsAdaptiveGroups(limit: 50, filter: $recent, orderBy: [count_DESC]) {
        count
        sum { visits }
        dimensions { requestPath }
      }
      byReferer: rumPageloadEventsAdaptiveGroups(limit: 50, filter: $recent, orderBy: [count_DESC]) {
        count
        sum { visits }
        dimensions { refererHost }
      }
      byCountry: rumPageloadEventsAdaptiveGroups(limit: 50, filter: $recent, orderBy: [count_DESC]) {
        count
        sum { visits }
        dimensions { countryName }
      }
      byDevice: rumPageloadEventsAdaptiveGroups(limit: 10, filter: $recent, orderBy: [count_DESC]) {
        count
        sum { visits }
        dimensions { deviceType }
      }
    }
  }
}
"""


def rum(start: str, recent_start: str, end: str) -> dict:
    out = call("/graphql", {
        "query": RUM_QUERY,
        "variables": {
            "accountTag": ACCOUNT,
            "byDay": {"siteTag": SITE_TAG, "date_geq": start, "date_leq": end},
            "recent": {"siteTag": SITE_TAG, "date_geq": recent_start, "date_leq": end},
        },
    })
    if out.get("errors"):
        raise RuntimeError(f"GraphQL errors: {out['errors']}")
    acc = out["data"]["viewer"]["accounts"][0]

    def flat(rows, key):
        return [{key: r["dimensions"][key], "pageviews": r["count"], "visits": r["sum"]["visits"]} for r in rows]

    return {
        "by_day": sorted(flat(acc["byDay"], "date"), key=lambda r: r["date"]),
        "last_7_days": {
            "pages": flat(acc["byPath"], "requestPath"),
            "referrers": flat(acc["byReferer"], "refererHost"),
            "countries": flat(acc["byCountry"], "countryName"),
            "devices": flat(acc["byDevice"], "deviceType"),
        },
    }


def funnel(start: str, recent_start: str) -> dict:
    rows = d1("SELECT day, step, COUNT(*) AS n FROM events WHERE day >= ? GROUP BY day, step", [start])
    by_day = {}
    for r in rows:
        by_day.setdefault(r["day"], {s: 0 for s in FUNNEL})[r["step"]] = r["n"]
    breakdown = d1(
        "SELECT step, lang, device, source, COUNT(*) AS n FROM events "
        "WHERE day >= ? AND (step IN ('view', 'hook', 'plan', 'calc_seen', 'active') OR step LIKE 'sc\\_%' ESCAPE '\\') "
        "GROUP BY step, lang, device, source ORDER BY n DESC",
        [recent_start],
    )
    monthly = d1(
        "SELECT substr(day, 1, 7) AS month, COUNT(*) AS active_user_days "
        "FROM events WHERE step = 'active' GROUP BY month ORDER BY month"
    )
    return {
        "note": "Counts are unique visitors per day per step. Monthly figures sum daily uniques, "
                "so a person active on 3 days counts 3 times.",
        "by_day": [dict(day=d, **steps) for d, steps in sorted(by_day.items())],
        "last_7_days_breakdown": breakdown,
        "monthly_active": monthly,
    }


def new_feedback(after_id: int) -> list:
    return d1(
        "SELECT id, ts, lang, place, vote, comment, device, country FROM feedback WHERE id > ? ORDER BY id",
        [after_id],
    )


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "daily").mkdir(exist_ok=True)
    today = dt.datetime.now(dt.timezone.utc).date()
    end = today.isoformat()
    start = (today - dt.timedelta(days=35)).isoformat()
    recent_start = (today - dt.timedelta(days=7)).isoformat()

    snapshot = {"generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "range": {"from": start, "to": end}, "errors": []}
    missing = [k for k, v in {"CF_API_TOKEN": TOKEN, "CF_ACCOUNT_ID": ACCOUNT,
                              "D1_DATABASE_ID": D1, "CF_SITE_TAG": SITE_TAG}.items() if not v]
    if missing:
        snapshot["errors"].append(f"missing settings: {', '.join(missing)}")

    try:
        snapshot["web_analytics"] = rum(start, recent_start, end)
    except Exception as e:  # keep going, record the problem
        snapshot["errors"].append(f"web analytics: {e}")
    try:
        snapshot["funnel"] = funnel(start, recent_start)
    except Exception as e:
        snapshot["errors"].append(f"funnel: {e}")

    state_file = DATA / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"last_feedback_id": 0}
    try:
        rows = new_feedback(state["last_feedback_id"])
        with open(DATA / "feedback.jsonl", "a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        if rows:
            state["last_feedback_id"] = rows[-1]["id"]
        snapshot["new_feedback"] = len(rows)
    except Exception as e:
        snapshot["errors"].append(f"feedback: {e}")

    text = json.dumps(snapshot, ensure_ascii=False, indent=1)
    (DATA / "latest.json").write_text(text + "\n", encoding="utf-8")
    (DATA / "daily" / f"{end}.json").write_text(text + "\n", encoding="utf-8")
    state_file.write_text(json.dumps(state) + "\n")
    print(f"exported {end}; errors: {snapshot['errors'] or 'none'}")


if __name__ == "__main__":
    main()
