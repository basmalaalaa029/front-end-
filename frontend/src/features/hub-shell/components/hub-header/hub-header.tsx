import type { ReactNode } from "react";

type HubHeaderProps = {
  title: string;
  sub?: string;
  right?: ReactNode;
};

export function HubHeader({ title, sub, right }: HubHeaderProps) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="header-title">{title}</h1>
        {sub ? <span className="header-sub">{sub}</span> : null}
      </div>
      <div className="header-right">{right}</div>
    </header>
  );
}
