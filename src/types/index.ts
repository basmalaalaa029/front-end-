export interface User {
  _id: string;
  name: string;
  email: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export interface Experience {
  id?: string;
  company: string;
  role: string;
  duration: string;
  description: string;
}

export interface Education {
  id?: string;
  institution: string;
  degree: string;
  year: string;
}

export interface Skill {
  id?: string;
  name: string;
  level: string;
}

export interface Language {
  id?: string;
  name: string;
  proficiency: string;
}

export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  summary: string;
  address?: string;
  linkedin?: string;
  github?: string;
}

export interface CVData {
  personalInfo: PersonalInfo;
  experiences: Experience[];
  education: Education[];
  skills: Skill[];
  languages: Language[];
}

export interface AnalyzeResult {
  score: number;
  suggestions: string[];
  missingKeywords: string[];
}

export interface MatchResult {
  matchScore: number;
  overlapTerms: string[];
  missingInCV: string[];
}
