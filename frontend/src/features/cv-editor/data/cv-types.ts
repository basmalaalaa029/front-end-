export type CvExperience = {
  title: string;
  company: string;
  location: string;
  dates: string;
  bullets: string[];
};

export type CvEducation = {
  degree: string;
  university: string;
  startDate: string;
  endDate: string;
  gpa: string;
};

export type CvProject = {
  title: string;
  description: string;
  bullets?: string[];
};

/** Matches common profile JSON (name, email, phone, address, education, skills, projects, certifications). */
export type CvProfileJson = {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  summary?: string;
  role?: string;
  url?: string;
  education?: Array<{
    degree?: string;
    university?: string;
    school?: string;
    startDate?: string;
    endDate?: string;
    gpa?: string;
    dates?: string;
  }>;
  skills?: string[];
  experience?: CvExperience[];
  projects?: Array<{ title?: string; name?: string; description?: string }>;
  certifications?: string[];
};

export type CvData = {
  name: string;
  email: string;
  phone: string;
  address: string;
  /** Optional headline under your name (e.g. "Computer Science Student"). */
  role: string;
  url: string;
  summary: string;
  education: CvEducation[];
  skills: string[];
  skillsByCategory?: Record<string, string[]>;
  experience: CvExperience[];
  projects: CvProject[];
  certifications: string[];
};
