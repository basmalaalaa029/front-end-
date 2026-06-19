import { useState } from "react";
import { Navigate, useParams } from "react-router-dom";
import { HubIcon } from "@/features/hub-shell";
import { isTemplateId, type TemplateId } from "@/features/cv-editor/data/cv-templates";
import { generatedCvToCvData } from "@/features/cv-editor/lib/generated-cv-to-cv-data";
import type { CvData } from "@/features/cv-editor/data/cv-types";
import { Step1BasicInfo } from "./step1-basic-info";
import { Step2Generating } from "./step2-generating";
import { Step3Review } from "./step3-review";
import { WizardProgress } from "./wizard-progress";
import type { GeneratedCv, WizardStep1Data } from "./types";
import "./cv-wizard.css";
import "@ui/ui_kits/cv-creator/creator.css";

export default function CvWizardPage() {
  const { templateId } = useParams<{ templateId: string }>();
  const [step, setStep] = useState(1);
  const [basicInfo, setBasicInfo] = useState<WizardStep1Data | null>(null);
  const [generatedCv, setGeneratedCv] = useState<GeneratedCv | null>(null);
  const [cvData, setCvData] = useState<CvData | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!templateId || !isTemplateId(templateId)) {
    return <Navigate to="/dashboard/editor" replace />;
  }

  const tpl = templateId as TemplateId;

  const handleStep1Next = (data: WizardStep1Data) => {
    setBasicInfo(data);
    setError(null);
    setStep(2);
  };

  const handleGenerationComplete = (cv: GeneratedCv) => {
    const targetJob = basicInfo?.target_job ?? cv.target_title ?? "";
    const mapped = generatedCvToCvData(cv, targetJob);
    setGeneratedCv(cv);
    setCvData(mapped);
    setStep(3);
  };

  const handleGenerationError = (message: string) => {
    setError(message);
    setStep(1);
  };

  const handleRestart = () => {
    setStep(1);
    setBasicInfo(null);
    setGeneratedCv(null);
    setCvData(null);
    setError(null);
  };

  return (
    <div className={`cv-wizard${step === 3 ? " cv-wizard--review" : ""}`}>
      <WizardProgress currentStep={step} />

      {error ? (
        <div className="error-banner" role="alert">
          <HubIcon name="alert-circle" size={16} stroke={2} />
          {error}
        </div>
      ) : null}

      {step === 1 ? <Step1BasicInfo onNext={handleStep1Next} /> : null}
      {step === 2 && basicInfo ? (
        <Step2Generating
          data={basicInfo}
          onComplete={handleGenerationComplete}
          onError={handleGenerationError}
        />
      ) : null}
      {step === 3 && generatedCv && cvData ? (
        <Step3Review
          generatedCv={generatedCv}
          cvData={cvData}
          templateId={tpl}
          onRestart={handleRestart}
          onCvChange={setCvData}
        />
      ) : null}
    </div>
  );
}
