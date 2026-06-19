import { useMemo } from "react";
import { EXAMPLE_STUDENT_CV } from "@/features/cv-editor/data/cv-templates";
import type { TemplateId } from "@/features/cv-editor/data/cv-templates";
import { buildHtml } from "@/features/cv-editor/lib/cv-print";

type Props = {
  templateId: TemplateId;
  title: string;
};

/** Scaled iframe preview — same HTML as export, filled with sample CV data. */
export function TemplateLivePreview({ templateId, title }: Props) {
  const html = useMemo(() => buildHtml(EXAMPLE_STUDENT_CV, templateId), [templateId]);

  return (
    <div className="template-live-preview" aria-hidden>
      <iframe title={title} srcDoc={html} tabIndex={-1} />
    </div>
  );
}
