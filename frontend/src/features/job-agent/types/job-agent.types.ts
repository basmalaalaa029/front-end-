export interface ScoreBreakdown {
  semantic?: number;
  hard_skills?: number;
  seniority?: number;
  role_title?: number;
  soft_certs?: number;
}

export interface MatchedJob {
  id: string;
  brand: string;
  logo: string;
  title: string;
  company: string;
  location: string;
  salary: string;
  match_score: number;
  why: string;
  source?: string;
  url?: string;
  posted?: string;
  score_breakdown?: ScoreBreakdown;
  tags?: string[];
  matched_skills?: string[];
  missing_skills?: string[];
}

export interface JobMatchRequest {
  cvText: string;
  targetRole?: string;
  location?: string;
}

export interface JobMatchResponse {
  session_id: string;
  status: string;
  total_jobs: number;
  message: string;
}

export interface JobMatchResults {
  session_id: string;
  status: string;
  jobs: MatchedJob[];
  target_role: string;
  latency_ms: number;
}
