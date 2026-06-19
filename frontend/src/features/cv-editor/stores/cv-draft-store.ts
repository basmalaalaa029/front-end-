import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { CvData } from "@/features/cv-editor/data/cv-types";
import { migrateCvData } from "@/features/cv-editor/data/cv-data-migrate";
import { createStarterCvData } from "@/features/cv-editor/data/cv-templates";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";

type SetCvData = CvData | ((prev: CvData) => CvData);

interface CvDraftState {
  data: CvData;
  activeSection: string;
  jobDescription: string;
  aiMarkdown: string | null;
  aiEnhancedData: Record<string, unknown> | null;
  lastTemplateId: TemplateId | null;

  setData: (value: SetCvData) => void;
  setActiveSection: (section: string) => void;
  setJobDescription: (text: string) => void;
  setAiMarkdown: (markdown: string | null) => void;
  setAiEnhancedData: (data: Record<string, unknown> | null) => void;
  setLastTemplateId: (id: TemplateId) => void;
  resetDraft: () => void;
}

const initialDraft = {
  data: createStarterCvData(),
  activeSection: "contact",
  jobDescription: "",
  aiMarkdown: null as string | null,
  aiEnhancedData: null as Record<string, unknown> | null,
  lastTemplateId: null as TemplateId | null,
};

export const useCvDraftStore = create<CvDraftState>()(
  persist(
    (set) => ({
      ...initialDraft,

      setData: (value) =>
        set((state) => ({
          data: typeof value === "function" ? value(state.data) : value,
        })),

      setActiveSection: (activeSection) => set({ activeSection }),

      setJobDescription: (jobDescription) => set({ jobDescription }),

      setAiMarkdown: (aiMarkdown) => set({ aiMarkdown }),

      setAiEnhancedData: (aiEnhancedData) => set({ aiEnhancedData }),

      setLastTemplateId: (lastTemplateId) => set({ lastTemplateId }),

      resetDraft: () => set({ ...initialDraft }),
    }),
    {
      name: "cv-draft-storage",
      version: 1,
      partialize: (state) => ({
        data: state.data,
        activeSection: state.activeSection,
        jobDescription: state.jobDescription,
        aiMarkdown: state.aiMarkdown,
        aiEnhancedData: state.aiEnhancedData,
        lastTemplateId: state.lastTemplateId,
      }),
      merge: (persisted, current) => {
        const p = persisted as Partial<CvDraftState> | undefined;
        if (!p?.data) return current;
        return {
          ...current,
          ...p,
          data: migrateCvData(p.data),
        };
      },
    },
  ),
);
