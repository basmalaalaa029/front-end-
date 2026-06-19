/** Interview practice simulator UI. */
export { default as InterviewPage } from "./components/interview-page";
export {
  useStartInterview,
  useSubmitInterviewAnswer,
  useEvaluateInterview,
  useInterviewSession,
} from "./hooks/use-interview";
export type { InterviewQuestion, EvaluationResult, AnswerScore } from "./types";
