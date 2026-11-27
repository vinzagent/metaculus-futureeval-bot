"""List open binary questions of a Metaculus tournament.

Usage:
  python3 list_open.py [tournament] [limit]
    tournament: "bot-testing-area" (default, test target) or 33121 (Fall 2026 live)
    limit: how many posts to fetch (default 50)

Prints one line per open binary question:
  question_id | post_id | closes | title
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metaculus_client as mc

if __name__ == "__main__":
    tournament = sys.argv[1] if len(sys.argv) > 1 else mc.BOT_TESTING_AREA_ID
    try:
        tournament = int(tournament)
    except ValueError:
        pass
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    for qid, pid, title, closes in mc.open_binary_questions(tournament, limit=limit):
        print(f"{qid} | {pid} | {closes} | {title}")
