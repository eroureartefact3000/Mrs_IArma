// Mrs Airma · The Cannes Oracle — application shell.
//
// State machine: form -> loading -> result | error
//   form        → FormWizard collects 6 inputs
//   loading     → API call in flight (~45s)
//   result      → ResultPage shows tier + axes + presages
//   error       → ErrorPage with possible causes + retry CTA

import { useState } from "react";
import type { EvaluateResponse, EvaluationFormState } from "./types";
import { evaluateBoard, ApiError } from "./api";
import { Header } from "./components/Header";
import { FormWizard } from "./components/FormWizard";
import { Loading } from "./components/Loading";
import { ResultPage } from "./components/ResultPage";
import { ErrorPage } from "./components/ErrorPage";

type View = "form" | "loading" | "result" | "error";

export function App() {
  const [view, setView] = useState<View>("form");
  const [result, setResult] = useState<EvaluateResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(form: EvaluationFormState) {
    setView("loading");
    setErrorMessage("");
    try {
      const response = await evaluateBoard(form);
      setResult(response);
      setView("result");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? `HTTP ${err.status} — ${err.message}`
          : err instanceof Error
            ? err.message
            : String(err);
      setErrorMessage(message);
      setView("error");
    }
  }

  function reset() {
    setResult(null);
    setErrorMessage("");
    setView("form");
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 flex items-center justify-center py-12">
        {view === "form" && <FormWizard onSubmit={handleSubmit} />}
        {view === "loading" && <Loading />}
        {view === "result" && result && <ResultPage result={result} onRetry={reset} />}
        {view === "error" && <ErrorPage message={errorMessage} onRetry={reset} />}
      </main>
      <footer className="py-6 text-center label-caps">
        Mrs IArma · Cannes Lions tier prediction · v0.1
      </footer>
    </div>
  );
}
