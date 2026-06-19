export type WizardEducation = {
  degree: string;
  university: string;
  year: string;
  gpa: string;
};

export type WizardExperience = {
  job_title: string;
  company: string;
  start_date: string;
  end_date: string;
  description: string;
};

export type WizardStep1Data = {
  full_name: string;
  target_job: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
  education: WizardEducation[];
  experience: WizardExperience[];
  has_experience: boolean;
};

export type GeneratedCvPersonalInfo = {
  full_name?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
  portfolio?: string;
};

export type GeneratedCvExperience = {
  job_title?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
  bullets?: string[];
};

export type GeneratedCvProject = {
  name?: string;
  tech_used?: string;
  description?: string;
  bullets?: string[];
};

export type GeneratedCvEducation = {
  degree?: string;
  university?: string;
  year?: string;
  gpa?: string;
};

export type GeneratedCv = {
  personal_info: GeneratedCvPersonalInfo;
  target_title?: string;
  summary?: string;
  skills?: Record<string, string[]> | string[];
  experience?: GeneratedCvExperience[];
  projects?: GeneratedCvProject[];
  education?: GeneratedCvEducation[];
  certifications?: string[];
  languages?: string[];
};

export type GenerateAiCvResponse =
  | { status: "success"; cv: GeneratedCv }
  | { status: "error"; message: string };

export function createEmptyWizardStep1(): WizardStep1Data {
  return {
    full_name: "",
    target_job: "",
    email: "",
    phone: "",
    location: "",
    linkedin: "",
    github: "",
    education: [{ degree: "", university: "", year: "", gpa: "" }],
    experience: [
      {
        job_title: "",
        company: "",
        start_date: "",
        end_date: "",
        description: "",
      },
    ],
    has_experience: true,
  };
}
