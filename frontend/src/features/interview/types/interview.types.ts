export interface InterviewQuestion {
  id: string;
  text: string;
  category: string;
}

export interface StartInterviewRequest {
  cvText: string;
  targetRole?: string;
  company?: string;
}

export interface StartInterviewResponse {
  session_id: string;
  status: string;
  questions: InterviewQuestion[];
  message: string;
}

export interface AnswerScore {
  clarity: number;
  structure: number;
  relevance: number;
  overall: number;
  feedback: string;
}

export interface SubmitAnswerRequest {
  questionId: string;
  answer: string;
}

export interface SubmitAnswerResponse {
  session_id: string;
  question_id: string;
  score: AnswerScore;
  next_question?: InterviewQuestion | null;
}

export interface EvaluationResult {
  session_id: string;
  status: string;
  overall_score: number;
  answers_scored: number;
  strengths: string[];
  improvements: string[];
  per_answer: AnswerScore[];
}

export interface InterviewSession {
  session_id: string;
  status: string;
  target_role: string;
  company: string;
  questions: InterviewQuestion[];
  answers_count: number;
  current_question?: InterviewQuestion | null;
}
