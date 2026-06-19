import { useMutation, useQuery } from "@tanstack/react-query";
import {
  evaluateInterview,
  getInterviewSession,
  startInterview,
  submitInterviewAnswer,
} from "../lib/interview-api";
import type { StartInterviewRequest, SubmitAnswerRequest } from "../types";

export function useStartInterview() {
  return useMutation({
    mutationKey: ["interview", "start"],
    mutationFn: (req: StartInterviewRequest) => startInterview(req),
  });
}

export function useInterviewSession(sessionId: string | null) {
  return useQuery({
    queryKey: ["interview", sessionId],
    queryFn: () => getInterviewSession(sessionId!),
    enabled: Boolean(sessionId),
  });
}

export function useSubmitInterviewAnswer() {
  return useMutation({
    mutationKey: ["interview", "answer"],
    mutationFn: ({
      sessionId,
      req,
    }: {
      sessionId: string;
      req: SubmitAnswerRequest;
    }) => submitInterviewAnswer(sessionId, req),
  });
}

export function useEvaluateInterview() {
  return useMutation({
    mutationKey: ["interview", "evaluate"],
    mutationFn: (sessionId: string) => evaluateInterview(sessionId),
  });
}
