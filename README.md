# Metaculus FutureEval Bot Tournament — vinzagent

**Tournament:** Fall 2026 FutureEval Bot Tournament (Seasonal Bot Tournament)
**Prize pool:** $50,000 per season. **Entry:** free. **Season:** 28 Sep 2026 – 6 Jan 2027.
**Questions:** ~300–400 (binary, numeric, discrete, multiple-choice).
**Tournament page:** https://www.metaculus.com/tournament/fall-futureeval-2026/
**Rules:** https://www.metaculus.com/notebooks/28751/futureeval-competition-rules/
**Participate:** https://www.metaculus.com/futureeval/participate/
**Status (2026-11-26 ~16:46 WIB):** account + bot CREATED by Kevin (bot
**vinzagent_ai**, user id 314063; plain "vinzagent" was taken). Token stored
mode 600 in `metaculus-token.txt` (Kevin sent it in chat, not via secure
card — his choice). **Test batch DONE:** 1 forecast on the Bot Testing Area
(EU-exit question 43332, 1% Yes, reasoning comment id 1364880, verified
`my_forecasts` present, logged in `forecasts.jsonl`). Note: the forecast
landed twice (identical 1%) because `submit_forecast.py` treated HTTP 201
as failure — fixed to accept 200/201. **Participation form SUBMITTED
~16:44 WIB** (Who are you = Non-Student Hobbyist; LLM credits = No, closed
for Fall; GitHub repo + links left blank). **Tournament registration: NO
Register button exists.** Kevin switched to bot-account view (banner
confirmed 16:45 WIB) and scrolled the whole tournament page to the bottom
("mentok") — only Follow + View Questions (206), no Register/Join anywhere.
Corroborated: the participate page's 3 steps have no registration step;
the Fall announcement says competitors "join any time... and will start in
the middle of the leaderboard with 0 points"; third-party bot docs
(Marina) show the flow as create bot -> forecast, no register click. The
rules notebook's "register via the landing page" line is stale boilerplate.
CONCLUSION: entry = forecasting on tournament questions (+ the form, done).
**Live status 2026-11-26 ~16:55 WIB:** ZERO open questions in tournament
33121 right now (API: 0 open via slug and numeric id; last binary closed
06:00Z / 13:00 WIB today). Tournament questions open at random hours for
~3h each, usually <=5 open at once. **Watcher cron `metaculus-live-watch`
SET 2026-11-26 ~17:00 WIB:** every 30 min, lists open binary questions
for 33121, researches + submits max 3 new ones per run (binary only,
evidence-first, never reads CP first, reasoning comment via
submit_forecast.py), skips anything already in forecasts.jsonl, reports
each new forecast to the WhatsApp side chat, stays silent when nothing is
open. First run ~17:01 WIB. AFTER the first live forecast lands, verify
vinzagent_ai appears on the Fall 2026 leaderboard — that confirms entry.

Delphi remains the priority until it ends 11 Dec 2026; this is track 2.

## Rules summary (read the full rules notebook before changing anything)

- Create a **free Metaculus bot account** and **register for the tournament
  via the tournament landing page** (accepting the terms).
- One bot per person; one prize-eligible bot per user.
- The bot must **autonomously generate forecasts + a written comment
  accompanying each forecast**. Prize eligibility requires a comment
  (displaying the forecast) under **every** question it forecasts.
- **No human in the loop when forecasting.** This includes running the bot
  on open/upcoming tournament questions, seeing its output, and then
  modifying the bot to improve its output. Consequence for us: test ONLY
  on the Bot Testing Area; never tune the method against live tournament
  questions or outcomes.
- **Do NOT blindly copy the community prediction** (programmatically or via
  an LLM). The CP may be incorporated in other ways, but the forecast must
  come from independent reasoning. Our workflow: research first, forecast
  from evidence, never read the CP before forecasting.
- Bot makers must provide a description of how the bot works or the actual
  code, and agree to a code inspection by Metaculus.
- Prizes are allocated by **weighted Peer Score** (see Scoring below).
  Winners are contacted within 5 business days of the announcement; prizes
  unclaimed within 30 days may be forfeited. Identity/nationality/residency
  verification is required for payout.
- All participants must fill out the first section of the participation
  form (3 required questions; also the route to apply for free LLM credits).

## Scoring (from the Scores FAQ)

- Log score (proper): predict your true beliefs; extremes are punished
  far more than rewarded. Binary predictions are restricted to 0.1%–99.9%.
- **Peer score** = your log score minus the average log score of all other
  forecasters on the question, ×100. Positive = better than the crowd.
  Sum of all Peer scores on a question is 0.
- Scores are **time-averaged over the question's lifetime**: before you
  predict, your score for that period is 0. Predicting early matters.
- Tournament score = weighted Peer Score across questions; prizes depend
  on rank and forecasting performance.

## Account setup — BLOCKED, needs the live browser (parent agent / Kevin)

I (subagent) cannot drive the live browser, so the account does not exist
yet. Exact steps:

1. Go to https://www.metaculus.com/ and **sign up** with email
   **kevinp280198@gmail.com**, username **vinzagent** (human account).
   Verify the email (check Gmail kevinp280198@gmail.com for the
   verification mail and click it).
2. Sign in, go to **Settings → My Forecasting Bots**, create a **bot
   account** named **vinzagent**, and copy its API token.
3. Store the token in `~/workspace/metaculus/metaculus-token.txt`
   (**mode 600**, never print it, never commit it).
4. On the tournament landing page
   (https://www.metaculus.com/tournament/fall-futureeval-2026/)
   **register the bot** for the Fall 2026 tournament (accept the terms).
5. Fill out the **first section of the participation form** (3 required
   questions; linked from the participate page). This is required of all
   participants. (Free LLM credits are offered via the same form, but we
   do not need them: the agent itself does the reasoning.)
6. If the first forecast attempt is refused for forecasting access, go to
   **Settings → Account → API forecasting access** and confirm the
   one-button prompt that appears once the setting is pending.

## Bot design

The bot is the agent + this API client (no separate LLM key needed: the
agent does the research and the probability judgment, exactly like the
Delphi evidence workflow).

- `metaculus_client.py` — stdlib-only API client (fresh code written from
  the public API surface; the official template under `template-ref/` is
  read-only reference, never executed).
  - Base `https://www.metaculus.com/api`, auth `Authorization: Token <token>`.
  - `GET /posts/` (tournaments, statuses=open, forecast_type filter),
    `GET /posts/{id}/`, `POST /questions/forecast/`,
    `POST /comments/create/`.
  - Binary payload: `{"question": id, "source": "api",
    "probability_yes": p, "probability_yes_per_category": null,
    "continuous_cdf": null}`. Probabilities clamped to 1%–99%.
  - Reasoning comment: private, `included_forecast: true`,
    `on_post: post_id`.
  - 2s between calls; stop on 429.
- `list_open.py` — list open binary questions of a tournament.
  Default target is the Bot Testing Area.
- `submit_forecast.py` — submit one researched forecast JSON: forecast →
  reasoning comment → verify by re-reading the post → append to
  `forecasts.jsonl`.
- `forecasts.jsonl` — append-only log of every submitted forecast.

Tournament IDs: Fall 2026 = **33121**; Bot Testing Area = **"bot-testing-area"**;
MiniBench = "minibench".

## How to run

**Test batch first (Bot Testing Area only):**

```
cd ~/workspace/metaculus
python3 list_open.py bot-testing-area 20     # pick 3-5 binary questions
# research each question (web search, evidence-first), write one JSON per
# question, then:
python3 submit_forecast.py forecast-1.json
```

A forecast JSON looks like:

```json
{
  "question_id": 12345,
  "post_id": 6789,
  "tournament": "bot-testing-area",
  "probability_yes": 0.62,
  "reasoning": "Evidence-first reasoning with numbers and dates.",
  "sources": ["https://example.com/..."],
  "question_title": "Will ... ?"
}
```

Verify each submission landed (the script re-reads the post; exit code 0
means forecast + comment + verification all OK). Then report the results
to the parent before scaling.

**Live run (only after the test batch is verified AND the parent says so):**
same flow with `"tournament": 33121`, binary questions first. Numeric and
multiple-choice support comes later, after the binary path is proven.

**Scaling:** run in small batches (a few questions per run), re-list open
questions each time, skip anything already in `forecasts.jsonl`. A daily
scheduled run can be added once the test batch is verified.

## Files

- `metaculus_client.py`, `submit_forecast.py`, `list_open.py` — the bot.
- `forecasts.jsonl` — append-only submission log.
- `metaculus-token.txt` — API token, mode 600 (CREATED 2026-11-26).
- `template-ref/` — official Metaculus template repo, READ-ONLY reference.
  Execution-risk flagged: never run, build, install, import, or execute
  anything from it; never copy its files elsewhere. Plain-text reading only.
