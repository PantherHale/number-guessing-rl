import os
from environment.game_env import NumberGuessingEnv
from agent.rl_agent import RLAgent
from training.trainer import Trainer
from evaluation.evaluator import Evaluator
from leaderboard import record_run, show_leaderboard

os.makedirs("checkpoints", exist_ok=True)
os.makedirs("charts", exist_ok=True)


def main():
    #  RESUME SETTINGS -
    # Set RESUME_CHECKPOINT to a .h5 path to continue a previous run.
    # Set to None to train from scratch.
    RESUME_CHECKPOINT   = "checkpoints/ep90000.weights.h5"
    RESUME_FROM_EPISODE = 90000
    TOTAL_EPISODES      = 230_000
    # ─

    env         = NumberGuessingEnv(number_range=(1, 1000), max_questions=7)
    state_size  = 13
    action_size = env.question_space.size()
    print(f"Actions: {action_size} | States: {state_size}")

    start_ep        = 0
    initial_epsilon = 1.0

    if RESUME_CHECKPOINT and os.path.exists(RESUME_CHECKPOINT):
        start_ep        = RESUME_FROM_EPISODE
        initial_epsilon = 0.01
        remaining       = TOTAL_EPISODES - start_ep
        print(f"Resuming from {RESUME_CHECKPOINT} (ep{start_ep}) — {remaining} episodes left")
    else:
        remaining = TOTAL_EPISODES
        print(f"Training from scratch — {TOTAL_EPISODES} episodes")
    print("-" * 60)

    agent = RLAgent(
        state_size=state_size,
        action_size=action_size,
        lr=0.0001,
        gamma=0.99,
        epsilon=initial_epsilon,
        epsilon_min=0.01,
        epsilon_decay=0.9995,
        memory_size=100_000,
        batch_size=64,
    )

    if RESUME_CHECKPOINT and os.path.exists(RESUME_CHECKPOINT):
        agent.load(RESUME_CHECKPOINT)

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
