import type { CvData } from "./cv-types";
import { cvDataFromProfileJson } from "./cv-profile-import";

export const TEMPLATE_IDS = ["modern", "executive", "tech", "minimal"] as const;
export type TemplateId = (typeof TEMPLATE_IDS)[number];

export function isTemplateId(value: string): value is TemplateId {
  return (TEMPLATE_IDS as readonly string[]).includes(value);
}

/** Empty starter — same fields as profile JSON. */
export function createStarterCvData(): CvData {
  return cvDataFromProfileJson({
    name: "",
    email: "",
    phone: "",
    address: "",
    summary: "",
    education: [
      {
        degree: "",
        university: "",
        startDate: "",
        endDate: "",
        gpa: "",
      },
    ],
    skills: [],
    experience: [],
    projects: [],
    certifications: [],
  });
}

/** Example student profile for demos / testing. */
export const EXAMPLE_STUDENT_CV = cvDataFromProfileJson({
  name: "Ahmed Mohamed",
  email: "ahmed.mohamed@gmail.com",
  phone: "+20 100 123 4567",
  address: "Cairo, Egypt",
  summary: "Computer Science student passionate about web development and AI.",
  role: "Computer Science Student",
  education: [
    {
      degree: "BSc Computer Science",
      university: "Cairo University",
      startDate: "2022",
      endDate: "2026",
      gpa: "3.7",
    },
  ],
  skills: ["Python", "Java", "HTML", "CSS", "JavaScript", "SQL"],
  experience: [],
  projects: [
    {
      title: "CV Builder",
      description: "Developed a web application for creating and exporting professional resumes.",
    },
    {
      title: "Student Portal",
      description: "Created a university portal using Java and MySQL.",
    },
  ],
  certifications: ["Python for Everybody"],
});
