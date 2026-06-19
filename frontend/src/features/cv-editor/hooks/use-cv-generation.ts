import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getResult,
  getStatus,
  startGeneration,
  type CvAgentGenerateRequest,
  type PollOptions,
  waitForCompletion,
} from "../lib/cv-agent-api";

export function useGenerateCv() {
  return useMutation({
    mutationKey: ["cv", "generate"],
    mutationFn: ({
      payload,
      signal,
    }: {
      payload: CvAgentGenerateRequest;
      signal?: AbortSignal;
    }) => startGeneration(payload, signal),
  });
}

export function useCvStatus(sessionId: string | null, enabled = true) {
  return useQuery({
    queryKey: ["cv", "status", sessionId],
    queryFn: () => getStatus(sessionId!),
    enabled: Boolean(sessionId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });
}

export function useCvResult(sessionId: string | null, enabled = false) {
  return useQuery({
    queryKey: ["cv", "result", sessionId],
    queryFn: () => getResult(sessionId!),
    enabled: Boolean(sessionId) && enabled,
  });
}

export function useWaitForCvCompletion() {
  return useMutation({
    mutationKey: ["cv", "wait"],
    mutationFn: ({
      sessionId,
      signal,
      onProgress,
    }: {
      sessionId: string;
      signal?: AbortSignal;
      onProgress?: PollOptions["onProgress"];
    }) => waitForCompletion(sessionId, { signal, onProgress }),
  });
}
