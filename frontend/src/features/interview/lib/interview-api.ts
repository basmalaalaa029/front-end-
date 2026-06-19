import { cvAgentFetch } from "@/shared/lib/cv-agent-client";
import type {
  EvaluationResult,
  InterviewSession,
  StartInterviewRequest,
  StartInterviewResponse,
  SubmitAnswerRequest,
  SubmitAnswerResponse,
} from "../types";

export async function startInterview(
  req: StartInterviewRequest,
): Promise<StartInterviewResponse> {
  return cvAgentFetch<StartInterviewResponse>("/interview/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      cv_text: req.cvText,
      target_role: req.targetRole ?? "Software Engineer",
      company: req.company ?? "",
    }),
    timeoutMs: 30_000,
  });
}

export async function getInterviewSession(
  sessionId: string,
): Promise<InterviewSession> {
  return cvAgentFetch<InterviewSession>(
    `/interview/${encodeURIComponent(sessionId)}`,
    { method: "GET" },
  );
}

export async function submitInterviewAnswer(
  sessionId: string,
  req: SubmitAnswerRequest,
): Promise<SubmitAnswerResponse> {
  return cvAgentFetch<SubmitAnswerResponse>(
    `/interview/${encodeURIComponent(sessionId)}/answer`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: req.questionId,
        answer: req.answer,
      }),
      timeoutMs: 30_000,
    },
  );
}

export async function evaluateInterview(
  sessionId: string,
): Promise<EvaluationResult> {
  return cvAgentFetch<EvaluationResult>(
    `/interview/${encodeURIComponent(sessionId)}/evaluate`,
    { method: "POST", timeoutMs: 30_000 },
  );
}
