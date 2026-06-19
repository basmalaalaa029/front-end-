import { useEffect, useState } from "react";
import { useI18n } from "@/features/i18n";
import { generateAiCv } from "@/features/cv-editor/lib/wizard-api";
import type { GeneratedCv, WizardStep1Data } from "./types";

type Props = {
  data: WizardStep1Data;
  onComplete: (cv: GeneratedCv) => void;
  onError: (message: string) => void;
};

export function Step2Generating({ data, onComplete, onError }: Props) {
  const { t } = useI18n();
  const [stage, setStage] = useState(0);

  const stages = [
    t("cvEditor.wizard.stage.reading"),
    t("cvEditor.wizard.stage.extracting"),
    t("cvEditor.wizard.stage.summary"),
    t("cvEditor.wizard.stage.ats"),
    t("cvEditor.wizard.stage.finalizing"),
  ];

  useEffect(() => {
    const stageInterval = window.setInterval(() => {
      setStage((prev) => Math.min(prev + 1, stages.length - 1));
    }, 1500);

    const ctrl = new AbortController();

    const run = async () => {
      try {
        const result = await generateAiCv(data, ctrl.signal);
        window.clearInterval(stageInterval);

        if (result.status === "success") {
          setStage(stages.length - 1);
          window.setTimeout(() => onComplete(result.cv), 500);
        } else {
          onError(result.message || t("cvEditor.wizard.generationFailed"));
        }
      } catch {
        window.clearInterval(stageInterval);
        if (!ctrl.signal.aborted) {
          onError(t("cvEditor.wizard.generationFailed"));
        }
      }
    };

    void run();

    return () => {
      ctrl.abort();
      window.clearInterval(stageInterval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per wizard submission
  }, []);

  return (
    <div className="wizard-step generating">
      <div className="spinner" aria-hidden />
      <h2>{t("cvEditor.wizard.step2Title")}</h2>
      <p className="stage-text">{stages[stage]}</p>
      <div className="progress-bar" role="progressbar" aria-valuenow={stage + 1} aria-valuemin={1} aria-valuemax={stages.length}>
        <div
          className="progress-fill"
          style={{ width: `${((stage + 1) / stages.length) * 100}%` }}
        />
      </div>
    </div>
  );
}
