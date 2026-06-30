export const NUMBER_MIN = 1;
export const NUMBER_MAX = 1000;
export const MAX_QUESTIONS = 7;
export const MAX_TYPE_QUESTIONS = 2;
export const AI_BENCHMARK = 42.8;

export function makeCandidates() {
  return Array.from(
    { length: NUMBER_MAX - NUMBER_MIN + 1 },
    (_, index) => NUMBER_MIN + index
  );
}

export function randomSecret() {
  const cryptoObj = globalThis.crypto;
  if (cryptoObj?.getRandomValues) {
    const buffer = new Uint32Array(1);
    cryptoObj.getRandomValues(buffer);
    return NUMBER_MIN + (buffer[0] % NUMBER_MAX);
  }

  return NUMBER_MIN + Math.floor(Math.random() * NUMBER_MAX);
}

export function getDailyChallenge(date = new Date()) {
  const key = date.toISOString().slice(0, 10);
  let hash = 2166136261;

  for (const char of `number-guessing-rl:${key}`) {
    hash ^= char.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }

  return {
    key,
    secret: NUMBER_MIN + (Math.abs(hash) % NUMBER_MAX),
  };
}

export function digitSum(n) {
  return String(n)
    .split("")
    .reduce((sum, digit) => sum + Number(digit), 0);
}

export function getDigit(n, pos) {
  if (pos === "hundreds") return Math.floor(n / 100) % 10;
  if (pos === "tens") return Math.floor(n / 10) % 10;
  return n % 10;
}

function makePrimeSet(limit) {
  const flags = Array(limit + 1).fill(true);
  flags[0] = false;
  flags[1] = false;

  for (let i = 2; i <= Math.floor(Math.sqrt(limit)); i += 1) {
    if (flags[i]) {
      for (let j = i * i; j <= limit; j += i) flags[j] = false;
    }
  }

  return new Set(flags.map((isPrime, n) => (isPrime ? n : null)).filter(Boolean));
}

function makeFibonacciSet(limit) {
  const values = new Set();
  let a = 1;
  let b = 1;

  while (a <= limit) {
    values.add(a);
    [a, b] = [b, a + b];
  }

  return values;
}

function makeTriangularSet(limit) {
  const values = new Set();
  let k = 1;
  let next = 1;

  while (next <= limit) {
    values.add(next);
    k += 1;
    next = (k * (k + 1)) / 2;
  }

  return values;
}

const PRIME_SET = makePrimeSet(NUMBER_MAX);
const FIBONACCI_SET = makeFibonacciSet(NUMBER_MAX);
const POWER_OF_2_SET = new Set(
  Array.from({ length: 10 }, (_, index) => 2 ** index).filter(
    (n) => n <= NUMBER_MAX
  )
);
const TRIANGULAR_SET = makeTriangularSet(NUMBER_MAX);
const SMALL_PRIMES = new Set([2, 3, 5, 7, 11, 13, 17, 19, 23]);

export function matchesSpecialProperty(n, property) {
  if (property === "perfect_square") {
    const root = Math.floor(Math.sqrt(n));
    return root * root === n;
  }
  if (property === "prime") return PRIME_SET.has(n);
  if (property === "palindrome") {
    const value = String(n);
    return value === value.split("").reverse().join("");
  }
  if (property === "fibonacci") return FIBONACCI_SET.has(n);
  if (property === "repeated_digit") {
    const value = String(n);
    return new Set(value).size !== value.length;
  }
  if (property === "power_of_2") return POWER_OF_2_SET.has(n);
  if (property === "triangular") return TRIANGULAR_SET.has(n);
  if (property === "digit_sum_prime") return SMALL_PRIMES.has(digitSum(n));
  return false;
}

export function answerQuestion(secret, question) {
  if (question.type === "range") {
    return question.low <= secret && secret <= question.high ? "yes" : "no";
  }

  if (question.type === "proximity") {
    const distA = Math.abs(secret - question.a);
    const distB = Math.abs(secret - question.b);
    if (distA < distB) return `closer to ${question.a}`;
    if (distB < distA) return `closer to ${question.b}`;
    return "equidistant";
  }

  if (question.type === "parity") return secret % 2 === 0 ? "even" : "odd";

  if (question.type === "modular") return String(secret % question.divisor);

  if (question.type === "digit_sum") {
    return digitSum(secret) > question.threshold ? "yes" : "no";
  }

  if (question.type === "special") {
    return matchesSpecialProperty(secret, question.property) ? "yes" : "no";
  }

  if (question.type === "digit_compare") {
    return getDigit(secret, question.pos1) > getDigit(secret, question.pos2)
      ? "yes"
      : "no";
  }

  if (question.type === "divisible") {
    return secret % question.divisor === 0 ? "yes" : "no";
  }

  return "";
}

export function filterCandidates(candidates, question, answer) {
  let next = candidates;

  if (question.type === "range") {
    next =
      answer === "yes"
        ? candidates.filter((n) => question.low <= n && n <= question.high)
        : candidates.filter((n) => !(question.low <= n && n <= question.high));
  }

  if (question.type === "proximity") {
    next = candidates.filter((n) => {
      const distA = Math.abs(n - question.a);
      const distB = Math.abs(n - question.b);
      if (answer === "equidistant") return distA === distB;
      if (answer === `closer to ${question.a}`) return distA < distB;
      return distB < distA;
    });
  }

  if (question.type === "parity") {
    next = candidates.filter((n) =>
      answer === "even" ? n % 2 === 0 : n % 2 !== 0
    );
  }

  if (question.type === "modular") {
    const remainder = Number(answer);
    next = candidates.filter((n) => n % question.divisor === remainder);
  }

  if (question.type === "digit_sum") {
    next = candidates.filter((n) =>
      answer === "yes"
        ? digitSum(n) > question.threshold
        : digitSum(n) <= question.threshold
    );
  }

  if (question.type === "special") {
    next = candidates.filter((n) =>
      answer === "yes"
        ? matchesSpecialProperty(n, question.property)
        : !matchesSpecialProperty(n, question.property)
    );
  }

  if (question.type === "digit_compare") {
    next = candidates.filter((n) => {
      const matches =
        getDigit(n, question.pos1) > getDigit(n, question.pos2);
      return answer === "yes" ? matches : !matches;
    });
  }

  if (question.type === "divisible") {
    next = candidates.filter((n) =>
      answer === "yes" ? n % question.divisor === 0 : n % question.divisor !== 0
    );
  }

  return next.length > 0 ? next : candidates;
}

export function summarizeCandidates(candidates) {
  return {
    count: candidates.length,
    min: Math.min(...candidates),
    max: Math.max(...candidates),
  };
}
