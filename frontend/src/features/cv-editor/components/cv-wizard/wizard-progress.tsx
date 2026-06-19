import { HubIcon } from "@/features/hub-shell";
import { useI18n } from "@/features/i18n";

type Props = {
  currentStep: number;
};

export function WizardProgress({ currentStep }: Props) {
  const { t } = useI18n();
  const steps = [
    t("cvEditor.wizard.steps.basic"),
    t("cvEditor.wizard.steps.generating"),
    t("cvEditor.wizard.steps.review"),
  ];

  return (
    <div className="wizard-progress" aria-label={t("cvEditor.wizard.progressLabel")}>
      {steps.map((label, i) => {
        const num = i + 1;
        const isActive = num === currentStep;
        const isDone = num < currentStep;

        return (
          <div key={label} className="progress-step">
            <div
              className={`step-circle${isActive ? " active" : ""}${isDone ? " done" : ""}`}
            >
              {isDone ? <HubIcon name="check" size={14} stroke={2.5} /> : num}
            </div>
            <span className={isActive ? "active" : ""}>{label}</span>
            {num < steps.length ? <div className="step-line" aria-hidden /> : null}
          </div>
        );
      })}
    </div>
  );
}
