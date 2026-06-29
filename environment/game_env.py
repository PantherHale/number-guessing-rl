import random
import numpy as np
from environment.question_space import QuestionSpace


def _sieve(n):
    flags = [True] * (n + 1)
    flags[0] = flags[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            for j in range(i * i, n + 1, i):
                flags[j] = False
    return {i for i in range(2, n + 1) if flags[i]}

_PRIME_SET = _sieve(1000)


def _fib_set(n):
    fibs, a, b = set(), 1, 1
    while a <= n:
        fibs.add(a)
        a, b = b, a + b
    return fibs

_FIBONACCI_SET  = _fib_set(1000)
_POWER_OF_2_SET = {2 ** i for i in range(10) if 2 ** i <= 1000}


def _tri_set(n):
    tris, k = set(), 1
    while (t := k * (k + 1) // 2) <= n:
        tris.add(t)
        k += 1
    return tris

_TRIANGULAR_SET = _tri_set(1000)
_SMALL_PRIMES   = {2, 3, 5, 7, 11, 13, 17, 19, 23}


def _digit_sum(n):
    return sum(int(d) for d in str(n))


def _get_digit(n, pos):
    if pos == "hundreds":
        return (n // 100) % 10
    elif pos == "tens":
        return (n // 10) % 10
    else:
        return n % 10


class NumberGuessingEnv:
    # Fixed order so type-usage state features are always at the same index
    _TYPE_ORDER = [
        "range", "proximity", "parity", "modular",
        "digit_sum", "special", "digit_compare", "divisible",
    ]

    def __init__(self, number_range=(1, 1000), max_questions=5):
        self.number_range         = number_range
        self.max_questions        = max_questions
        self.question_space       = QuestionSpace(number_range)
        self.secret_number        = None
        self.questions_asked      = 0
        self.remaining_candidates = []
        self.question_history     = []
        self.asked_action_set     = set()
        self.asked_type_counts    = {}

    def reset(self):
        low, high = self.number_range
        self.secret_number        = random.randint(low, high)
        self.remaining_candidates = list(range(low, high + 1))
        self.questions_asked      = 0
        self.question_history     = []
        self.asked_action_set     = set()
        self.asked_type_counts    = {}
        return self.get_state()

    def get_forbidden_actions(self):
        forbidden = set()
        for i, q in enumerate(self.question_space.all_questions):
            if i in self.asked_action_set:
                forbidden.add(i)
            elif self.asked_type_counts.get(q["type"], 0) >= 2:
                forbidden.add(i)
        return forbidden

    def step(self, action):
        self.asked_action_set.add(action)
        qtype = self.question_space.decode_action(action)["type"]
        self.asked_type_counts[qtype] = self.asked_type_counts.get(qtype, 0) + 1

        q   = self.question_space.decode_action(action)
        ans = self.answer_question(q)
        self.update_candidates(q, ans)
        self.question_history.append((q, ans))
        self.questions_asked += 1
        done = self.questions_asked >= self.max_questions

        info = {"secret": self.secret_number, "guess": None}

        if done:
            mid           = len(self.remaining_candidates) // 2
            guess         = self.remaining_candidates[mid]
            reward        = self.calculate_reward(guess)
            info["guess"] = guess
        else:
            reward = -1

        return self.get_state(), reward, done, info

    def answer_question(self, q):
        secret = self.secret_number
        qtype  = q["type"]

        if qtype == "range":
            return "yes" if q["low"] <= secret <= q["high"] else "no"

        elif qtype == "proximity":
            dist_a = abs(secret - q["a"])
            dist_b = abs(secret - q["b"])
            if dist_a < dist_b:
                return f"closer to {q['a']}"
            elif dist_b < dist_a:
                return f"closer to {q['b']}"
            else:
                return "equidistant"

        elif qtype == "parity":
            return "even" if secret % 2 == 0 else "odd"

        elif qtype == "modular":
            return str(secret % q["divisor"])

        elif qtype == "digit_sum":
            return "yes" if _digit_sum(secret) > q["threshold"] else "no"

        elif qtype == "special":
            prop = q["property"]
            if prop == "perfect_square":
                r = int(secret ** 0.5)
                return "yes" if r * r == secret else "no"
            elif prop == "prime":
                return "yes" if secret in _PRIME_SET else "no"
            elif prop == "palindrome":
                s = str(secret)
                return "yes" if s == s[::-1] else "no"
            elif prop == "fibonacci":
                return "yes" if secret in _FIBONACCI_SET else "no"
            elif prop == "repeated_digit":
                s = str(secret)
                return "yes" if len(s) != len(set(s)) else "no"
            elif prop == "power_of_2":
                return "yes" if secret in _POWER_OF_2_SET else "no"
            elif prop == "triangular":
                return "yes" if secret in _TRIANGULAR_SET else "no"
            elif prop == "digit_sum_prime":
                return "yes" if _digit_sum(secret) in _SMALL_PRIMES else "no"

        elif qtype == "digit_compare":
            d1 = _get_digit(secret, q["pos1"])
            d2 = _get_digit(secret, q["pos2"])
            return "yes" if d1 > d2 else "no"

        elif qtype == "divisible":
            return "yes" if secret % q["divisor"] == 0 else "no"

        return ""

    def update_candidates(self, q, ans):
        prev  = self.remaining_candidates[:]
        qtype = q["type"]

        if qtype == "range":
            if ans == "yes":
                new_cands = [n for n in prev if q["low"] <= n <= q["high"]]
            else:
                new_cands = [n for n in prev if not (q["low"] <= n <= q["high"])]

        elif qtype == "proximity":
            if ans == "equidistant":
                new_cands = [n for n in prev if abs(n - q["a"]) == abs(n - q["b"])]
            elif ans == f"closer to {q['a']}":
                new_cands = [n for n in prev if abs(n - q["a"]) < abs(n - q["b"])]
            else:
                new_cands = [n for n in prev if abs(n - q["b"]) < abs(n - q["a"])]

        elif qtype == "parity":
            if ans == "even":
                new_cands = [n for n in prev if n % 2 == 0]
            else:
                new_cands = [n for n in prev if n % 2 != 0]

        elif qtype == "modular":
            rem       = int(ans)
            new_cands = [n for n in prev if n % q["divisor"] == rem]

        elif qtype == "digit_sum":
            t = q["threshold"]
            if ans == "yes":
                new_cands = [n for n in prev if _digit_sum(n) > t]
            else:
                new_cands = [n for n in prev if _digit_sum(n) <= t]

        elif qtype == "special":
            prop = q["property"]
            if prop == "perfect_square":
                matches = lambda n: int(n ** 0.5) ** 2 == n
            elif prop == "prime":
                matches = lambda n: n in _PRIME_SET
            elif prop == "palindrome":
                matches = lambda n: str(n) == str(n)[::-1]
            elif prop == "fibonacci":
                matches = lambda n: n in _FIBONACCI_SET
            elif prop == "repeated_digit":
                matches = lambda n: len(str(n)) != len(set(str(n)))
            elif prop == "power_of_2":
                matches = lambda n: n in _POWER_OF_2_SET
            elif prop == "triangular":
                matches = lambda n: n in _TRIANGULAR_SET
            elif prop == "digit_sum_prime":
                matches = lambda n: _digit_sum(n) in _SMALL_PRIMES
            else:
                matches = lambda n: False
            if ans == "yes":
                new_cands = [n for n in prev if matches(n)]
            else:
                new_cands = [n for n in prev if not matches(n)]

        elif qtype == "digit_compare":
            if ans == "yes":
                new_cands = [n for n in prev
                             if _get_digit(n, q["pos1"]) > _get_digit(n, q["pos2"])]
            else:
                new_cands = [n for n in prev
                             if not (_get_digit(n, q["pos1"]) > _get_digit(n, q["pos2"]))]

        elif qtype == "divisible":
            if ans == "yes":
                new_cands = [n for n in prev if n % q["divisor"] == 0]
            else:
                new_cands = [n for n in prev if n % q["divisor"] != 0]

        else:
            new_cands = prev

        # guard: if filter empties the list keep previous candidates
        self.remaining_candidates = new_cands if new_cands else prev

    def get_state(self):
        # 5 game-progress features + 8 per-type usage counts (normalized 0/0.5/1.0)
        cands = self.remaining_candidates
        base = np.array([
            len(cands) / 1000,
            min(cands) / 1000,
            max(cands) / 1000,
            self.questions_asked / self.max_questions,
            (self.max_questions - self.questions_asked) / self.max_questions,
        ], dtype=np.float32)
        type_counts = np.array([
            self.asked_type_counts.get(t, 0) / 2.0
            for t in self._TYPE_ORDER
        ], dtype=np.float32)
        return np.concatenate([base, type_counts])

    def calculate_reward(self, guess):
        if guess == self.secret_number:
            return 100 - (self.questions_asked * 2)
        proximity_bonus = max(0, 50 - abs(guess - self.secret_number) * 0.1)
        return -50 + proximity_bonus

    def render(self):
        last_qa = self.question_history[-1] if self.question_history else ("—", "—")
        print(
            f"Secret: {self.secret_number} | "
            f"Asked: {self.questions_asked} | "
            f"Candidates: {len(self.remaining_candidates)} | "
            f"Last: {last_qa}"
        )
