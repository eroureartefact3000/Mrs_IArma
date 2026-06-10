// Multi-step Typeform-style wizard for collecting the 6 inputs required by
// the prediction engine: campaign_name, category, client +
// client_internationally_known, agency, image.
//
// One question per step. Pressing Enter advances. The SunRays motif frames
// each step.

import { useEffect, useRef, useState } from "react";
import type { CannesCategory, EvaluationFormState } from "../types";
import { fetchCategories } from "../api";
import { SunRays } from "./SunRays";

interface FormWizardProps {
  onSubmit: (form: EvaluationFormState) => void;
}

type StepKey = "campaign" | "category" | "client" | "agency" | "image";

const STEPS: { key: StepKey; question: string; hint?: string }[] = [
  { key: "campaign", question: "What's your campaign name?" },
  { key: "category", question: "Which Cannes Lions category?" },
  {
    key: "client",
    question: "Who is the client?",
  },
  { key: "agency", question: "Which agency made the work?" },
  {
    key: "image",
    question: "Upload your board",
    hint: "JPG · PNG · WEBP · AVIF — up to 25 MB",
  },
];

export function FormWizard({ onSubmit }: FormWizardProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [categories, setCategories] = useState<CannesCategory[]>([]);
  const [form, setForm] = useState<EvaluationFormState>({
    campaign_name: "",
    category: "",
    client: "",
    client_internationally_known: true,
    agency: "",
    image: null,
  });
  const inputRef = useRef<HTMLInputElement>(null);

  // Load categories from the backend on mount
  useEffect(() => {
    fetchCategories()
      .then((res) => {
        const enabled = res.categories.filter((c) => c.enabled);
        setCategories(enabled);
        // Pre-select the first enabled category
        if (enabled.length > 0 && !form.category) {
          setForm((f) => ({ ...f, category: enabled[0].key }));
        }
      })
      .catch(() => {
        // Quiet failure — the category step will show an empty state
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-focus the input when the step changes
  useEffect(() => {
    inputRef.current?.focus();
  }, [stepIndex]);

  const currentStep = STEPS[stepIndex];
  const isLast = stepIndex === STEPS.length - 1;

  function canAdvance(): boolean {
    switch (currentStep.key) {
      case "campaign":
        return form.campaign_name.trim().length > 0;
      case "category":
        return form.category.length > 0;
      case "client":
        return form.client.trim().length > 0;
      case "agency":
        return form.agency.trim().length > 0;
      case "image":
        return form.image !== null;
    }
  }

  function handleAdvance() {
    if (!canAdvance()) return;
    if (isLast) {
      onSubmit(form);
    } else {
      setStepIndex((i) => i + 1);
    }
  }

  function handleBack() {
    setStepIndex((i) => Math.max(0, i - 1));
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && currentStep.key !== "image") {
      e.preventDefault();
      handleAdvance();
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-4 animate-fade-in">
      <SunRays variant="open" size={420}>
        <div className="text-center">
          <div className="label-caps mb-6">
            Question {stepIndex + 1} / {STEPS.length}
          </div>
          <h1 className="editorial text-2xl md:text-3xl leading-tight mb-6 px-2">
            {currentStep.question}
          </h1>

          {/* Render the input that matches the current step */}
          {currentStep.key === "campaign" && (
            <input
              ref={inputRef}
              type="text"
              value={form.campaign_name}
              onChange={(e) => setForm({ ...form, campaign_name: e.target.value })}
              onKeyDown={handleKeyDown}
              maxLength={200}
              placeholder="Type your answer..."
              className="w-full bg-transparent border-b border-ink text-center editorial text-xl py-1.5 focus:outline-none placeholder:text-ink-faint placeholder:italic"
            />
          )}

          {currentStep.key === "category" && (
            <select
              ref={inputRef as unknown as React.RefObject<HTMLSelectElement>}
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent border-b border-ink text-center editorial text-2xl py-2 focus:outline-none cursor-pointer"
            >
              {categories.length === 0 && <option value="">Loading...</option>}
              {categories.map((cat) => (
                <option key={cat.key} value={cat.key}>
                  {cat.label}
                </option>
              ))}
            </select>
          )}

          {currentStep.key === "client" && (
            <>
              <input
                ref={inputRef}
                type="text"
                value={form.client}
                onChange={(e) => setForm({ ...form, client: e.target.value })}
                onKeyDown={handleKeyDown}
                maxLength={200}
                placeholder="Type your answer..."
                className="w-full bg-transparent border-b border-ink text-center editorial text-xl py-1.5 focus:outline-none placeholder:text-ink-faint placeholder:italic"
              />
              <div className="mt-4 flex items-center justify-center gap-6">
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="radio"
                    name="intl"
                    checked={form.client_internationally_known}
                    onChange={() => setForm({ ...form, client_internationally_known: true })}
                  />
                  International
                </label>
                <label className="flex items-center gap-2 cursor-pointer text-sm">
                  <input
                    type="radio"
                    name="intl"
                    checked={!form.client_internationally_known}
                    onChange={() => setForm({ ...form, client_internationally_known: false })}
                  />
                  Local
                </label>
              </div>
            </>
          )}

          {currentStep.key === "agency" && (
            <input
              ref={inputRef}
              type="text"
              value={form.agency}
              onChange={(e) => setForm({ ...form, agency: e.target.value })}
              onKeyDown={handleKeyDown}
              maxLength={200}
              placeholder="Type your answer..."
              className="w-full bg-transparent border-b border-ink text-center editorial text-xl py-1.5 focus:outline-none placeholder:text-ink-faint placeholder:italic"
            />
          )}

          {currentStep.key === "image" && (
            <FileUpload
              file={form.image}
              onChange={(file) => setForm({ ...form, image: file })}
            />
          )}
        </div>
      </SunRays>

      {currentStep.hint && (
        <div className="text-center label-caps mt-6">{currentStep.hint}</div>
      )}

      {/* Step indicator + CTA */}
      <div className="flex flex-col items-center gap-4 mt-8">
        <button
          className="cta-primary"
          disabled={!canAdvance()}
          onClick={handleAdvance}
        >
          {isLast ? "Consult the oracle" : "Next"}
        </button>
        <div className="flex gap-2 items-center text-ink-faint text-xs">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`block rounded-full transition-all ${
                i === stepIndex ? "w-2.5 h-2.5 bg-ink" : "w-1.5 h-1.5 bg-ink-faint/40"
              }`}
            />
          ))}
          {stepIndex > 0 && (
            <button
              onClick={handleBack}
              className="ml-4 text-xs underline underline-offset-2 hover:text-ink"
            >
              back
            </button>
          )}
        </div>
        {currentStep.key !== "image" && (
          <div className="text-ink-faint text-xs">or press Enter ↵</div>
        )}
      </div>
    </div>
  );
}

interface FileUploadProps {
  file: File | null;
  onChange: (file: File | null) => void;
}

function FileUpload({ file, onChange }: FileUploadProps) {
  return (
    <label className="block cursor-pointer">
      <input
        type="file"
        accept=".jpg,.jpeg,.png,.webp,.avif,.gif"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
        className="sr-only"
      />
      <div className="border border-dashed border-ink py-6 px-4 hover:bg-ink/[0.03] transition-colors">
        {file ? (
          <div>
            <div className="editorial text-lg">{file.name}</div>
            <div className="label-caps mt-1">
              {(file.size / (1024 * 1024)).toFixed(2)} MB · click to change
            </div>
          </div>
        ) : (
          <div>
            <div className="editorial text-lg italic text-ink-faint">
              Drop your board, or click to select
            </div>
          </div>
        )}
      </div>
    </label>
  );
}
