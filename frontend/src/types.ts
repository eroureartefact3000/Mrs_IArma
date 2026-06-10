// TypeScript types matching the backend `pipeline.schema` Pydantic models.
// Keep these in sync with /Users/.../pipeline/schema.py — they're the
// contract between the engine and the UI.

export type PredictedTier = "Grand Prix" | "Gold" | "Silver" | "Bronze" | "No Medal";

export type ConfidenceLabel = "high" | "medium" | "low";

export type AxisKey = "idea" | "strategy" | "execution" | "impact";

export interface AxisDisplay {
  key: AxisKey;
  label: string; // display label (e.g. "Creative Idea")
  score: number; // 0-100
  weight: number; // 0.0-1.0
}

export type PresageKind = "favorable" | "unfavorable";
export type PresageType = "aesthetic" | "client" | "network";

export interface Presage {
  type: PresageType;
  kind: PresageKind;
  title: string;
  detail: string;
  malus_pct: number; // 0 if favorable
}

export interface TierPrediction {
  predicted_tier: PredictedTier;
  tier_label: string; // "GOLD LION", "NO LION", etc.
  tier_probabilities: Record<PredictedTier, number>;
  confidence: ConfidenceLabel;
  score_percent: number; // 0-100, headline figure
  mystic_verdict: string; // "The stars align. Your campaign will carry gold."
  axes: AxisDisplay[];
  presages: Presage[];
  synthesis: string; // 1-2 sentence post-mortem
}

export interface EvaluateResponse {
  evaluation_id: string;
  elapsed_seconds: number;
  tier_prediction: TierPrediction;
  // _debug field is present but not surfaced in the UI.
}

export interface CannesCategory {
  key: string;
  label: string;
  family: string;
  enabled: boolean;
}

export interface CategoriesResponse {
  categories: CannesCategory[];
}

// Form state for the multi-step wizard.
export interface EvaluationFormState {
  campaign_name: string;
  category: string;
  client: string;
  client_internationally_known: boolean;
  agency: string;
  image: File | null;
}
