/** Cross-feature CV → jobs → interview handoff (sessionStorage). */

export type WorkflowSource = "generate" | "analyze" | "editor";

export type WorkflowCvContext = {
  cvText: string;
  targetRole: string;
  company: string;
  jobDescription: string;
  source: WorkflowSource;
};

export type WorkflowJobPick = {
  title: string;
  company: string;
  targetRole: string;
  jobDescription?: string;
  url?: string;
};

export const WORKFLOW_CV_KEY = "hub:workflowCv";
export const WORKFLOW_JOB_KEY = "hub:workflowJob";

export type JobNavigationState = {
  autoStart?: boolean;
  targetRole?: string;
};

export type InterviewNavigationState = {
  autoStart?: boolean;
  targetRole?: string;
};

function readJson<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function writeJson(key: string, value: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
}

export function saveWorkflowCv(ctx: WorkflowCvContext): void {
  writeJson(WORKFLOW_CV_KEY, ctx);
}

export function loadWorkflowCv(): WorkflowCvContext | null {
  return readJson<WorkflowCvContext>(WORKFLOW_CV_KEY);
}

export function saveWorkflowJobPick(pick: WorkflowJobPick): void {
  writeJson(WORKFLOW_JOB_KEY, pick);
}

export function loadWorkflowJobPick(): WorkflowJobPick | null {
  return readJson<WorkflowJobPick>(WORKFLOW_JOB_KEY);
}

export function clearWorkflowJobPick(): void {
  try {
    sessionStorage.removeItem(WORKFLOW_JOB_KEY);
  } catch {
    /* ignore */
  }
}
