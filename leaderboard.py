"""
leaderboard.py — Track which training runs scored best.

Each run appends one row to leaderboard.csv with:
  success rate, avg reward, dominant question type at each step, episodes trained.

Usage
-----
  # View leaderboard (standalone)
  py -3.11 leaderboard.py

  # Clear leaderboard (start fresh)
  py -3.11 leaderboard.py --clear

  # Called automatically from main.py after evaluation.
"""

import os           # file existence checks
import sys          # arg parsing fallback
import argparse     # CLI flags
import pandas as pd  # CSV read/write
from datetime import datetime  # timestamps

LEADERBOARD_FILE = "leaderboard.csv"  # where scores are stored

# Columns written per run
_COLS = [
    "rank", "run_name", "timestamp",
    "episodes", "questions_in_vocab",
    "success_rate_pct", "avg_reward",
    "top_q_step1", "top_q_step2", "top_q_step3", "top_q_step4", "top_q_step5",
]


def _top_type_per_step(eval_results, max_steps):
    """Return list of dominant question type at each step position."""
    counts = [{} for _ in range(max_steps)]  # one dict per step
    for game in eval_results:                # iterate eval games
        for i, qtype in enumerate(game.get("question_types", [])):
            if i < max_steps:                # guard step index
                counts[i][qtype] = counts[i].get(qtype, 0) + 1  # tally
    tops = []
    for c in counts:                         # pick dominant type at each step
        tops.append(max(c, key=c.get) if c else "none")
    return tops                              # list[str] length max_steps


def record_run(evaluator, run_name=None, episodes=None):
    """Append current evaluation results as a new leaderboard row."""
    if not evaluator.eval_results:           # nothing to record
        print("[leaderboard] No eval results — run evaluation first.")
        return

    res = evaluator.baseline_results.get("agent", {})  # agent stats dict
    sr  = res.get("success_rate", 0) * 100   # success rate as %
    ar  = res.get("avg_reward", 0)            # avg reward float
    vocab_size = evaluator.env.question_space.size()  # question count
    max_steps  = evaluator.env.max_questions           # steps per game

    if run_name is None:                     # auto-name if not provided
        run_name = "run_" + datetime.now().strftime("%m%d_%H%M")

    tops = _top_type_per_step(evaluator.eval_results, max_steps)  # dominant types
    tops += ["—"] * (5 - len(tops))          # pad to 5 entries

    entry = {                                # build row dict
        "run_name":          run_name,
        "timestamp":         datetime.now().strftime("%Y-%m-%d %H:%M"),
        "episodes":          episodes if episodes is not None else "?",
        "questions_in_vocab": vocab_size,
        "success_rate_pct":  round(sr, 1),
        "avg_reward":        round(ar, 2),
        "top_q_step1":       tops[0],
        "top_q_step2":       tops[1],
        "top_q_step3":       tops[2],
        "top_q_step4":       tops[3],
        "top_q_step5":       tops[4],
    }

    if os.path.exists(LEADERBOARD_FILE):     # append to existing file
        df = pd.read_csv(LEADERBOARD_FILE)
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    else:                                    # create new file
        df = pd.DataFrame([entry])

    df = df.sort_values("success_rate_pct", ascending=False).reset_index(drop=True)
    df.to_csv(LEADERBOARD_FILE, index=False)      # persist without rank column
    print(f"[leaderboard] Recorded '{run_name}'  success={sr:.1f}%  reward={ar:.1f}")


def show_leaderboard():
    """Print ranked leaderboard table from leaderboard.csv."""
    if not os.path.exists(LEADERBOARD_FILE):  # no data yet
        print("No leaderboard yet. Train the model first: py -3.11 main.py")
        return

    df = pd.read_csv(LEADERBOARD_FILE)        # load all runs
    df = df.sort_values("success_rate_pct", ascending=False).reset_index(drop=True)

    sep = "-" * 100                           # table separator
    print(f"\n{'='*100}")
    print(f"  LEADERBOARD  ({len(df)} run{'s' if len(df) != 1 else ''})")
    print(f"{'='*100}")
    print(f"  {'#':<4} {'Run Name':<22} {'Success':>8} {'Reward':>8} "
          f"{'Q-vocab':>7} {'Ep':>7}   Q1>Q2>Q3      Date")
    print(sep)

    medals = {1: "[1]", 2: "[2]", 3: "[3]"}  # top 3 markers

    for i, row in df.iterrows():
        rank   = i + 1                        # 1-based rank
        medal  = medals.get(rank, f"  {rank} ")  # medal or number
        name   = str(row["run_name"])[:20]    # truncate long names
        sr     = row["success_rate_pct"]
        ar     = row.get("avg_reward", "?")
        vocab  = row.get("questions_in_vocab", "?")
        ep     = str(row.get("episodes", "?"))
        q1     = str(row.get("top_q_step1", "?"))[:8]  # step 1 type
        q2     = str(row.get("top_q_step2", "?"))[:8]  # step 2 type
        q3     = str(row.get("top_q_step3", "?"))[:8]  # step 3 type
        ts     = str(row.get("timestamp", ""))[:16]     # date+time

        print(f"  {medal:<4} {name:<22} {sr:>7.1f}%  {str(ar):>8}  "
              f"{str(vocab):>6}  {ep:>6}   {q1}|{q2}|{q3}  {ts}")

    print(sep)

    if len(df) > 1:                           # show improvement summary
        best = df.iloc[0]
        print(f"\n  Best run : {best['run_name']}  ({best['success_rate_pct']:.1f}%)")
        worst = df.iloc[-1]
        delta = best["success_rate_pct"] - worst["success_rate_pct"]
        print(f"  Spread   : {delta:.1f}pp between best and worst run")

    print()


def clear_leaderboard():
    """Delete leaderboard.csv after confirmation."""
    if not os.path.exists(LEADERBOARD_FILE):  # nothing to clear
        print("No leaderboard file found.")
        return
    ans = input("Clear leaderboard? This cannot be undone. [y/N]: ").strip().lower()
    if ans == "y":
        os.remove(LEADERBOARD_FILE)           # delete file
        print("Leaderboard cleared.")
    else:
        print("Aborted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View or manage the run leaderboard")
    parser.add_argument("--clear", action="store_true", help="Wipe leaderboard.csv")
    args = parser.parse_args()

    if args.clear:
        clear_leaderboard()                   # wipe file
    else:
        show_leaderboard()                    # print table
