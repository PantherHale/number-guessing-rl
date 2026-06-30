import { useMemo, useState } from "react";
import {
  AI_BENCHMARK,
  MAX_QUESTIONS,
  MAX_TYPE_QUESTIONS,
  NUMBER_MAX,
  NUMBER_MIN,
  answerQuestion,
  filterCandidates,
  getDailyChallenge,
  makeCandidates,
  randomSecret,
  summarizeCandidates,
} from "./gameLogic";
import { QUESTIONS, TYPE_META, TYPE_ORDER } from "./questions";

const STATS_KEY = "number-guessing-rl-human-stats-v2";

function loadStats() {
  try {
    const raw = localStorage.getItem(STATS_KEY);
    if (!raw) return { games: 0, wins: 0, bestWinQuestions: null };
    return JSON.parse(raw);
  } catch {
    return { games: 0, wins: 0, bestWinQuestions: null };
  }
}

function saveStats(nextStats) {
  localStorage.setItem(STATS_KEY, JSON.stringify(nextStats));
}

function formatPercent(value) {
  if (!Number.isFinite(value)) return "0.0%";
  return `${value.toFixed(1)}%`;
}

function buildRunLog({ mode, dailyKey, secret, guess, result, history }) {
  return {
    app: "numberl",
    mode,
    dailyKey: mode === "daily" ? dailyKey : null,
    timestamp: new Date().toISOString(),
    secret,
    guess,
    won: result.won,
    questionsAsked: history.length,
    aiBenchmarkSuccessRatePct: AI_BENCHMARK,
    questions: history.map((entry, index) => ({
      step: index + 1,
      actionId: entry.question.id,
      type: entry.question.type,
      text: entry.question.text,
      answer: entry.answer,
      candidatesRemaining: entry.candidatesAfter,
    })),
  };
}

export default function App() {
  const daily = useMemo(() => getDailyChallenge(), []);
  const [mode, setMode] = useState("daily");
  const [practiceSecret, setPracticeSecret] = useState(() => randomSecret());
  const [history, setHistory] = useState([]);
  const [candidates, setCandidates] = useState(() => makeCandidates());
  const [guess, setGuess] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [activeType, setActiveType] = useState("range");
  const [stats, setStats] = useState(() => loadStats());
  const [copied, setCopied] = useState(false);

  const secret = mode === "daily" ? daily.secret : practiceSecret;
  const currentSlot = Math.min(history.length, MAX_QUESTIONS - 1);
  const canAsk = history.length < MAX_QUESTIONS && !result;

  const usedQuestionIds = useMemo(
    () => new Set(history.map((entry) => entry.question.id)),
    [history]
  );

  const typeCounts = useMemo(() => {
    const counts = Object.fromEntries(TYPE_ORDER.map((type) => [type, 0]));
    for (const entry of history) counts[entry.question.type] += 1;
    return counts;
  }, [history]);

  const candidateSummary = useMemo(
    () => summarizeCandidates(candidates),
    [candidates]
  );

  const activeQuestions = useMemo(
    () => QUESTIONS.filter((question) => question.type === activeType),
    [activeType]
  );

  function resetRound(nextMode = mode) {
    setHistory([]);
    setCandidates(makeCandidates());
    setGuess("");
    setResult(null);
    setError("");
    setCopied(false);
    if (nextMode === "practice") setPracticeSecret(randomSecret());
  }

  function switchMode(nextMode) {
    if (nextMode === mode) return;
    setMode(nextMode);
    resetRound(nextMode);
  }

  function disabledReason(question) {
    if (!canAsk) return "done";
    if (usedQuestionIds.has(question.id)) return "used";
    if (typeCounts[question.type] >= MAX_TYPE_QUESTIONS) return "type cap";
    return "";
  }

  function ask(question) {
    if (disabledReason(question)) return;

    const answer = answerQuestion(secret, question);
    const nextCandidates = filterCandidates(candidates, question, answer);

    setHistory((items) => [
      ...items,
      {
        question,
        answer,
        candidatesBefore: candidates.length,
        candidatesAfter: nextCandidates.length,
      },
    ]);
    setCandidates(nextCandidates);
    setError("");
  }

  function submitGuess(event) {
    event.preventDefault();
    if (result) return;

    const numericGuess = Number(guess);
    if (!Number.isInteger(numericGuess)) {
      setError("Enter a whole number.");
      return;
    }
    if (numericGuess < NUMBER_MIN || numericGuess > NUMBER_MAX) {
      setError(`Guess must be between ${NUMBER_MIN} and ${NUMBER_MAX}.`);
      return;
    }

    const won = numericGuess === secret;
    const nextResult = {
      won,
      guess: numericGuess,
      secret,
      offBy: Math.abs(numericGuess - secret),
    };
    setResult(nextResult);
    setError("");

    const nextStats = {
      games: stats.games + 1,
      wins: stats.wins + (won ? 1 : 0),
      bestWinQuestions: won
        ? Math.min(stats.bestWinQuestions ?? MAX_QUESTIONS, history.length)
        : stats.bestWinQuestions,
    };
    setStats(nextStats);
    saveStats(nextStats);
  }

  async function copyRun() {
    if (!result) return;
    const payload = buildRunLog({
      mode,
      dailyKey: daily.key,
      secret,
      guess: result.guess,
      result,
      history,
    });

    await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <main className="page">
      <section className="puzzle" aria-label="Numberl puzzle">
        <header className="header">
          <h1>Numberl</h1>
          <div className="modeSwitch" aria-label="Game mode">
            <button
              className={mode === "daily" ? "selected" : ""}
              type="button"
              onClick={() => switchMode("daily")}
            >
              Daily
            </button>
            <button
              className={mode === "practice" ? "selected" : ""}
              type="button"
              onClick={() => switchMode("practice")}
            >
              Practice
            </button>
          </div>
        </header>

        <div className="statusLine">
          <span>
            {history.length}/{MAX_QUESTIONS} questions · {candidateSummary.count} left
          </span>
        </div>

        <div className="playLayout">
          <CandidateGrid
            candidates={candidates}
            lastEntry={history[history.length - 1]}
            summary={candidateSummary}
          />

          <div className="questionColumn">
            <div className="rows" aria-label="Question history">
              {Array.from({ length: MAX_QUESTIONS }, (_, index) => {
                const entry = history[index];
                const isCurrent = canAsk && index === currentSlot;

                return (
                  <div
                    className={`slot ${entry ? "filled" : ""} ${isCurrent ? "active" : ""}`}
                    key={index}
                  >
                    <div className="slotRow">
                      <span className="slotNumber">{index + 1}</span>
                      <span className="slotQuestion">
                        {entry
                          ? entry.question.text
                          : isCurrent
                            ? "Choose a question"
                            : "choose question"}
                      </span>
                      <span
                        className={`answerChip ${entry?.answer === "no" ? "no" : ""}`}
                      >
                        {entry ? entry.answer : "-"}
                      </span>
                    </div>

                    {isCurrent && (
                      <QuestionPicker
                        activeType={activeType}
                        setActiveType={setActiveType}
                        activeQuestions={activeQuestions}
                        typeCounts={typeCounts}
                        disabledReason={disabledReason}
                        onAsk={ask}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            <form className="guessForm" onSubmit={submitGuess}>
              <input
                inputMode="numeric"
                value={guess}
                onChange={(event) => setGuess(event.target.value)}
                placeholder="Enter your final guess (1-1000)"
                aria-label="Final guess"
                disabled={Boolean(result)}
              />
              <button type="submit" disabled={Boolean(result) || !guess.trim()}>
                Submit
              </button>
            </form>

            {error && <p className="errorText">{error}</p>}

            {result && (
              <ResultPanel
                result={result}
                historyLength={history.length}
                copied={copied}
                copyRun={copyRun}
                reset={() => resetRound(mode)}
              />
            )}
          </div>
        </div>

        <footer className="footer">
          <span>AI {formatPercent(AI_BENCHMARK)} · no mod 10</span>
          <button type="button" onClick={() => resetRound(mode)}>
            new
          </button>
        </footer>
      </section>
    </main>
  );
}

function getCandidateGridModel(candidates, summary) {
  const candidateSet = new Set(candidates);
  const gridSide = Math.ceil(Math.sqrt(summary.max));
  const gridMax = gridSide * gridSide;
  const showLabels = gridSide <= 20;
  const cells = Array.from({ length: gridMax }, (_, index) => {
    const value = NUMBER_MIN + index;
    return {
      active: value <= NUMBER_MAX && candidateSet.has(value),
      inGameRange: value <= NUMBER_MAX,
      label: showLabels ? String(value) : "",
      value,
    };
  });

  return {
    activeMax: summary.max,
    activeMin: summary.min,
    cells,
    gridMax,
    gridSide,
    showLabels,
  };
}

function getBarBehavior(entry) {
  if (!entry) {
    return "Grid shows every remaining candidate across the current scale.";
  }

  const { question, answer } = entry;
  const answerText = `Answer: ${answer}.`;

  const behaviorByType = {
    range:
      answer === "yes"
        ? "Range zooms to the kept interval."
        : "Range removes that interval and redraws the remaining candidates.",
    proximity:
      answer === "equidistant"
        ? "Proximity keeps only the midpoint tie."
        : "Proximity keeps the side closer to the answer.",
    parity: "Parity leaves alternating candidate cells.",
    modular: "Modulo leaves repeating remainder cells.",
    digit_sum: "Digit sum keeps numbers matching the threshold result.",
    special: "Special properties create sparse matching cells.",
    digit_compare: "Digit comparison keeps numbers matching the digit pattern.",
    divisible: "Divisibility keeps or removes regular multiple cells.",
  };

  return `${answerText} ${behaviorByType[question.type]}`;
}

function CandidateGrid({ candidates, lastEntry, summary }) {
  const model = useMemo(
    () => getCandidateGridModel(candidates, summary),
    [candidates, summary]
  );
  const behavior = getBarBehavior(lastEntry);

  return (
    <div
      className="candidateGrid"
      aria-label={`${summary.count} candidates remaining. Active candidates run from ${summary.min} to ${summary.max}. Grid is ${model.gridSide} by ${model.gridSide}, ending at ${model.gridMax}. ${behavior}`}
      style={{ "--grid-side": model.gridSide }}
    >
      <div className="gridText">
        <span>1</span>
        <span>{model.gridMax}</span>
      </div>
      <div className="numberGrid" aria-hidden="true">
        {model.cells.map((cell, index) => (
          <span
            className={`numberCell ${cell.active ? "active" : "inactive"} ${
              cell.inGameRange ? "" : "outside"
            } ${model.showLabels ? "labeled" : "unlabeled"}`}
            key={index}
            title={String(cell.value)}
          >
            {cell.label}
          </span>
        ))}
      </div>
      <div className="gridScale">
        <span>1</span>
        <span>
          active {model.activeMin}-{model.activeMax}
        </span>
        <span>{model.gridMax}</span>
      </div>
      <p className="gridBehavior">{behavior}</p>
    </div>
  );
}

function QuestionPicker({
  activeType,
  setActiveType,
  activeQuestions,
  typeCounts,
  disabledReason,
  onAsk,
}) {
  const activeCount = typeCounts[activeType] ?? 0;

  return (
    <div className="picker">
      <div className="tabs" aria-label="Question type">
        {TYPE_ORDER.map((type) => (
          <button
            className={activeType === type ? "selected" : ""}
            key={type}
            type="button"
            onClick={() => setActiveType(type)}
          >
            {TYPE_META[type].shortLabel}
          </button>
        ))}
      </div>

      <div className="pickerMeta">
        <span>
          {TYPE_META[activeType].label} {activeCount}/{MAX_TYPE_QUESTIONS}
        </span>
        {activeType === "modular" && <strong>No mod 10</strong>}
      </div>

      <div className="questionList">
        {activeQuestions.map((question) => {
          const reason = disabledReason(question);
          return (
            <button
              className="questionButton"
              disabled={Boolean(reason)}
              key={question.id}
              type="button"
              onClick={() => onAsk(question)}
            >
              <span>{question.text}</span>
              {reason && <em>{reason}</em>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function ResultPanel({
  result,
  historyLength,
  copied,
  copyRun,
  reset,
}) {
  return (
    <div className={`result ${result.won ? "win" : "miss"}`} role="status">
      <h2>{result.won ? "You got it" : "Missed it"}</h2>
      <p>
        Guess {result.guess}. Secret {result.secret}. Off by {result.offBy}.
      </p>
      <p>
        {result.won
          ? `Solved in ${historyLength} questions.`
          : `AI benchmark is ${formatPercent(AI_BENCHMARK)}.`}
      </p>
      <div className="resultActions">
        <button type="button" onClick={copyRun}>
          {copied ? "Copied" : "Copy run"}
        </button>
        <button type="button" onClick={reset}>
          Play again
        </button>
      </div>
    </div>
  );
}
