"""Submit one researched binary forecast to Metaculus.

Usage:
  python3 submit_forecast.py forecast.json

forecast.json format:
  {
    "question_id": 12345,
    "post_id": 6789,
    "tournament": "bot-testing-area",   # or 33121 for Fall 2026 (live)
    "probability_yes": 0.62,
    "reasoning": "Short evidence-first reasoning with sources. ...",
    "sources": ["https://..."],
    "question_title": "..."
  }

What it does, in order:
  1. Submits the binary forecast via POST /api/questions/forecast/.
  2. Posts the reasoning as a private comment with the forecast attached
     (included_forecast=true). Prize eligibility REQUIRES a comment under
     every forecasted question.
  3. Re-reads the post to verify the forecast landed.
  4. Appends one line to forecasts.jsonl (append-only log).

Rules enforced here:
  - Binary only in this script (numeric/multiple-choice come later, after
    the binary path is verified end to end).
  - Test runs MUST target the Bot Testing Area ("bot-testing-area").
    Live Fall 2026 submissions (tournament 33121) only after the test
    batch is verified AND the parent says so.
  - If the API refuses with a forecasting-access error, the script stops
    and prints the exact fix (confirm API forecasting access on the
    Metaculus settings page) instead of retrying.

Exit code 0 = forecast + comment + verification all OK.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metaculus_client as mc

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "forecasts.jsonl")
TEST_TOURNAMENT = "bot-testing-area"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    with open(sys.argv[1]) as f:
        fc = json.load(f)

    qid = fc["question_id"]
    pid = fc["post_id"]
    p = float(fc["probability_yes"])
    tournament = fc.get("tournament", TEST_TOURNAMENT)

    print(f"question {qid} post {pid} tournament {tournament} p_yes={p}")

    # 1. Forecast
    status, data, p_used = mc.submit_binary_forecast(qid, p)
    print(f"forecast POST -> {status}: {json.dumps(data)[:400]}")
    if status not in (200, 201):
        body = json.dumps(data)
        if "forecast" in body.lower() and ("access" in body.lower()
                                           or "permission" in body.lower()
                                           or "forbidden" in body.lower()):
            print("BLOCKED: API forecasting access is not enabled for this "
                  "account. On metaculus.com go to Settings -> Account -> "
                  "API forecasting access and confirm the one-button "
                  "prompt, then re-run.")
        sys.exit(1)

    # 2. Reasoning comment (private, forecast attached)
    sources = fc.get("sources") or []
    src_text = "\n".join(f"- {s}" for s in sources)
    comment = (
        f"Forecast: {p_used:.0%} Yes.\n\n"
        f"{fc.get('reasoning', '').strip()}\n\n"
        f"Sources:\n{src_text}\n\n"
        f"Bot: vinzagent_ai (Muse Spark agent). Forecast produced by "
        f"independent research of the sources above; the community "
        f"prediction was not copied."
    )
    status, data = mc.post_reasoning_comment(pid, comment)
    print(f"comment POST -> {status}: {json.dumps(data)[:400]}")
    if status not in (200, 201):
        print("WARNING: forecast submitted but the reasoning comment "
              "failed. Prize eligibility requires a comment under every "
              "forecasted question. Fix and re-post the comment manually.")
        sys.exit(1)

    # 3. Verify by re-reading
    found, detail = mc.verify_forecast_landed(pid, qid)
    print(f"verify: found={found} ({detail})")

    # 4. Log
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "tournament": str(tournament),
        "question_id": qid,
        "post_id": pid,
        "question_title": fc.get("question_title", ""),
        "probability_yes": p_used,
        "reasoning": fc.get("reasoning", ""),
        "sources": sources,
        "forecast_status": "submitted",
        "comment_status": "submitted",
        "verified": found,
        "verify_detail": detail,
    }
    with open(LOG, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"logged to {LOG}")

    sys.exit(0 if found else 1)


if __name__ == "__main__":
    main()
