import type { WorkflowCvContext, WorkflowJobPick } from "@/features/hub-shell/lib/workflow-pipeline";

export type InterviewJobHandoff = {
  title: string;
  company: string;
  location?: string;
  salary?: string;
  url?: string;
  description?: string;
  why?: string;
  matched_skills?: string[];
  missing_skills?: string[];
};

/** Build a job description for interview practice from a matched role. */
export function buildInterviewJobDescription(job: InterviewJobHandoff): string {
  const description = job.description?.trim();
  if (description && description.length >= 80) {
    return description;
  }

  const lines: string[] = [];
  const titleLine = [job.title, job.company].filter(Boolean).join(" at ");
  if (titleLine) lines.push(titleLine);

  const meta = [job.location, job.salary].filter(Boolean).join(" · ");
  if (meta) lines.push(meta);

  if (description) lines.push(description);
  if (job.why?.trim()) lines.push(job.why.trim());

  if (job.matched_skills?.length) {
    lines.push(`Matched skills: ${job.matched_skills.join(", ")}`);
  }
  if (job.missing_skills?.length) {
    lines.push(`Skills to highlight: ${job.missing_skills.join(", ")}`);
  }

  if (job.url?.trim()) lines.push(`Posting: ${job.url.trim()}`);

  return lines.join("\n\n").trim();
}

export function buildInterviewPrefillFromWorkflow(
  job: WorkflowJobPick | null,
  wf: WorkflowCvContext | null,
  candidateName: string,
): { jobDescription: string; candidateName: string } {
  const jobDescription =
    job?.jobDescription?.trim() ||
    (job
      ? buildInterviewJobDescription({
          title: job.title,
          company: job.company,
        })
      : "") ||
    wf?.jobDescription?.trim() ||
    (wf?.targetRole ? `Target role: ${wf.targetRole}` : "") ||
    (job?.targetRole ? `Target role: ${job.targetRole}` : "");

  const name =
    candidateName.trim() ||
    wf?.targetRole?.trim() ||
    job?.title?.trim() ||
    "";

  return { jobDescription, candidateName: name };
}
