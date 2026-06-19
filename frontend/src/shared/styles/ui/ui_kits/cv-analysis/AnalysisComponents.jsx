function ScoreHero({ score = 87, subscores }) {
  const R = 38, C = 2 * Math.PI * R;
  const off = C - (score / 100) * C;
  return (
    <div className="score-hero">
      <div className="score-ring">
        <svg className="ring-svg" viewBox="0 0 96 96">
          <circle className="bg" cx="48" cy="48" r={R} fill="none" strokeWidth="8" />
          <circle className="fg" cx="48" cy="48" r={R} fill="none" strokeWidth="8"
                  strokeDasharray={C} strokeDashoffset={off} />
        </svg>
        <div>
          <div className="score-num">{score}<span style={{ fontSize: 18, color: "var(--moss-300)" }}>/100</span></div>
          <div className="score-label">Match · Strong</div>
        </div>
      </div>
      <div className="score-verdict">You're a strong fit for this role. Two sections need work before this is recruiter-ready.</div>
      <div className="sub-scores">
        {subscores.map(s => (
          <div key={s.label} className="sub">
            <div className="n">{s.value}</div>
            <div className="l">{s.label}</div>
            <div className="bar"><i style={{ width: s.value + "%" }} /></div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CritCard({ section, status, summary, quote, fix }) {
  const cls = status === "pass" ? "status-pass" : status === "warn" ? "status-warn" : "status-fail";
  const lbl = status === "pass" ? "Strong" : status === "warn" ? "Needs work" : "Gap";
  return (
    <div className="crit-card">
      <div className="crit-head">
        <div className="title"><Icon name="file-text" size={16} />{section}</div>
        <span className={"status-pill " + cls}>{lbl}</span>
      </div>
      <div className="crit-body">{summary}</div>
      {quote && <div className="crit-quote">"{quote}"</div>}
      {fix && (
        <div className="crit-fix">
          <div className="label"><Icon name="sparkles" size={11} stroke={2} /> Recommended rewrite</div>
          <div style={{ color: "var(--fg-primary)" }}>{fix}</div>
        </div>
      )}
    </div>
  );
}

function GapMatrix({ rows }) {
  return (
    <div className="card" style={{ marginTop: 18 }}>
      <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border-subtle)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Keyword & skill coverage</h3>
        <span style={{ fontSize: 12, color: "var(--fg-tertiary)" }}>vs Senior Product Designer · Stripe</span>
      </div>
      <div>
        {rows.map(r => {
          const color = r.coverage >= 70 ? "var(--moss-500)" : r.coverage >= 40 ? "var(--amber-500)" : "var(--rust-500)";
          return (
            <div key={r.name} className="gap-row">
              <div className="name">{r.name}</div>
              <div className="bar"><i style={{ width: r.coverage + "%", background: color }} /></div>
              <div className="pct">{r.coverage}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, { ScoreHero, CritCard, GapMatrix });
