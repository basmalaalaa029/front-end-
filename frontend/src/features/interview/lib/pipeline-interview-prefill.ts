import { useAuthStore } from "@/features/auth/stores/auth-store";
import { cvAgentFetch } from "@/shared/lib/cv-agent-client";
import {
  loadWorkflowCv,
  loadWorkflowJobPick,
  type WorkflowCvContext,
} from "@/features/hub-shell/lib/workflow-pipeline";
import { getPipelineCvFile } from "@/features/hub-shell/lib/pipeline-cv-file";
import { buildInterviewPrefillFromWorkflow } from "@/features/interview/lib/build-interview-job-description";

export type InterviewPrefillPayload = {
  jobDescription: string;
  candidateName: string;
  cvFile: File | null;
};

export type InterviewPrefillOptions = {
  jobDescription?: string;
};

function safePdfStem(label: string): string {
  const stem = label.replace(/[^\w.-]+/g, "_").replace(/^_|_$/g, "");
  return stem || "CV";
}

async function cvTextToPdfFile(cvText: string, label: string): Promise<File> {
  const blob = await cvAgentFetch<Blob>("/pdf/direct", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      markdown: cvText,
      candidate_name: label,
    }),
  });
  return new File([blob], `${safePdfStem(label)}_CV.pdf`, {
    type: "application/pdf",
  });
}

async function resolveInterviewCvFile(
  wf: WorkflowCvContext | null,
  label: string,
): Promise<File | null> {
  const stored = getPipelineCvFile();
  if (stored) {
    if (stored.name.toLowerCase().endsWith(".pdf") || stored.type === "application/pdf") {
      return stored;
    }
  }

  const cvText = wf?.cvText?.trim() ?? "";
  if (cvText.length >= 50) {
    try {
      return await cvTextToPdfFile(cvText, label);
    } catch {
      return null;
    }
  }

  return null;
}

export async function buildInterviewPrefill(
  options?: InterviewPrefillOptions,
): Promise<InterviewPrefillPayload | null> {
  const wf = loadWorkflowCv();
  const job = loadWorkflowJobPick();
  if (!wf && !job && !getPipelineCvFile()) return null;

  const authName = useAuthStore.getState().user?.name?.trim() ?? "";
  const fromWorkflow = buildInterviewPrefillFromWorkflow(job, wf, authName);
  const jobDescription =
    options?.jobDescription?.trim() || fromWorkflow.jobDescription;
  const candidateName = fromWorkflow.candidateName;
  const label = candidateName || job?.title || wf?.targetRole || "CV";
  const cvFile = await resolveInterviewCvFile(wf, label);

  if (!cvFile && !jobDescription) return null;

  return { jobDescription, candidateName, cvFile };
}

function applyPrefillToDom(host: HTMLElement, prefill: InterviewPrefillPayload): void {
  const apply = (
    window as Window & {
      __CV_INTERVIEW_APPLY_PREFILL__?: (data: InterviewPrefillPayload) => void;
    }
  ).__CV_INTERVIEW_APPLY_PREFILL__;

  if (typeof apply === "function") {
    apply(prefill);
    return;
  }

  const jd = host.querySelector<HTMLTextAreaElement>("#jd");
  if (jd && prefill.jobDescription) {
    jd.value = prefill.jobDescription;
  }

  const nameInput = host.querySelector<HTMLInputElement>("#candidate-name");
  if (nameInput && prefill.candidateName) {
    nameInput.value = prefill.candidateName;
  }

  if (prefill.cvFile) {
    const input = host.querySelector<HTMLInputElement>("#cv-file");
    const dzLbl = host.querySelector("#dz-lbl");
    const dz = host.querySelector("#dz");
    if (input) {
      try {
        const dt = new DataTransfer();
        dt.items.add(prefill.cvFile);
        input.files = dt.files;
      } catch {
        /* DataTransfer unsupported */
      }
    }
    if (dzLbl) dzLbl.textContent = `✓ ${prefill.cvFile.name}`;
    dz?.classList.add("active");
  }
}

export async function applyInterviewWorkflowPrefill(
  host: HTMLElement,
  options?: InterviewPrefillOptions,
): Promise<boolean> {
  const prefill = await buildInterviewPrefill(options);
  if (!prefill) return false;
  applyPrefillToDom(host, prefill);
  return Boolean(prefill.cvFile || prefill.jobDescription);
}

export async function applyInterviewWorkflowPrefillForce(
  host: HTMLElement,
  options?: InterviewPrefillOptions,
): Promise<boolean> {
  const prefill = await buildInterviewPrefill(options);
  if (!prefill) return false;
  applyPrefillToDom(host, prefill);
  return Boolean(prefill.cvFile || prefill.jobDescription);
}
