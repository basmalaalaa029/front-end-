function InterviewerCard({ name, role, sub, time }) {
  return (
    <div className="interviewer-card">
      <div className="interviewer-av">
        EC
        <span className="live" />
      </div>
      <div className="interviewer-meta">
        <div className="role">{role}</div>
        <div className="name">{name}</div>
        <div className="sub">{sub}</div>
      </div>
      <div className="timer">
        <div className="t">{time}</div>
        <div className="l">Elapsed</div>
      </div>
    </div>
  );
}

function QuestionCard({ num, total, question, tag }) {
  return (
    <div className="question-card">
      <div className="question-num">Question {num} of {total}</div>
      <div className="question-text">{question}</div>
      <span className="question-tag"><Icon name="tag" size={11} stroke={2} />{tag}</span>
    </div>
  );
}

function Transcript({ entries }) {
  return (
    <div className="transcript">
      {entries.map((e, i) => (
        <div key={i} className={"bubble " + e.who}>
          <div className={"who " + e.who}>{e.who === "ai" ? "AI" : "You"}</div>
          <div className="text">{e.text}</div>
        </div>
      ))}
    </div>
  );
}

function MicBar({ listening }) {
  const bars = Array.from({ length: 36 });
  return (
    <div className="mic-bar">
      <button className="mic-btn"><Icon name={listening ? "square" : "mic"} size={18} stroke={2} /></button>
      <div className="waveform">
        {bars.map((_, i) => (
          <i key={i} style={{ animationDelay: `${(i % 9) * 0.1}s`, opacity: listening ? 1 : 0.3 }} />
        ))}
      </div>
      <div className="mic-meta">{listening ? "Listening · 00:42" : "Press to speak"}</div>
      <button className="btn btn-ghost"><Icon name="keyboard" size={14} stroke={2} />Type instead</button>
      <button className="btn btn-secondary">Skip</button>
    </div>
  );
}

function FeedbackPanel() {
  const metrics = [
    { label: "Clarity",       pct: 88 },
    { label: "Specificity",   pct: 72 },
    { label: "Pacing",        pct: 91 },
    { label: "Confidence",    pct: 79 },
    { label: "Filler words",  pct: 64 },
  ];
  return (
    <>
      <div className="feedback-section">
        <h4>Live feedback</h4>
        {metrics.map(m => (
          <div key={m.label} className="metric-row">
            <span className="label">{m.label}</span>
            <span className="bar"><i style={{ width: m.pct + "%" }} /></span>
            <span className="pct">{m.pct}</span>
          </div>
        ))}
      </div>
      <div className="feedback-section">
        <h4>Coach</h4>
        <div className="coaching">
          <div className="label"><Icon name="sparkles" size={11} stroke={2} />Suggestion</div>
          <div className="body">Your answer leads with context. Try the STAR pattern — situation, task, action, result — and put the metric in the last sentence.</div>
        </div>
        <div className="coaching" style={{ background: "var(--clay-50)", borderColor: "var(--clay-200)" }}>
          <div className="label" style={{ color: "var(--clay-700)" }}><Icon name="alert-triangle" size={11} stroke={2} />Watch out</div>
          <div className="body">You said "kind of" three times in the last answer. Replace with the specific verb.</div>
        </div>
      </div>
      <div className="feedback-section">
        <h4>Session</h4>
        <div className="metric-row"><span className="label">Questions answered</span><span className="pct">3 / 8</span></div>
        <div className="metric-row"><span className="label">Average score</span><span className="pct">82</span></div>
        <div className="metric-row"><span className="label">Role</span><span className="pct">PD · Stripe</span></div>
      </div>
    </>
  );
}

Object.assign(window, { InterviewerCard, QuestionCard, Transcript, MicBar, FeedbackPanel });
