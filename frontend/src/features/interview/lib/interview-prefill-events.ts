import type { InterviewPrefillPayload } from "@/features/interview/lib/pipeline-interview-prefill";

const PREFILL_EVENT = "careerpilot:interview-prefill";

export function dispatchInterviewPrefill(prefill: InterviewPrefillPayload): void {
  window.dispatchEvent(new CustomEvent(PREFILL_EVENT, { detail: prefill }));
}

export function subscribeInterviewPrefill(
  handler: (prefill: InterviewPrefillPayload) => void,
): () => void {
  const listener = (event: Event) => {
    const detail = (event as CustomEvent<InterviewPrefillPayload>).detail;
    if (detail) handler(detail);
  };
  window.addEventListener(PREFILL_EVENT, listener);
  return () => window.removeEventListener(PREFILL_EVENT, listener);
}

export async function remountInterviewHost(host: HTMLElement, token: string): Promise<void> {
  const { unmountInterviewApp, mountInterviewApp } = await import(
    "@/features/interview/lib/mount-interview-app"
  );
  unmountInterviewApp(host);
  await mountInterviewApp(host, token);
}
