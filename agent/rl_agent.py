import random
import numpy as np
from collections import deque
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.optimizers import Adam

tf.get_logger().setLevel("ERROR")


class RLAgent:
    def __init__(
        self,
        state_size,
        action_size,
        lr=0.001,
        gamma=0.99,
        epsilon=1.0,
        epsilon_min=0.01,
        epsilon_decay=0.9995,
        memory_size=50000,
        batch_size=64,
    ):
        self.state_size    = state_size
        self.action_size   = action_size
        self.lr            = lr
        self.gamma         = gamma
        self.epsilon       = epsilon
        self.epsilon_min   = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.batch_size    = batch_size
        self.memory        = deque(maxlen=memory_size)
        self.model         = self._build_model()
        self.target_model  = self._build_model()
        self.update_target_network()

    def _build_model(self):
        model = Sequential([
            Input(shape=(self.state_size,)),
            Dense(256, activation="relu"),
            Dense(256, activation="relu"),
            Dense(128, activation="relu"),
            Dense(self.action_size, activation="linear"),
        ])
        model.compile(optimizer=Adam(learning_rate=self.lr, clipnorm=1.0), loss="mse")
        return model

    def select_action(self, state, forbidden=None):
        forbidden = forbidden or set()
        available = [i for i in range(self.action_size) if i not in forbidden]
        if not available:
            available = list(range(self.action_size))

        if random.random() < self.epsilon:
            return random.choice(available)

        q_values = self.model(state.reshape(1, -1), training=False).numpy()[0]
        for i in forbidden:
            q_values[i] = -np.inf
        return int(np.argmax(q_values))

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return

        batch       = random.sample(self.memory, self.batch_size)
        states      = np.array([e[0] for e in batch])
        next_states = np.array([e[3] for e in batch])
        cur_q       = self.model(states, training=False).numpy()
        next_q      = self.target_model(next_states, training=False).numpy()

        for i, (s, a, r, s2, done) in enumerate(batch):
            # Bellman: Q(s,a) = r + gamma * max Q(s')
            cur_q[i][a] = r if done else r + self.gamma * float(np.max(next_q[i]))

        self.model.train_on_batch(states, cur_q)
        self.decay_epsilon()

    def update_target_network(self):
        self.target_model.set_weights(self.model.get_weights())

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, path):
        self.model.save_weights(path)

    def load(self, path):
        self.model.load_weights(path)
        self.update_target_network()
