export const TYPE_ORDER = [
  "range",
  "proximity",
  "parity",
  "modular",
  "digit_sum",
  "special",
  "digit_compare",
  "divisible",
];

export const TYPE_META = {
  range: {
    label: "Range",
    shortLabel: "Range",
    answer: "yes/no",
    accent: "#2563eb",
  },
  proximity: {
    label: "Proximity",
    shortLabel: "Near",
    answer: "closer/equal",
    accent: "#7c3aed",
  },
  parity: {
    label: "Parity",
    shortLabel: "Parity",
    answer: "even/odd",
    accent: "#0891b2",
  },
  modular: {
    label: "Modular",
    shortLabel: "Mod",
    answer: "remainder",
    accent: "#f59e0b",
  },
  digit_sum: {
    label: "Digit Sum",
    shortLabel: "Sum",
    answer: "yes/no",
    accent: "#0f9f6e",
  },
  special: {
    label: "Special",
    shortLabel: "Special",
    answer: "yes/no",
    accent: "#ef5b5b",
  },
  digit_compare: {
    label: "Digit Compare",
    shortLabel: "Digits",
    answer: "yes/no",
    accent: "#4f46e5",
  },
  divisible: {
    label: "Divisible",
    shortLabel: "Div",
    answer: "yes/no",
    accent: "#0d9488",
  },
};

const rangePairs = [
  [1, 100],
  [1, 200],
  [1, 300],
  [1, 400],
  [1, 500],
  [1, 600],
  [1, 700],
  [1, 800],
  [1, 900],
  [101, 200],
  [201, 300],
  [301, 400],
  [401, 500],
  [501, 600],
  [601, 700],
  [701, 800],
  [801, 900],
  [901, 1000],
  [1, 500],
  [251, 750],
  [1, 333],
  [334, 666],
  [667, 1000],
  [1, 250],
  [251, 500],
  [501, 750],
  [751, 1000],
  [201, 400],
  [401, 600],
  [601, 800],
  [801, 1000],
  [1, 125],
  [126, 250],
  [251, 375],
  [376, 500],
  [501, 625],
  [626, 750],
  [751, 875],
  [876, 1000],
  [300, 700],
  [350, 650],
  [400, 600],
  [1, 750],
  [251, 1000],
];

const proximityPairs = [
  [250, 750],
  [100, 900],
  [200, 800],
  [300, 700],
  [400, 600],
  [150, 850],
  [333, 666],
  [50, 950],
  [450, 550],
  [100, 500],
  [125, 875],
  [375, 625],
];

const specialProperties = [
  ["perfect_square", "Is the number a perfect square?"],
  ["prime", "Is the number prime?"],
  ["palindrome", "Is the number a palindrome?"],
  ["fibonacci", "Is the number a Fibonacci number?"],
  ["repeated_digit", "Does the number have a repeated digit?"],
  ["power_of_2", "Is the number a power of 2?"],
  ["triangular", "Is the number a triangular number?"],
  ["digit_sum_prime", "Is the digit sum itself a prime number?"],
];

let nextId = 0;
const questions = [];

for (const [low, high] of rangePairs) {
  questions.push({
    id: nextId++,
    type: "range",
    low,
    high,
    text: `Is the number between ${low} and ${high}?`,
  });
}

for (const [a, b] of proximityPairs) {
  questions.push({
    id: nextId++,
    type: "proximity",
    a,
    b,
    text: `Is the number closer to ${a} or ${b}?`,
  });
}

questions.push({
  id: nextId++,
  type: "parity",
  text: "Is the number even or odd?",
});

for (const divisor of [2, 3, 4, 5]) {
  questions.push({
    id: nextId++,
    type: "modular",
    divisor,
    text: `What is the number modulo ${divisor}?`,
  });
}

for (const threshold of [5, 10, 15, 20, 25]) {
  questions.push({
    id: nextId++,
    type: "digit_sum",
    threshold,
    text: `Is the digit sum greater than ${threshold}?`,
  });
}

for (const [property, text] of specialProperties) {
  questions.push({
    id: nextId++,
    type: "special",
    property,
    text,
  });
}

for (const [pos1, pos2] of [
  ["hundreds", "units"],
  ["tens", "hundreds"],
  ["units", "tens"],
]) {
  questions.push({
    id: nextId++,
    type: "digit_compare",
    pos1,
    pos2,
    text: `Is the ${pos1} digit greater than the ${pos2} digit?`,
  });
}

for (const divisor of [6, 7, 9, 11, 25]) {
  questions.push({
    id: nextId++,
    type: "divisible",
    divisor,
    text: `Is the number divisible by ${divisor}?`,
  });
}

export const QUESTIONS = questions;
