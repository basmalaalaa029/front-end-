/** CV creation: templates, editor, AI generation, PDF export. */
export { default as CvEditorPage } from "./components/cv-editor-page";
export { default as CvTemplatePickerPage } from "./components/cv-template-picker-page";
export { CvWizardPage } from "./components/cv-wizard";
export { useCvGenerationStore, useCvDraftStore } from "./stores";
export type { GenStage } from "./stores";
export {
  startGeneration,
  waitForCompletion,
  getResult,
  getStatus,
  fetchPdfBlob,
  saveBlobAsFile,
  downloadDirectPdf,
  CV_AGENT_BASE,
  CvAgentApiError,
} from "./lib/cv-agent-api";
export type {
  CvAgentGenerateRequest,
  CvAgentResult,
  CvAgentScores,
  CvAgentSessionStatus,
} from "./lib/cv-agent-api";
export {
  printCvWithTemplate,
  printMarkdownWithTemplate,
  buildHtml,
  buildHtmlFromMarkdown,
} from "./lib/cv-print";
export { buildGeneratePayload } from "./lib/cv-to-profile";
export {
  useGenerateCv,
  useCvStatus,
  useCvResult,
  useWaitForCvCompletion,
} from "./hooks/use-cv-generation";
export type { CvData, CvExperience, CvProfileJson } from "./data/cv-types";
export { cvDataFromProfileJson } from "./data/cv-profile-import";
export { migrateCvData } from "./data/cv-data-migrate";
export {
  TEMPLATE_IDS,
  createStarterCvData,
  EXAMPLE_STUDENT_CV,
  isTemplateId,
  type TemplateId,
} from "./data/cv-templates";
