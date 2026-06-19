import { useMutation, useQuery } from "@tanstack/react-query";
import { getJobResults, matchJobs, matchJobsUpload } from "../lib/job-agent-api";
import type { JobMatchRequest } from "../types";

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

export function useJobResults(sessionId: string | null) {
  return useQuery({
    queryKey: ["jobs", sessionId],
    queryFn: () => getJobResults(sessionId!),
    enabled: Boolean(sessionId),
  });
}
