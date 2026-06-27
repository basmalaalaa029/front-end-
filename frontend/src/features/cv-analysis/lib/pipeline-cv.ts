import type { CvData } from "@/features/cv-editor/data/cv-types";
import { cvDataToMarkdown } from "@/features/cv-editor/lib/cv-to-profile";
import { useCvDraftStore } from "@/features/cv-editor/stores/cv-draft-store";
import {
  loadWorkflowCv,
  saveWorkflowCv,
  type WorkflowSource,
} from "@/features/hub-shell/lib/workflow-pipeline";
import {
  getDraftAnalysisInputs,
  type DraftAnalysisInputs,
} from "./draft-for-analysis";
import { setPendingJobFile } from "@/features/hub-shell/lib/pending-job-file";

/** Pipeline CV context: workflow handoff first, then editor draft. */
export function getPipelineCvInputs(): DraftAnalysisInputs | null {
  const wf = loadWorkflowCv();
  if (wf?.cvText && wf.cvText.length >= 50) {
    return {
      cvText: wf.cvText,
      targetRole: wf.targetRole,
      company: wf.company,
      jobDescription: wf.jobDescription,
    };
  }
  return getDraftAnalysisInputs();
}

export function saveWorkflowCvFromInputs(
  inputs: DraftAnalysisInputs,
  source: WorkflowSource,
): void {
  saveWorkflowCv({
    cvText: inputs.cvText,
    targetRole: inputs.targetRole,
    company: inputs.company,
    jobDescription: inputs.jobDescription,
    source,
  });
}

/** Persist generated/edited CV data for the jobs → interview pipeline. */
export function persistCvDataForPipeline(cvData: CvData, jobDescription = ""): DraftAnalysisInputs | null {
  const cvText = cvDataToMarkdown(cvData).trim();
  if (cvText.length < 50) return null;

  const targetRole =
    cvData.role.trim() ||
    cvData.education.map((e) => e.degree.trim()).find(Boolean) ||
    cvData.name.trim() ||
    "Target role";

  const store = useCvDraftStore.getState();
  store.setData(cvData);
  if (jobDescription.trim()) store.setJobDescription(jobDescription.trim());

  const inputs: DraftAnalysisInputs = {
    cvText,
    targetRole,
    company: "",
    jobDescription: jobDescription.trim(),
  };
  saveWorkflowCvFromInputs(inputs, "generate");
  return inputs;
}

export function handoffCvToJobMatching(opts: {
  cvText?: string;
  cvFile?: File | null;
  targetRole: string;
  company?: string;
  jobDescription?: string;
  source: WorkflowSource;
}): boolean {
  if (opts.cvFile) {
    setPendingJobFile(opts.cvFile);
  }

  const cvText = opts.cvText?.trim() ?? "";
  if (cvText.length >= 50) {
    saveWorkflowCvFromInputs(
      {
        cvText,
        targetRole: opts.targetRole,
        company: opts.company ?? "",
        jobDescription: opts.jobDescription ?? "",
      },
      opts.source,
    );
    return true;
  }

  if (opts.cvFile) {
    saveWorkflowCv({
      cvText: "",
      targetRole: opts.targetRole,
      company: opts.company ?? "",
      jobDescription: opts.jobDescription ?? "",
      source: opts.source,
    });
    return true;
  }

  const draft = getPipelineCvInputs();
  if (draft) {
    saveWorkflowCvFromInputs(draft, opts.source);
    return true;
  }

  return false;
}
