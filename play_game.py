"""
play_game.py — Test the trained agent interactively.

Usage
-----
  py -3.11 play_game.py                  # agent plays 5 random games (detailed)
  py -3.11 play_game.py --secret 742     # agent tries to guess YOUR number
  py -3.11 play_game.py --games 10       # agent plays 10 random games
  py -3.11 play_game.py --quick 200      # 200 games, summary only (fast benchmark)
  py -3.11 play_game.py --list-questions # print all questions and exit
"""

import sys
import os
import glob
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from environment.game_env import NumberGuessingEnv
from agent.rl_agent import RLAgent

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"


def load_agent(env):
    state_size  = 13
    action_size = env.question_space.size()
    agent = RLAgent(state_size=state_size, action_size=action_size, epsilon=0.0)

    checkpoints = glob.glob("checkpoints/*.weights.h5")
    if not checkpoints:
        print(f"{YELLOW}[!] No checkpoint found — agent will guess randomly.{RESET}")
        print(f"    Train first:  py -3.11 main.py\n")
        return agent

    latest = max(checkpoints, key=os.path.getmtime)
    try:
        agent.load(latest)
        ep = os.path.basename(latest).replace(".weights.h5", "")
        print(f"{GREEN}[OK] Loaded {ep}{RESET}  ({latest})\n")
    except Exception as err:
        print(f"{YELLOW}[!] Could not load checkpoint ({err}).{RESET}")
        print(f"    Architecture changed? Retrain:  py -3.11 main.py\n")
    return agent


def play_one_game(env, agent, secret=None, verbose=True):
    state = env.reset()
    if secret is not None:
        env.secret_number = secret
        low, high = env.number_range
        env.remaining_candidates = list(range(low, high + 1))
        state = env.get_state()

    if verbose:
        print(f"\n{CYAN}" + "-" * 55 + RESET)
        print(f"{CYAN}  SECRET: {env.secret_number:<6}  |  Candidates: 1000{RESET}")
        print(f"{CYAN}" + "-" * 55 + RESET)

    done = False
    info = {}
    while not done:
        step_num = env.questions_asked + 1
        action   = agent.select_action(state, forbidden=env.get_forbidden_actions())
        q        = env.question_space.decode_action(action)
        preview  = env.answer_question(q)
        q_desc   = env.question_space.describe(action)

        state, reward, done, info = env.step(action)

        if verbose:
            cands_left = len(env.remaining_candidates)
            print(f"  {YELLOW}Q{step_num}{RESET}: {q_desc}")
            print(f"       Answer: {preview!r:<18}  {cands_left} candidates remain")

    guess   = info["guess"]
    secret_ = info["secret"]
    win     = guess == secret_

    if verbose:
        colour = GREEN if win else RED
        tag    = "[WIN]" if win else "[MISS]"
        print(f"\n  Guess: {guess}   Secret: {secret_}   {colour}{tag}{RESET}")
        print(f"  Reward: {reward:.1f}")
        remaining    = env.remaining_candidates
        preview_list = str(remaining[:12]) + ("..." if len(remaining) > 12 else "")
        print(f"  Remaining candidates ({len(remaining)}): {preview_list}")

    return win, reward


def quick_bench(env, agent, n):
    wins    = 0
    total_r = 0.0

    for i in range(n):
        w, r     = play_one_game(env, agent, verbose=False)
        wins    += int(w)
        total_r += r
        if (i + 1) % 50 == 0:
            print(f"  ... {i+1}/{n}", end="\r", flush=True)

    print(f"\n{CYAN}" + "-" * 55 + RESET)
    print(f"  Games: {n}   Wins: {wins}   Success: {wins/n:.1%}")
    print(f"  Avg reward: {total_r/n:.2f}")
    print(f"{CYAN}" + "-" * 55 + RESET)


def list_all_questions(env):
    qs = env.question_space
    print(f"\n{CYAN}All {qs.size()} questions in the vocabulary:{RESET}\n")
    current_type = None
    for i in range(qs.size()):
        q     = qs.decode_action(i)
        qtype = q["type"]
        if qtype != current_type:
            print(f"\n  {YELLOW}== {qtype.upper()} =={RESET}")
            current_type = qtype
        print(f"  [{i:02d}] {qs.describe(i)}")


def main():
    parser = argparse.ArgumentParser(
        description="Test the trained number-guessing DQN agent",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--secret", type=int, default=None,
                        help="Fix the secret number (1-1000); agent will try to guess it")
    parser.add_argument("--games",  type=int, default=5,
                        help="Number of detailed games to play (default: 5)")
    parser.add_argument("--quick",  type=int, default=None,
                        help="Run N games silently and show win-rate summary")
    parser.add_argument("--list-questions", action="store_true",
                        help="Print all questions in the vocabulary and exit")
    args = parser.parse_args()

    env = NumberGuessingEnv(number_range=(1, 1000), max_questions=7)

    if args.list_questions:
        list_all_questions(env)
        return

    agent = load_agent(env)

    if args.quick is not None:
        print(f"Running {args.quick} games (no detail)...\n")
        quick_bench(env, agent, args.quick)
        return

    if args.secret is not None:
        if not (1 <= args.secret <= 1000):
            print("Error: --secret must be between 1 and 1000")
            sys.exit(1)
        play_one_game(env, agent, secret=args.secret)
        return

    wins = 0
    for i in range(args.games):
        print(f"\n{CYAN}[Game {i+1} / {args.games}]{RESET}")
        w, _ = play_one_game(env, agent)
        wins += int(w)

    print(f"\n{CYAN}" + "=" * 55 + RESET)
    print(f"  Result: {wins}/{args.games} won  ({wins/args.games:.0%})")
    print(f"{CYAN}" + "=" * 55 + RESET + "\n")


if __name__ == "__main__":
    main()
