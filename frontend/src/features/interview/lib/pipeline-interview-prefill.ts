import { useAuthStore } from "@/features/auth/stores/auth-store";
import { cvAgentFetch } from "@/shared/lib/cv-agent-client";
import {
  loadWorkflowCv,
  loadWorkflowJobPick,
  type WorkflowCvContext,
  type WorkflowJobPick,
} from "@/features/hub-shell/lib/workflow-pipeline";
import { getPipelineCvFile } from "@/features/hub-shell/lib/pipeline-cv-file";

export type InterviewPrefillPayload = {
  jobDescription: string;
  candidateName: string;
  cvFile: File | null;
};

function buildJobDescription(
  job: WorkflowJobPick | null,
  wf: WorkflowCvContext | null,
): string {
  if (job?.jobDescription?.trim()) return job.jobDescription.trim();
  if (wf?.jobDescription?.trim()) return wf.jobDescription.trim();
  if (job) {
    return [`Role: ${job.title}`, job.company ? `Company: ${job.company}` : ""]
      .filter(Boolean)
      .join("\n\n");
  }
  return wf?.targetRole ? `Target role: ${wf.targetRole}` : "";
}

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
    if (stored.name.toLowerCase().endsWith(".pdf")) return stored;
    if (stored.type === "application/pdf") return stored;
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

export async function buildInterviewPrefill(): Promise<InterviewPrefillPayload | null> {
  const wf = loadWorkflowCv();
  const job = loadWorkflowJobPick();
  if (!wf && !job && !getPipelineCvFile()) return null;

  const jobDescription = buildJobDescription(job, wf);
  const authName = useAuthStore.getState().user?.name?.trim() ?? "";
  const candidateName = authName || wf?.targetRole?.trim() || job?.title?.trim() || "";
  const label = candidateName || job?.title || wf?.targetRole || "CV";
  const cvFile = await resolveInterviewCvFile(wf, label);

  if (!cvFile && !jobDescription) return null;

  return { jobDescription, candidateName, cvFile };
}

export async function applyInterviewWorkflowPrefill(host: HTMLElement): Promise<boolean> {
  const prefill = await buildInterviewPrefill();
  if (!prefill) return false;

  const apply = (
    window as Window & {
      __CV_INTERVIEW_APPLY_PREFILL__?: (data: InterviewPrefillPayload) => void;
    }
  ).__CV_INTERVIEW_APPLY_PREFILL__;

  if (typeof apply === "function") {
    apply(prefill);
    return true;
  }

  const jd = host.querySelector<HTMLTextAreaElement>("#jd");
  if (jd && prefill.jobDescription && !jd.value.trim()) {
    jd.value = prefill.jobDescription;
  }

  const nameInput = host.querySelector<HTMLInputElement>("#candidate-name");
  if (nameInput && prefill.candidateName && !nameInput.value.trim()) {
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

  return Boolean(prefill.cvFile || prefill.jobDescription);
}
