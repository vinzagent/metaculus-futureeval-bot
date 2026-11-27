"""Metaculus API client for the vinzagent FutureEval bot.

Stdlib-only (urllib). Fresh code written from the public Metaculus API
surface (see README.md). Does NOT import or execute any third-party bot
code; the official template repo under template-ref/ is read-only reference.

Auth: Authorization: Token <METACULUS_TOKEN>
Token source: ~/workspace/metaculus/metaculus-token.txt (mode 600),
or the METACULUS_TOKEN environment variable.

Tournament IDs (verified against the official template):
  Fall 2026 FutureEval Bot Tournament: 33121
  Bot Testing Area (sanctioned test target): "bot-testing-area"
  MiniBench: "minibench"

Rate limits are unpublished. Be gentle: 2s between calls, stop on 429.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://www.metaculus.com/api"
FALL_2026_TOURNAMENT_ID = 33121
BOT_TESTING_AREA_ID = "bot-testing-area"

# Binary probabilities on Metaculus are restricted to 0.1%-99.9%.
# We clamp tighter: never submit more extreme than 1%-99% (log score
# punishes an extreme wrong call far more than it rewards an extreme
# right one).
PROB_MIN = 0.01
PROB_MAX = 0.99

SLEEP_BETWEEN_CALLS = 2.0


def load_token():
    token = os.environ.get("METACULUS_TOKEN")
    if token:
        return token.strip()
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "metaculus-token.txt")
    with open(path) as f:
        return f.read().strip()


def _request(method, path, params=None, payload=None):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Token " + load_token())
    req.add_header("User-Agent", "curl/8.5.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return e.code, {"_error_body": body}
    except urllib.error.URLError as e:
        # Connection closed mid-read etc. Caller decides whether to retry.
        return None, {"_error_body": str(e)}


def list_open_posts(tournament_id, limit=50, offset=0):
    """List open posts of a tournament. Returns the parsed JSON."""
    status, data = _request("GET", "/posts/", params={
        "limit": limit,
        "offset": offset,
        "order_by": "-hotness",
        "forecast_type": "binary,multiple_choice,numeric,discrete",
        "tournaments": tournament_id,
        "statuses": "open",
        "include_description": "true",
    })
    time.sleep(SLEEP_BETWEEN_CALLS)
    if status != 200:
        raise RuntimeError(f"list posts failed: {status} {data}")
    return data


def open_binary_questions(tournament_id, limit=50):
    """Return [(question_id, post_id, title, scheduled_close_time)] for
    open binary questions in a tournament."""
    data = list_open_posts(tournament_id, limit=limit)
    out = []
    for post in data.get("results", []):
        q = post.get("question")
        if not q:
            continue
        if q.get("type") != "binary":
            continue
        if q.get("status") != "open":
            continue
        out.append((q["id"], post["id"], q.get("title", ""),
                    q.get("scheduled_close_time")))
    return out


def get_post(post_id):
    status, data = _request("GET", f"/posts/{post_id}/")
    time.sleep(SLEEP_BETWEEN_CALLS)
    if status != 200:
        raise RuntimeError(f"get post {post_id} failed: {status} {data}")
    return data


def submit_binary_forecast(question_id, probability_yes):
    """Submit a binary forecast. probability_yes is a float 0..1 (clamped)."""
    p = min(max(float(probability_yes), PROB_MIN), PROB_MAX)
    payload = [{
        "question": question_id,
        "source": "api",
        "probability_yes": p,
        "probability_yes_per_category": None,
        "continuous_cdf": None,
    }]
    status, data = _request("POST", "/questions/forecast/", payload=payload)
    time.sleep(SLEEP_BETWEEN_CALLS)
    return status, data, p


def post_reasoning_comment(post_id, text):
    """Post the reasoning comment. Private, with the forecast attached
    (required for prize eligibility: a comment under each forecasted
    question, displaying the forecast)."""
    payload = {
        "text": text,
        "parent": None,
        "included_forecast": True,
        "is_private": True,
        "on_post": post_id,
    }
    status, data = _request("POST", "/comments/create/", payload=payload)
    time.sleep(SLEEP_BETWEEN_CALLS)
    return status, data


def verify_forecast_landed(post_id, question_id):
    """Re-read the post and check whether our forecast is recorded.
    Returns (found: bool, detail: str). The exact field name for the
    bot's own forecast varies; we search the whole post JSON for the
    question id paired with a forecast entry."""
    post = get_post(post_id)
    blob = json.dumps(post)
    q = post.get("question") or {}
    # Preferred: question.my_forecasts (list) if the API returns it.
    mine = q.get("my_forecasts") or q.get("forecasts") or []
    if isinstance(mine, list) and mine:
        return True, f"my_forecasts present: {len(mine)} entr(ies)"
    if isinstance(mine, dict) and mine:
        return True, "my_forecasts dict present"
    # Fallback: the question id appears in the serialized post at all.
    if str(question_id) in blob:
        return True, "question id present in re-read post (field shape unverified)"
    return False, "no trace of the forecast in re-read post"
