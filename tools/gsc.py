"""Google Search Console numbers for the daily export (optional).

Only runs when the GSC_SA_JSON secret is set: the JSON key of a Google Cloud
service account that has the Search Console API enabled and is added as a
(restricted) user on the youretfplan.com property. Without it the export skips
this part silently.

Returns impressions, clicks and average position by day, plus the top queries and
pages of the last 7 days. Aggregate search data only, no visitor data.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
SITES = [s for s in [os.environ.get("GSC_SITE", ""), "sc-domain:youretfplan.com", "https://youretfplan.com/"] if s]


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _token(sa: dict) -> str:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now = int(time.time())
    head = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = _b64(json.dumps({"iss": sa["client_email"], "scope": SCOPE, "aud": sa["token_uri"],
                             "iat": now, "exp": now + 3600}).encode())
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = key.sign(f"{head}.{claim}".encode(), padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{head}.{claim}.{_b64(sig)}"
    body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                                   "assertion": jwt}).encode()
    with urllib.request.urlopen(urllib.request.Request(sa["token_uri"], data=body), timeout=30) as r:
        return json.loads(r.read())["access_token"]


def _query(token: str, site: str, payload: dict) -> list:
    url = ("https://www.googleapis.com/webmasters/v3/sites/"
           + urllib.parse.quote(site, safe="") + "/searchAnalytics/query")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read()).get("rows", [])


def search_console(start: str, recent_start: str, end: str):
    raw = os.environ.get("GSC_SA_JSON", "").strip()
    if not raw:
        return None  # not configured yet
    token = _token(json.loads(raw))
    last_err = None
    for site in SITES:
        try:
            days = _query(token, site, {"startDate": start, "endDate": end, "dimensions": ["date"]})
        except urllib.error.HTTPError as e:
            last_err = f"{site}: HTTP {e.code} {e.read().decode(errors='replace')[:300]}"
            continue

        def top(dim):
            rows = _query(token, site, {"startDate": recent_start, "endDate": end,
                                        "dimensions": [dim], "rowLimit": 50})
            return [{dim: r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"],
                     "position": round(r["position"], 1)} for r in rows]

        return {
            "site": site,
            "by_day": [{"date": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"],
                        "position": round(r["position"], 1)} for r in days],
            "last_7_days": {"queries": top("query"), "pages": top("page"), "countries": top("country")},
        }
    raise RuntimeError(last_err or "no Search Console property found")
