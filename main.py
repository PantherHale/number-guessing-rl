import os
from environment.game_env import NumberGuessingEnv
from agent.rl_agent import RLAgent
from training.trainer import Trainer
from evaluation.evaluator import Evaluator
from leaderboard import record_run, show_leaderboard

CHECKPOINT_DIR = "checkpoints_ddqn"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs("charts", exist_ok=True)


def main():
    # ── RESUME SETTINGS ───────────────────────────────────────────────────────
    # Set RESUME_CHECKPOINT to a .h5 path to continue a previous run.
    # Set to None to train from scratch.
    RESUME_CHECKPOINT   = None
    RESUME_FROM_EPISODE = 0
    TOTAL_EPISODES      = 200_000
    # ─────────────────────────────────────────────────────────────────────────

    env         = NumberGuessingEnv(number_range=(1, 1000), max_questions=6)
    state_size  = 26   # 5 base + 3 distribution stats + 10 histogram buckets + 8 type-usage
    action_size = env.question_space.size()
    print(f"Actions: {action_size} | States: {state_size}")

    start_ep        = 0
    initial_epsilon = 1.0

    if RESUME_CHECKPOINT and os.path.exists(RESUME_CHECKPOINT):
        start_ep        = RESUME_FROM_EPISODE
        initial_epsilon = 0.05
        remaining       = TOTAL_EPISODES - start_ep
        print(f"Resuming from {RESUME_CHECKPOINT} (ep{start_ep}) — {remaining} episodes left")
    else:
        start_ep  = 0
        remaining = TOTAL_EPISODES
        print(f"Training Double DQN from scratch — {TOTAL_EPISODES} episodes")
    print("-" * 60)

    agent = RLAgent(
        state_size=state_size,
        action_size=action_size,
        lr=0.0001,
        gamma=0.99,
        epsilon=initial_epsilon,
        epsilon_min=0.01,
        epsilon_decay=0.9998,
        memory_size=100_000,
        batch_size=64,
    )

    if RESUME_CHECKPOINT and os.path.exists(RESUME_CHECKPOINT):
        agent.load(RESUME_CHECKPOINT)
        print(f"Loaded weights from {RESUME_CHECKPOINT}")

    trainer = Trainer(env=env, agent=agent, episodes=remaining, start_episode=start_ep)
    trainer.train()
    trainer.save_logs("training_log.csv")

    print("\n" + "=" * 60 + "\nTRAINING DONE — EVALUATING\n" + "=" * 60)

    import pandas as pd
    full_log = pd.read_csv("training_log.csv")
    full_logs = {
        "success_log": full_log["success"].tolist(),
        "rewards_log": full_log["reward"].tolist(),
    }

    evaluator = Evaluator(env=env, agent=agent)
    evaluator.run_evaluation(num_games=1000)
    evaluator.compare_with_baselines()
    evaluator.analyze_question_strategy()
    evaluator.plot_results(
        trainer_logs=full_logs,
        start_episode=0,
    )
    evaluator.save_results("eval_results.csv")

    record_run(evaluator, run_name=f"run_{TOTAL_EPISODES}ep", episodes=TOTAL_EPISODES)
    show_leaderboard()

    print("Outputs: charts/ | training_log.csv | eval_results.csv | leaderboard.csv")


if __name__ == "__main__":
    main()

#    cd c:\Users\gaura\Documents\researchmodel1\number_guessing_rl
#   py -3.11 main.py
