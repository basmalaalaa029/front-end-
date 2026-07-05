import { useCallback, useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";
import { useI18n } from "@/features/i18n";
import {
  rewriteCvSection,
  type RewriteSectionKind,
} from "@/features/cv-editor/lib/section-rewrite-api";

const DEBOUNCE_MS = 2500;

type RewritePayload = {
  section: RewriteSectionKind;
  key: string;
  targetRole: string;
  summary?: string;
  jobTitle?: string;
  company?: string;
  bullets?: string[];
  skills?: string[];
  education?: string[];
};

function contentSignature(payload: RewritePayload): string {
  if (payload.section === "summary") return payload.summary?.trim() ?? "";
  if (payload.section === "experience") {
    return [payload.jobTitle, payload.company, ...(payload.bullets ?? [])].join("\n").trim();
  }
  return (payload.skills ?? []).join(",").trim();
}

function meetsMinimum(payload: RewritePayload): boolean {
  if (payload.section === "summary") {
    return (payload.summary?.trim().length ?? 0) >= 10;
  }
  if (payload.section === "experience") {
    const bullets = (payload.bullets ?? []).map((b) => b.trim()).filter(Boolean);
    return bullets.length > 0 && bullets.join(" ").length >= 8;
  }
  return (payload.skills ?? []).filter((s) => s.trim()).length >= 1;
}

export function useAtsSectionRewrite(
  onApply: (result: {
    section: RewriteSectionKind;
    key: string;
    summary?: string;
    bullets?: string[];
    skills?: string[];
    skillsByCategory?: Record<string, string[]>;
  }) => void,
) {
  const { t } = useI18n();
  const [rewritingKey, setRewritingKey] = useState<string | null>(null);
  const lastAppliedRef = useRef<Record<string, string>>({});
  const pendingRef = useRef<RewritePayload | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runRewrite = useCallback(
    async (payload: RewritePayload) => {
      if (!meetsMinimum(payload)) return;

      const signature = contentSignature(payload);
      if (!signature || lastAppliedRef.current[payload.key] === signature) return;

      abortRef.current?.abort();
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      setRewritingKey(payload.key);

      try {
        const res = await rewriteCvSection(
          {
            section: payload.section,
            target_role: payload.targetRole || undefined,
            summary: payload.summary,
            job_title: payload.jobTitle,
            company: payload.company,
            bullets: payload.bullets,
            skills: payload.skills,
            education: payload.education,
          },
          ctrl.signal,
        );

        if (ctrl.signal.aborted) return;

        onApply({
          section: res.section,
          key: payload.key,
          summary: res.summary,
          bullets: res.bullets,
          skills: res.skills,
          skillsByCategory: res.skills_by_category,
        });

        let appliedSignature = signature;
        if (res.section === "summary" && res.summary) {
          appliedSignature = res.summary.trim();
        } else if (res.section === "experience" && res.bullets?.length) {
          appliedSignature = [payload.jobTitle, payload.company, ...res.bullets].join("\n").trim();
        } else if (res.section === "skills" && res.skills?.length) {
          appliedSignature = res.skills.join(",").trim();
        }
        lastAppliedRef.current[payload.key] = appliedSignature;
      } catch (err) {
        if ((err as DOMException)?.name === "AbortError") return;
        console.error("[ATS rewrite]", err);
        toast.error(t("cvEditor.atsRewrite.failed"));
      } finally {
        if (!ctrl.signal.aborted) {
          setRewritingKey((k) => (k === payload.key ? null : k));
        }
      }
    },
    [onApply, t],
  );

  const scheduleRewrite = useCallback(
    (payload: RewritePayload) => {
      pendingRef.current = payload;
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        const p = pendingRef.current;
        if (p) void runRewrite(p);
      }, DEBOUNCE_MS);
    },
    [runRewrite],
  );

  const rewriteNow = useCallback(
    (payload: RewritePayload) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      void runRewrite(payload);
    },
    [runRewrite],
  );

  useEffect(
    () => () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      abortRef.current?.abort();
    },
    [],
  );

  return { scheduleRewrite, rewriteNow, rewritingKey, isRewriting: rewritingKey !== null };
}
