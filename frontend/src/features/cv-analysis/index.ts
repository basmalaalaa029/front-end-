/** CV analysis vs job description — async /cv-analysis API. */
export { default as AnalysisPage } from "./components/analysis-page";
export {
  runAnalysisAsync,
  runAnalysisUploadAsync,
  saveAnalysisCache,
  loadAnalysisCache,
  ANALYSIS_CACHE_KEY,
  CV_AGENT_BASE,
  CvAnalysisApiError,
} from "./lib/cv-analysis-api";
export { getDraftAnalysisInputs, getDraftAnalysisFile, cvTextToAnalysisFile, formatCvFileSize } from "./lib/draft-for-analysis";
export { setPendingAnalysisFile, takePendingAnalysisFile } from "./lib/pending-upload";
export {
  getPipelineCvInputs,
  handoffCvToJobMatching,
  persistCvDataForPipeline,
  saveWorkflowCvFromInputs,
} from "./lib/pipeline-cv";
export type { DraftAnalysisInputs } from "./lib/draft-for-analysis";
export { useAnalyzeCvAsync, useAnalyzeCvUpload } from "./hooks/use-analyze-cv";
export type {
  CvAnalysisResult,
  SectionCritique,
  KeywordCoverage,
  AnalyzeCvInput,
  AnalysisJobResponse,
} from "./types";
