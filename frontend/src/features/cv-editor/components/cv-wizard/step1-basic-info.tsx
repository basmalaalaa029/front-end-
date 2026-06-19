import { useState, type ChangeEvent } from "react";
import { useI18n } from "@/features/i18n";
import { HubIcon } from "@/features/hub-shell";
import {
  createEmptyWizardStep1,
  type WizardStep1Data,
} from "./types";

type Props = {
  onNext: (data: WizardStep1Data) => void;
};

export function Step1BasicInfo({ onNext }: Props) {
  const { t } = useI18n();
  const [data, setData] = useState<WizardStep1Data>(createEmptyWizardStep1);

  const updatePersonal =
    (field: keyof Pick<WizardStep1Data, "full_name" | "target_job" | "email" | "phone" | "location" | "linkedin" | "github">) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      setData((prev) => ({ ...prev, [field]: e.target.value }));
    };

  const updateEducation =
    (index: number, field: keyof WizardStep1Data["education"][number]) =>
    (e: ChangeEvent<HTMLInputElement>) => {
      setData((prev) => {
        const updated = [...prev.education];
        updated[index] = { ...updated[index], [field]: e.target.value };
        return { ...prev, education: updated };
      });
    };

  const updateExperience =
    (index: number, field: keyof WizardStep1Data["experience"][number]) =>
    (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      setData((prev) => {
        const updated = [...prev.experience];
        updated[index] = { ...updated[index], [field]: e.target.value };
        return { ...prev, experience: updated };
      });
    };

  const addEducation = () => {
    setData((prev) => ({
      ...prev,
      education: [...prev.education, { degree: "", university: "", year: "", gpa: "" }],
    }));
  };

  const removeEducation = (index: number) => {
    setData((prev) => ({
      ...prev,
      education: prev.education.filter((_, i) => i !== index),
    }));
  };

  const addExperience = () => {
    setData((prev) => ({
      ...prev,
      experience: [
        ...prev.experience,
        {
          job_title: "",
          company: "",
          start_date: "",
          end_date: "",
          description: "",
        },
      ],
    }));
  };

  const removeExperience = (index: number) => {
    setData((prev) => ({
      ...prev,
      experience: prev.experience.filter((_, i) => i !== index),
    }));
  };

  const toggleNoExperience = () => {
    setData((prev) => {
      const nextHasExp = !prev.has_experience;
      return {
        ...prev,
        has_experience: nextHasExp,
        experience: nextHasExp
          ? prev.experience.length
            ? prev.experience
            : [
                {
                  job_title: "",
                  company: "",
                  start_date: "",
                  end_date: "",
                  description: "",
                },
              ]
          : [],
      };
    });
  };

  const canContinue =
    data.full_name.trim() &&
    data.target_job.trim() &&
    data.education[0]?.degree.trim() &&
    (!data.has_experience || data.experience[0]?.job_title.trim());

  return (
    <div className="wizard-step">
      <h2>{t("cvEditor.wizard.step1Title")}</h2>
      <p className="step-subtitle">{t("cvEditor.wizard.step1Subtitle")}</p>

      <section className="form-section">
        <h3>
          <HubIcon name="user" size={16} stroke={2} />
          {t("cvEditor.wizard.personalInfo")}
        </h3>
        <div className="form-row">
          <input
            placeholder={t("cvEditor.fields.name")}
            value={data.full_name}
            onChange={updatePersonal("full_name")}
          />
          <input
            placeholder={t("cvEditor.wizard.targetJobPlaceholder")}
            value={data.target_job}
            onChange={updatePersonal("target_job")}
          />
        </div>
        <div className="form-row">
          <input
            placeholder={t("cvEditor.fields.email")}
            value={data.email}
            onChange={updatePersonal("email")}
          />
          <input
            placeholder={t("cvEditor.fields.phone")}
            value={data.phone}
            onChange={updatePersonal("phone")}
          />
          <input
            placeholder={t("cvEditor.fields.address")}
            value={data.location}
            onChange={updatePersonal("location")}
          />
        </div>
        <div className="form-row">
          <input
            placeholder={t("cvEditor.wizard.linkedinOptional")}
            value={data.linkedin}
            onChange={updatePersonal("linkedin")}
          />
          <input
            placeholder={t("cvEditor.wizard.githubOptional")}
            value={data.github}
            onChange={updatePersonal("github")}
          />
        </div>
      </section>

      <section className="form-section">
        <h3>
          <HubIcon name="graduation-cap" size={16} stroke={2} />
          {t("cvEditor.sections.education")}
        </h3>
        {data.education.map((edu, i) => (
          <div className="repeatable-block" key={i}>
            <div className="form-row">
              <input
                placeholder={t("cvEditor.wizard.degreePlaceholder")}
                value={edu.degree}
                onChange={updateEducation(i, "degree")}
              />
              <input
                placeholder={t("cvEditor.fields.university")}
                value={edu.university}
                onChange={updateEducation(i, "university")}
              />
            </div>
            <div className="form-row">
              <input
                placeholder={t("cvEditor.wizard.gradYearPlaceholder")}
                value={edu.year}
                onChange={updateEducation(i, "year")}
              />
              <input
                placeholder={t("cvEditor.wizard.gpaOptional")}
                value={edu.gpa}
                onChange={updateEducation(i, "gpa")}
              />
              {data.education.length > 1 ? (
                <button
                  type="button"
                  className="icon-btn"
                  aria-label={t("cvEditor.wizard.removeDegree")}
                  onClick={() => removeEducation(i)}
                >
                  <HubIcon name="trash-2" size={16} stroke={2} />
                </button>
              ) : null}
            </div>
          </div>
        ))}
        <button type="button" className="add-btn" onClick={addEducation}>
          <HubIcon name="plus" size={14} stroke={2} />
          {t("cvEditor.wizard.addDegree")}
        </button>
      </section>

      <section className="form-section">
        <div className="section-header-row">
          <h3>
            <HubIcon name="briefcase" size={16} stroke={2} />
            {t("cvEditor.sections.experience")}
          </h3>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={!data.has_experience}
              onChange={toggleNoExperience}
            />
            {t("cvEditor.wizard.noExperience")}
          </label>
        </div>

        {data.has_experience ? (
          <>
            {data.experience.map((exp, i) => (
              <div className="repeatable-block" key={i}>
                <div className="form-row">
                  <input
                    placeholder={t("cvEditor.fields.jobTitle")}
                    value={exp.job_title}
                    onChange={updateExperience(i, "job_title")}
                  />
                  <input
                    placeholder={t("cvEditor.fields.company")}
                    value={exp.company}
                    onChange={updateExperience(i, "company")}
                  />
                </div>
                <div className="form-row">
                  <input
                    placeholder={t("cvEditor.wizard.startDatePlaceholder")}
                    value={exp.start_date}
                    onChange={updateExperience(i, "start_date")}
                  />
                  <input
                    placeholder={t("cvEditor.wizard.endDatePlaceholder")}
                    value={exp.end_date}
                    onChange={updateExperience(i, "end_date")}
                  />
                  {data.experience.length > 1 ? (
                    <button
                      type="button"
                      className="icon-btn"
                      aria-label={t("cvEditor.wizard.removeRole")}
                      onClick={() => removeExperience(i)}
                    >
                      <HubIcon name="trash-2" size={16} stroke={2} />
                    </button>
                  ) : null}
                </div>
                <textarea
                  placeholder={t("cvEditor.wizard.experienceDescPlaceholder")}
                  value={exp.description}
                  onChange={updateExperience(i, "description")}
                  rows={3}
                />
              </div>
            ))}
            <button type="button" className="add-btn" onClick={addExperience}>
              <HubIcon name="plus" size={14} stroke={2} />
              {t("cvEditor.addRole")}
            </button>
          </>
        ) : (
          <p className="hint-text">{t("cvEditor.wizard.noExperienceHint")}</p>
        )}
      </section>

      <div className="step-footer">
        <span className="hint">
          <HubIcon name="lightbulb" size={14} stroke={2} />
          {t("cvEditor.wizard.wordingHint")}
        </span>
        <button
          type="button"
          className="btn btn-primary"
          disabled={!canContinue}
          onClick={() => onNext(data)}
        >
          {t("cvEditor.wizard.continue")}
          <HubIcon name="arrow-right" size={14} stroke={2} />
        </button>
      </div>
    </div>
  );
}