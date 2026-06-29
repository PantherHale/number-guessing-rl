import pandas as pd   # DataFrame + CSV
import numpy as np    # mean computation


class Logger:
    """Logs per-episode stats."""

    def __init__(self, log_filepath="training_log.csv"):
        """Initialize empty log."""
        self.log_filepath = log_filepath  # output file path
        self.records = []                 # episode record list

    def record(self, episode, reward, success, questions_used, epsilon):
        """Store one episode's stats."""
        self.records.append({             # append dict to list
            "episode": episode,           # episode index
            "reward": reward,             # total episode reward
            "success": success,           # 1=win 0=lose
            "questions_used": questions_used,  # questions this game
            "epsilon": epsilon,           # exploration rate
        })

    def save_to_csv(self):
        """Write log records to CSV file."""
        pd.DataFrame(self.records).to_csv(self.log_filepath, index=False)  # write to file
        print(f"Log saved to {self.log_filepath}")  # confirm write

    def print_summary(self, last_n=1000):
        """Print mean success and reward for recent episodes."""
        recent = self.records[-last_n:]          # slice last N records
        if not recent:                           # nothing to report
            print("No records yet.")
            return
        mean_success = np.mean([r["success"] for r in recent])  # avg win rate
        mean_reward = np.mean([r["reward"] for r in recent])    # avg reward
        print(f"Last {last_n} — Success: {mean_success:.1%} | Reward: {mean_reward:.2f}")
