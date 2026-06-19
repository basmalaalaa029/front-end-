import mongoose from "mongoose";

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
