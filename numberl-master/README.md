# Numberl

Numberl is a daily number-guessing puzzle inspired by Wordle and built from the
question vocabulary in
[PantherHale/number-guessing-rl](https://github.com/PantherHale/number-guessing-rl).

The goal is simple: find the secret number from 1 to 1000. Instead of typing
freeform questions, players choose from the same structured math questions used
by the reinforcement-learning project, then submit a final guess.

## Why this exists

The original project trains an RL agent to ask useful questions and guess a
number. Numberl turns that idea into a human-playable web game so people can try
the same challenge and compare themselves against the AI benchmark.

## Gameplay

- The secret number is between 1 and 1000.
- You get up to 7 questions.
- You can ask each question only once.
- You can ask at most 2 questions from the same type.
- After asking questions, submit one final guess.
- Daily mode uses a stable number for the day.
- Practice mode starts a random round.

## Question types

- Range: `Is the number between 1 and 500?`
- Proximity: `Is the number closer to 250 or 750?`
- Parity: `Is the number even or odd?`
- Modular: `What is the number modulo 2/3/4/5?`
- Digit Sum: `Is the digit sum greater than 10?`
- Special: prime, perfect square, Fibonacci, palindrome, and related properties
- Digit Compare: compares hundreds, tens, and units digits
- Divisible: checks divisibility by 6, 7, 9, 11, or 25

Modulo 10 and modulo 1000 are intentionally not included because they reveal too
much direct information.

## Candidate Grid

The grid shows which numbers are still possible.

- Filled cell: still a possible candidate.
- Blank cell: eliminated.
- The board is always square.
- The board ends at the next biggest square number after the current maximum
  candidate. For example, if the current max is 125, the board becomes 12 by 12
  and ends at 144.
- Number labels appear only when cells are large enough to read cleanly.

Examples:

- After a `1-100` range answer, the grid becomes a 10 by 10 board showing
  numbers 1 through 100.
- After a modulo answer, the grid keeps the matching remainder pattern and blanks
  the eliminated cells.

## Run Locally

```bash
npm install
npm run dev
```

Then open the local URL printed by Vite.

## Build

```bash
npm run build
```

## Deploy on Vercel

This repo is a Vite app and includes `vercel.json`.

- Build command: `npm run build`
- Output directory: `dist`
- Framework: Vite

## Tech

- React
- Vite
- Plain CSS

## Attribution

The game rules and question set are based on the
[Number Guessing RL Agent](https://github.com/PantherHale/number-guessing-rl)
project by PantherHale.
