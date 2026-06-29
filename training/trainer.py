import os
import numpy as np
import pandas as pd


class Trainer:
    def __init__(self, env, agent, episodes=100_000, start_episode=0):
        self.env              = env
        self.agent            = agent
        self.episodes         = episodes
        self.start_episode    = start_episode
        self.total_episodes   = start_episode + episodes
        self.target_update_freq = 500
        self.rewards_log        = []
        self.success_log        = []
        self.questions_used_log = []
        self.epsilon_log        = []

    def train(self):
        for episode in range(self.episodes):
            actual_ep = self.start_episode + episode
            state     = self.env.reset()
            done      = False
            total_r   = 0

            while not done:
                a = self.agent.select_action(state, forbidden=self.env.get_forbidden_actions())
                ns, r, done, info = self.env.step(a)
                self.agent.remember(state, a, r, ns, done)
                state    = ns
                total_r += r

            self.agent.replay()
            success = int(info["guess"] == info["secret"])

            self.rewards_log.append(total_r)
            self.success_log.append(success)
            self.questions_used_log.append(self.env.questions_asked)
            self.epsilon_log.append(self.agent.epsilon)

            if actual_ep % self.target_update_freq == 0:
                self.agent.update_target_network()

            freq = max(100, self.total_episodes // 20)
            if actual_ep % freq == 0:
                self._print_progress(actual_ep)

            if actual_ep % 10000 == 0 and actual_ep > 0:
                os.makedirs("checkpoints", exist_ok=True)
                self.agent.save(f"checkpoints/ep{actual_ep}.weights.h5")

    def _print_progress(self, actual_ep):
        last_s = self.success_log[-1000:]
        last_r = self.rewards_log[-1000:]
        print(
            f"Episode {actual_ep}/{self.total_episodes} | "
            f"Success: {np.mean(last_s) * 100:.1f}% | "
            f"Avg Reward: {np.mean(last_r):.1f} | "
            f"Epsilon: {self.agent.epsilon:.4f}"
        )

    def save_logs(self, path="training_log.csv"):
        new_df = pd.DataFrame({
            "episode":        range(self.start_episode, self.start_episode + len(self.rewards_log)),
            "reward":         self.rewards_log,
            "success":        self.success_log,
            "questions_used": self.questions_used_log,
            "epsilon":        self.epsilon_log,
        })
        if os.path.exists(path) and self.start_episode > 0:
            old_df = pd.read_csv(path)
            old_df = old_df[old_df["episode"] < self.start_episode]
            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined.to_csv(path, index=False)
        else:
            new_df.to_csv(path, index=False)
        print(f"Training logs saved to {path}")
