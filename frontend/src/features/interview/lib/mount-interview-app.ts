import { CV_AGENT_BASE } from "@/shared/lib/cv-agent-client";
import { applyInterviewWorkflowPrefill } from "@/features/interview/lib/pipeline-interview-prefill";

const STYLE_ID = "career-interview-app-styles";
const THEME_LINK_ID = "career-interview-app-theme";
const AUTH_SCRIPT_ID = "career-interview-auth-bridge";

declare global {
  interface Window {
    __CV_INTERVIEW_CONFIG__?: {
      token: string;
      api: string;
      embedded?: boolean;
    };
    __CV_INTERVIEW_INSTALL_AUTH__?: () => void;
    __CV_INTERVIEW_AUTH_UNINSTALL__?: () => void;
  }
}

/** Bumped on unmount so in-flight mount work is ignored. */
let mountGeneration = 0;

function loadScriptOnce(id: string, src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    if (document.getElementById(id)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.id = id;
    script.src = src;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(script);
  });
}

function ensureStyles(doc: Document): void {
  if (!document.getElementById(STYLE_ID)) {
    doc.querySelectorAll("style").forEach((style) => {
      const el = document.createElement("style");
      el.id = STYLE_ID;
      el.textContent = style.textContent;
      document.head.appendChild(el);
    });
  }

  if (!document.getElementById(THEME_LINK_ID)) {
    const link = document.createElement("link");
    link.id = THEME_LINK_ID;
    link.rel = "stylesheet";
    link.href = "/interview/career-pilot-theme.css";
    document.head.appendChild(link);
  }

  const fontHref = doc.querySelector('link[href*="fonts.googleapis"]')?.getAttribute("href");
  if (fontHref && !document.querySelector(`link[href="${fontHref}"]`)) {
    const fontLink = document.createElement("link");
    fontLink.rel = "stylesheet";
    fontLink.href = fontHref;
    document.head.appendChild(fontLink);
  }
}

function mountBodyHtml(doc: Document): string {
  return Array.from(doc.body.children)
    .filter((node) => node.tagName !== "SCRIPT")
    .map((node) => (node as HTMLElement).outerHTML)
    .join("");
}

async function runScripts(doc: Document, host: HTMLElement, generation: number): Promise<void> {
  for (const script of Array.from(doc.querySelectorAll("script"))) {
    if (generation !== mountGeneration) return;

    const src = script.getAttribute("src");
    if (src) {
      if (src.includes("auth-bridge")) continue;
      const resolved = src.startsWith("/")
        ? src
        : `/interview/${src.replace(/^\.\//, "")}`;
      await loadScriptOnce(`career-interview-${resolved}`, resolved);
      continue;
    }

    const code = script.textContent?.trim();
    if (!code) continue;
    if (code.includes("embedded") && code.length < 220) continue;

    const inline = document.createElement("script");
    inline.textContent = code;
    host.appendChild(inline);
  }
}

function installAuthBridge(token: string): void {
  window.__CV_INTERVIEW_CONFIG__ = {
    token,
    api: CV_AGENT_BASE,
    embedded: true,
  };
  if (window.__CV_INTERVIEW_INSTALL_AUTH__) {
    window.__CV_INTERVIEW_INSTALL_AUTH__();
  }
}

export async function mountInterviewApp(
  host: HTMLElement,
  token: string,
): Promise<void> {
  const generation = ++mountGeneration;
  host.classList.add("interview-app-host", "embedded");
  host.innerHTML = "";

  installAuthBridge(token);
  await loadScriptOnce(AUTH_SCRIPT_ID, "/interview/auth-bridge.js");
  installAuthBridge(token);

  if (generation !== mountGeneration) return;

  const res = await fetch("/interview/index.html");
  if (!res.ok) {
    throw new Error("Could not load interview UI");
  }

  if (generation !== mountGeneration) return;

  const html = await res.text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  ensureStyles(doc);
  host.innerHTML = mountBodyHtml(doc);

  if (generation !== mountGeneration) return;

  await runScripts(doc, host, generation);

  if (generation !== mountGeneration) return;

  await applyInterviewWorkflowPrefill(host);

  if (generation === mountGeneration) {
    host.dataset.mounted = "1";
  }
}

export function unmountInterviewApp(host: HTMLElement): void {
  mountGeneration += 1;
  window.__CV_INTERVIEW_AUTH_UNINSTALL__?.();
  delete window.__CV_INTERVIEW_CONFIG__;
  delete host.dataset.mounted;
  host.innerHTML = "";
  host.classList.remove("interview-app-host", "embedded");
}
