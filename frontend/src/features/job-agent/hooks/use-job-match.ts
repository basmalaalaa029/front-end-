import { useMutation, useQuery } from "@tanstack/react-query";
import {
  matchJobs,
  matchJobsUpload,
  waitForJobResults,
} from "../lib/job-agent-api";
import type { JobMatchRequest, JobMatchStatus } from "../types";

export function useJobMatch() {
  return useMutation({
    mutationKey: ["jobs", "match"],
    mutationFn: (req: JobMatchRequest) => matchJobs(req),
  });
}

export function useJobMatchUpload() {
  return useMutation({
    mutationKey: ["jobs", "match", "upload"],
    mutationFn: (vars: { file: File; targetRole?: string; location?: string }) =>
      matchJobsUpload(vars.file, { targetRole: vars.targetRole, location: vars.location }),
  });
}

export function useJobResults(
  sessionId: string | null,
  onStatus?: (status: JobMatchStatus) => void,
) {
  return useQuery({
    queryKey: ["jobs", "result", sessionId],
    queryFn: () => waitForJobResults(sessionId!, onStatus),
    enabled: Boolean(sessionId),
    staleTime: Infinity,
    retry: false,
  });
}
