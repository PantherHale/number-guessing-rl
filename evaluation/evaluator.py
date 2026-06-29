import os
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class Evaluator:
    def __init__(self, env, agent):
        self.env              = env
        self.agent            = agent
        self.eval_results     = []
        self.baseline_results = {}

    def run_evaluation(self, num_games=1000):
        self.agent.epsilon = 0.0
        self.eval_results  = []
        wins           = 0
        total_questions = 0

        for _ in range(num_games):
            state = self.env.reset()
            done  = False
            episode_reward = 0

            while not done:
                action = self.agent.select_action(state, forbidden=self.env.get_forbidden_actions())
                state, r, done, info = self.env.step(action)
                episode_reward += r

            success = info["guess"] == info["secret"]
            if success:
                wins += 1
            total_questions += self.env.questions_asked

            q_types = [q["type"] for q, _ in self.env.question_history]
            self.eval_results.append({
                "success":        success,
                "questions_used": self.env.questions_asked,
                "question_types": q_types,
                "secret":         info["secret"],
                "guess":          info["guess"],
                "reward":         episode_reward,
            })

        success_rate = wins / num_games
        avg_q        = total_questions / num_games
        avg_r        = sum(g["reward"] for g in self.eval_results) / num_games
        self.baseline_results["agent"] = {
            "success_rate": success_rate,
            "avg_questions": avg_q,
            "avg_reward":    avg_r,
        }
        print(f"\n--- Evaluation Results ({num_games} games) ---")
        print(f"Won: {wins} | Success Rate: {success_rate:.1%} | Avg Reward: {avg_r:.1f}")

    def compare_with_baselines(self):
        bin_res        = self.binary_search_baseline(1000)
        rnd_res        = self.random_baseline(1000)
        human_baseline = {"success_rate": 0.05, "avg_questions": 6.9}

        self.baseline_results["binary_search"] = bin_res
        self.baseline_results["random"]        = rnd_res
        self.baseline_results["human"]         = human_baseline

        strategies = [
            ("Agent (DQN)",  self.baseline_results.get("agent", {})),
            ("Binary Search", bin_res),
            ("Random",        rnd_res),
            ("Human",         human_baseline),
        ]
        print("\n--- Strategy Comparison ---")
        print(f"{'Strategy':<20} {'Success Rate':>14} {'Avg Questions':>15}")
        print("-" * 51)
        for name, res in strategies:
            sr = res.get("success_rate", 0)
            aq = res.get("avg_questions", 0)
            print(f"{name:<20} {sr:>13.1%} {aq:>15.2f}")

    def binary_search_baseline(self, n):
        wins    = 0
        total_q = 0

        for _ in range(n):
            self.env.reset()
            done = False

            while not done:
                candidates   = self.env.remaining_candidates
                best_action  = 0
                best_balance = float("inf")

                for action in range(self.env.question_space.size()):
                    q = self.env.question_space.decode_action(action)
                    if q["type"] != "range":
                        continue
                    in_range = sum(1 for c in candidates if q["low"] <= c <= q["high"])
                    balance  = abs(in_range - len(candidates) / 2)
                    if balance < best_balance:
                        best_balance = balance
                        best_action  = action

                _, _, done, info = self.env.step(best_action)

            if info["guess"] == info["secret"]:
                wins += 1
            total_q += self.env.questions_asked

        return {"success_rate": wins / n, "avg_questions": total_q / n}

    def random_baseline(self, n):
        wins    = 0
        total_q = 0

        for _ in range(n):
            self.env.reset()
            done = False

            while not done:
                action = random.randint(0, self.env.question_space.size() - 1)
                _, _, done, info = self.env.step(action)

            if info["guess"] == info["secret"]:
                wins += 1
            total_q += self.env.questions_asked

        return {"success_rate": wins / n, "avg_questions": total_q / n}

    def analyze_question_strategy(self):
        max_steps = self.env.max_questions
        strategy  = {step: {} for step in range(1, max_steps + 1)}

        for game in self.eval_results:
            for step_idx, qtype in enumerate(game["question_types"], 1):
                strategy[step_idx][qtype] = strategy[step_idx].get(qtype, 0) + 1

        print("\n--- Question Strategy Per Step ---")
        for step, counts in strategy.items():
            if not counts:
                continue
            total       = sum(counts.values())
            most_common = max(counts, key=counts.get)
            freq        = counts[most_common] / total * 100
            print(f"Step {step}: {most_common} ({freq:.1f}%)")

        return strategy

    def _compute_strategy(self):
        max_steps = self.env.max_questions
        strategy  = {step: {} for step in range(1, max_steps + 1)}
        for game in self.eval_results:
            for step_idx, qtype in enumerate(game["question_types"], 1):
                strategy[step_idx][qtype] = strategy[step_idx].get(qtype, 0) + 1
        return strategy

    def plot_results(self, trainer_logs=None, start_episode=0):
        os.makedirs("charts", exist_ok=True)

        # 1. Learning curve
        if trainer_logs and "success_log" in trainer_logs:
            success_log = trainer_logs["success_log"]
            window      = 1000
            rolling     = [
                np.mean(success_log[max(0, i - window + 1):i + 1])
                for i in range(len(success_log))
            ]
            x_vals = list(range(start_episode, start_episode + len(success_log)))
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(x_vals, rolling, color="steelblue", linewidth=0.8)
            ax.set_xlabel("Episode")
            ax.set_ylabel("Success Rate (rolling 1000)")
            ax.set_title(f"Learning Curve  (episodes {start_episode}–{x_vals[-1]})")
            ax.set_ylim(0, 1)
            plt.tight_layout()
            plt.savefig("charts/learning_curve.png", dpi=150)
            plt.close()

        # 2. Reward curve
        if trainer_logs and "rewards_log" in trainer_logs:
            rewards_log = trainer_logs["rewards_log"]
            window      = 1000
            rolling_r   = [
                np.mean(rewards_log[max(0, i - window + 1):i + 1])
                for i in range(len(rewards_log))
            ]
            x_vals = list(range(start_episode, start_episode + len(rewards_log)))
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(x_vals, rolling_r, color="darkorange", linewidth=0.8)
            ax.set_xlabel("Episode")
            ax.set_ylabel("Avg Reward (rolling 1000)")
            ax.set_title(f"Reward Curve  (episodes {start_episode}–{x_vals[-1]})")
            plt.tight_layout()
            plt.savefig("charts/reward_curve.png", dpi=150)
            plt.close()

        # 3. Strategy comparison
        labels, values = [], []
        order = [("Agent", "agent"), ("Binary Search", "binary_search"),
                 ("Random", "random"), ("Human", "human")]
        for name, key in order:
            if key in self.baseline_results:
                labels.append(name)
                values.append(self.baseline_results[key]["success_rate"] * 100)
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(labels, values,
                      color=["steelblue", "seagreen", "darkorange", "crimson"])
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                    f"{val:.1f}%", ha="center", va="bottom", fontsize=11)
        ax.set_ylabel("Success Rate (%)")
        ax.set_title(f"Strategy Comparison  ({self.env.max_questions} questions, 1–1000)")
        ax.set_ylim(0, 100)
        plt.tight_layout()
        plt.savefig("charts/strategy_comparison.png", dpi=150)
        plt.close()

        # 4. Question heatmap
        if self.eval_results:
            all_types = [
                "range", "proximity", "parity", "modular",
                "digit_sum", "special", "digit_compare", "divisible",
            ]
            steps        = list(range(1, self.env.max_questions + 1))
            strategy     = self._compute_strategy()
            heatmap_data = np.zeros((len(all_types), len(steps)))
            for j, step in enumerate(steps):
                for i, qtype in enumerate(all_types):
                    heatmap_data[i][j] = strategy[step].get(qtype, 0)
            col_labels = [f"Step {s}" for s in steps]
            df_heat    = pd.DataFrame(heatmap_data, index=all_types, columns=col_labels)
            fig, ax    = plt.subplots(figsize=(12, 6))
            sns.heatmap(df_heat, annot=True, fmt=".0f",
                        cmap="YlOrRd", ax=ax, linewidths=0.5)
            ax.set_title("Question Type Usage by Step  (out of 1000 eval games)")
            ax.set_xlabel("Step Position")
            ax.set_ylabel("Question Type")
            plt.tight_layout()
            plt.savefig("charts/question_heatmap.png", dpi=150)
            plt.close()

        # 5. Questions used distribution
        if self.eval_results:
            q_counts        = [g["questions_used"] for g in self.eval_results]
            unique, counts  = np.unique(q_counts, return_counts=True)
            fig, ax         = plt.subplots(figsize=(8, 5))
            bars            = ax.bar([str(u) for u in unique], counts, color="steelblue")
            for bar, cnt in zip(bars, counts):
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                        str(cnt), ha="center", va="bottom", fontsize=10)
            ax.set_xlabel("Questions Used")
            ax.set_ylabel("Game Count")
            ax.set_title("Questions Used Per Game")
            plt.tight_layout()
            plt.savefig("charts/questions_used_dist.png", dpi=150)
            plt.close()

        print("Charts saved to charts/")

    def save_results(self, path="eval_results.csv"):
        rows = []
        for game in self.eval_results:
            row = {
                "success":        game["success"],
                "questions_used": game["questions_used"],
                "secret":         game["secret"],
                "guess":          game["guess"],
            }
            for i, qtype in enumerate(game["question_types"], 1):
                row[f"step_{i}_type"] = qtype
            rows.append(row)
        pd.DataFrame(rows).to_csv(path, index=False)
        print(f"Eval results saved to {path}")
