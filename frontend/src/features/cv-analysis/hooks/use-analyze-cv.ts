import { useMutation } from "@tanstack/react-query";
import { runAnalysisAsync, runAnalysisUploadAsync } from "../lib/cv-analysis-api";
import type { AnalyzeCvInput } from "../types";

export function useAnalyzeCvAsync() {
  return useMutation({
    mutationKey: ["analysis", "async"],
    mutationFn: (req: AnalyzeCvInput & { signal?: AbortSignal }) =>
      runAnalysisAsync(req),
  });
}

export function useAnalyzeCvUpload() {
  return useMutation({
    mutationKey: ["analysis", "upload"],
    mutationFn: ({
      file,
      opts,
    }: {
      file: File;
      opts?: AnalyzeCvInput & { signal?: AbortSignal };
    }) => runAnalysisUploadAsync(file, opts),
  });
}
