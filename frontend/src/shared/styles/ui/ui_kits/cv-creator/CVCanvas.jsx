function CVCanvas({ data, highlightedBullet }) {
  return (
    <div className="cv-canvas">
      <div className="cv-name">{data.name}</div>
      <div className="cv-role">{data.role}</div>
      <div className="cv-contact">
        <span>{data.email}</span>
        <span>·</span>
        <span>{data.location}</span>
        <span>·</span>
        <span>{data.url}</span>
      </div>

      <div className="cv-section">
        <h3>Summary</h3>
        <p style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--fg-primary)", margin: 0 }}>{data.summary}</p>
      </div>

      <div className="cv-section">
        <h3>Experience</h3>
        {data.experience.map((e, i) => (
          <div className="cv-entry" key={i}>
            <div className="cv-entry-head">
              <span className="cv-entry-title">{e.title}</span>
              <span className="cv-entry-meta">{e.dates}</span>
            </div>
            <div className="cv-entry-sub">{e.company} · {e.location}</div>
            <ul>
              {e.bullets.map((b, j) => (
                <li key={j} className={highlightedBullet === `${i}-${j}` ? "ai-suggested" : ""}>{b}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="cv-section">
        <h3>Education</h3>
        {data.education.map((e, i) => (
          <div className="cv-entry" key={i}>
            <div className="cv-entry-head">
              <span className="cv-entry-title">{e.school}</span>
              <span className="cv-entry-meta">{e.dates}</span>
            </div>
            <div className="cv-entry-sub">{e.degree}</div>
          </div>
        ))}
      </div>

      <div className="cv-section">
        <h3>Skills</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
          {data.skills.map(s => (
            <span key={s} style={{ fontSize: 12, padding: "3px 10px", borderRadius: 999, background: "var(--bone-100)", color: "var(--fg-secondary)" }}>{s}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function SectionsPanel({ active, onPick }) {
  const sections = [
    { id: "summary",    icon: "align-left",  label: "Summary" },
    { id: "experience", icon: "briefcase",   label: "Experience" },
    { id: "education",  icon: "graduation-cap", label: "Education" },
    { id: "skills",     icon: "wrench",      label: "Skills" },
    { id: "projects",   icon: "folder-open", label: "Projects" },
    { id: "awards",     icon: "award",       label: "Awards" },
  ];
  return (
    <div className="sections-panel">
      <h4>Sections</h4>
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {sections.map(s => (
          <div
            key={s.id}
            className={"section-block " + (active === s.id ? "is-active" : "")}
            onClick={() => onPick(s.id)}
          >
            <Icon name="grip-vertical" size={14} className="grip" />
            <Icon name={s.icon} size={15} />
            <span>{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function AIRail({ score, onApply }) {
  const suggestions = [
    {
      label: "Sharpen your summary",
      body: "Lead with measurable outcomes — try \"Shipped 14 features that cut onboarding time 38%.\"",
      target: "summary",
    },
    {
      label: "Add a metric to bullet 1",
      body: "\"Led design for checkout\" reads vague. Pair it with the conversion delta you mentioned in onboarding.",
      target: "0-0",
    },
    {
      label: "Stronger verb",
      body: "Swap \"helped with\" for \"owned\" or \"shipped\" — recruiters skim for ownership signals.",
      target: "0-1",
    },
  ];
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <div className="score-card">
        <div className="score-n">{score}</div>
        <div className="score-l">Recruiter readability</div>
        <span className="score-delta">+8 this session</span>
      </div>

      <SectionsPanel active="experience" onPick={() => {}} />

      <div className="ai-rail">
        <div className="rail-head">
          <Icon name="sparkles" size={16} />
          <h3>Copilot suggestions</h3>
        </div>
        <div className="rail-sub">Calibrated against your target role</div>
        {suggestions.map((s, i) => (
          <div key={i} className="suggestion">
            <div className="label">AI suggestion</div>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{s.label}</div>
            <div className="body">{s.body}</div>
            <div className="actions">
              <button className="btn btn-primary btn-sm" onClick={() => onApply(s.target)}>Apply</button>
              <button className="btn btn-ghost btn-sm">Dismiss</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { CVCanvas, SectionsPanel, AIRail });
