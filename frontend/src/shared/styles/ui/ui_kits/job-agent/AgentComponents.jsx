function JobCard({ job, selected, onClick }) {
  const matchCls = job.match >= 80 ? "strong" : job.match >= 60 ? "medium" : "weak";
  return (
    <div className={"job-card " + (selected ? "selected" : "")} onClick={onClick}>
      <div className="job-row">
        <div className={"job-logo " + job.brand}>{job.logo}</div>
        <div className="job-body">
          <div className="job-title">{job.title}</div>
          <div className="job-meta">
            <span><Icon name="building-2" size={12} stroke={2} />{job.company}</span>
            <span><Icon name="map-pin" size={12} stroke={2} />{job.location}</span>
            <span><Icon name="dollar-sign" size={12} stroke={2} />{job.salary}</span>
          </div>
        </div>
        <span className={"match-pill " + matchCls}>{job.match}% match</span>
      </div>
      <div className="job-why">
        <Icon name="sparkles" size={13} stroke={2} className="ai" />
        <span>{job.why}</span>
      </div>
    </div>
  );
}

function AgentDrawer() {
  const tasks = [
    { state: "done",    icon: "check-circle-2", label: "Pulled 47 roles from LinkedIn, Wellfound, Otta",  when: "8m ago" },
    { state: "done",    icon: "check-circle-2", label: "Filtered against your preferences",              when: "7m ago" },
    { state: "done",    icon: "check-circle-2", label: "Scored each role on your CV + JD overlap",       when: "6m ago" },
    { state: "active",  icon: "loader-2",       label: "Drafting tailored cover letters for top 3",      when: "now" },
    { state: "pending", icon: "circle",         label: "Schedule follow-ups for replies",                when: "—" },
  ];
  return (
    <div className="agent-drawer">
      <div className="drawer-head">
        <span className="pulse" />
        <h3>Agent activity</h3>
      </div>
      {tasks.map((t, i) => (
        <div key={i} className={"task " + t.state}>
          <Icon name={t.icon} size={14} stroke={2} className="ico" />
          <span className="label">{t.label}</span>
          <span className="when">{t.when}</span>
        </div>
      ))}
    </div>
  );
}

function ContextPanel({ job }) {
  if (!job) return null;
  return (
    <>
      <AgentDrawer />
      <div className="context-section">
        <h4>Selected role</h4>
        <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 2 }}>{job.title}</div>
        <div style={{ fontSize: 13, color: "var(--fg-secondary)" }}>{job.company} · {job.location}</div>
      </div>
      <div className="context-section">
        <h4>Why we matched you</h4>
        <p style={{ fontSize: 13, color: "var(--fg-primary)", lineHeight: 1.55, margin: 0 }}>{job.why}</p>
      </div>
      <div className="context-section">
        <h4>Match breakdown</h4>
        <div className="kv"><span className="k">Skills overlap</span><span className="v">92%</span></div>
        <div className="kv"><span className="k">Years of experience</span><span className="v">Match</span></div>
        <div className="kv"><span className="k">Compensation band</span><span className="v">Within range</span></div>
        <div className="kv"><span className="k">Location</span><span className="v">Remote OK</span></div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-accent" style={{ flex: 1, justifyContent: "center" }}><Icon name="send" size={14} stroke={2} />Apply now</button>
        <button className="btn btn-secondary"><Icon name="bookmark" size={14} stroke={2} /></button>
      </div>
    </>
  );
}

Object.assign(window, { JobCard, AgentDrawer, ContextPanel });
