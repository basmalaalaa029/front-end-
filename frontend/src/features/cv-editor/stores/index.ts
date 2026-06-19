import { create } from "zustand";
import type { CvAgentScores } from "@/features/cv-editor/lib/cv-agent-api";

export { useCvDraftStore } from "./cv-draft-store";

export type GenStage =
  | "idle"
  | "submitting"
  | "running"
  | "downloading"
  | "done"
  | "failed";

interface CvGenerationState {
  sessionId: string | null;
  genStage: GenStage;
  genMessage: string;
  aiScores: CvAgentScores | null;
  aiMarkdown: string | null;

  setSession: (id: string) => void;
  setStage: (stage: GenStage, message?: string) => void;
  setResult: (scores: CvAgentScores | null, markdown: string | null) => void;
  reset: () => void;
}

export const useCvGenerationStore = create<CvGenerationState>()((set) => ({
  sessionId: null,
  genStage: "idle",
  genMessage: "",
  aiScores: null,
  aiMarkdown: null,

  setSession: (id) => set({ sessionId: id }),
  setStage: (stage, message) =>
    set((s) => ({
      genStage: stage,
      genMessage: message !== undefined ? message : s.genMessage,
    })),
  setResult: (scores, markdown) => set({ aiScores: scores, aiMarkdown: markdown }),
  reset: () =>
    set({
      sessionId: null,
      genStage: "idle",
      genMessage: "",
      aiScores: null,
      aiMarkdown: null,
    }),
}));
