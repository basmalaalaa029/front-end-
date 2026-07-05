import mongoose from "mongoose";

const wizardEducationSchema = new mongoose.Schema(
  {
    degree: { type: String, default: "" },
    university: { type: String, default: "" },
    year: { type: String, default: "" },
    gpa: { type: String, default: "" },
  },
  { _id: false },
);

const wizardExperienceSchema = new mongoose.Schema(
  {
    job_title: { type: String, default: "" },
    company: { type: String, default: "" },
    start_date: { type: String, default: "" },
    end_date: { type: String, default: "" },
    description: { type: String, default: "" },
  },
  { _id: false },
);

const wizardProjectSchema = new mongoose.Schema(
  {
    name: { type: String, default: "" },
    tech_used: { type: String, default: "" },
    description: { type: String, default: "" },
  },
  { _id: false },
);

const wizardProfileSchema = new mongoose.Schema(
  {
    full_name: { type: String, default: "" },
    target_job: { type: String, default: "" },
    email: { type: String, default: "" },
    phone: { type: String, default: "" },
    location: { type: String, default: "" },
    linkedin: { type: String, default: "" },
    github: { type: String, default: "" },
    education: { type: [wizardEducationSchema], default: [] },
    experience: { type: [wizardExperienceSchema], default: [] },
    has_experience: { type: Boolean, default: true },
    projects: { type: [wizardProjectSchema], default: [] },
    certifications: { type: [String], default: [] },
  },
  { _id: false },
);

const userSchema = new mongoose.Schema(
  {
    name: { type: String, required: true, trim: true },
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    password: { type: String, default: null },
    googleId: { type: String, default: null, sparse: true },
    linkedinId: { type: String, default: null, sparse: true },
    phone: { type: String, default: "" },
    location: { type: String, default: "" },
    bio: { type: String, default: "" },
    jobTitle: { type: String, default: "" },
    avatarUrl: { type: String, default: "" },
    skills: { type: [String], default: [] },
    linkedIn: { type: String, default: "" },
    portfolio: { type: String, default: "" },
    wizardProfile: { type: wizardProfileSchema, default: null },
  },
  { timestamps: true }
);

userSchema.methods.toProfile = function toProfile() {
  return {
    _id: String(this._id),
    name: this.name,
    email: this.email,
    phone: this.phone,
    location: this.location,
    bio: this.bio,
    jobTitle: this.jobTitle,
    avatarUrl: this.avatarUrl,
    skills: this.skills,
    linkedIn: this.linkedIn,
    portfolio: this.portfolio,
  };
};

userSchema.methods.toAuthPayload = function toAuthPayload(token) {
  return {
    token,
    _id: String(this._id),
    name: this.name,
    email: this.email,
  };
};

export const User = mongoose.model("User", userSchema);
