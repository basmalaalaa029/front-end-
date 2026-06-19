// Start screen: pick a template OR upload an existing CV.

const TEMPLATES = [
  { id: "classic",   name: "Classic",   tag: "ats",   tagLabel: "ATS-safe", style: "classic" },
  { id: "modern",    name: "Modern",    tag: null,    tagLabel: null,       style: "modern" },
  { id: "compact",   name: "Compact",   tag: "ats",   tagLabel: "ATS-safe", style: "compact" },
  { id: "executive", name: "Executive", tag: "pro",   tagLabel: "Pro",      style: "executive" },
  { id: "academic",  name: "Academic",  tag: null,    tagLabel: null,       style: "academic" },
  { id: "creative",  name: "Creative",  tag: "pro",   tagLabel: "Pro",      style: "creative" },
];

function TplPreview({ style }) {
  // Each style is a tiny CSS-only layout abstraction of the resume.
  if (style === "classic") return (
    <div className="tpl-paper">
      <div className="sk-strong" style={{ width: "55%" }} />
      <div className="sk-line"  style={{ width: "70%" }} />
      <div className="sk-accent" style={{ width: "30%", marginTop: 6 }} />
      <div className="sk-line"  style={{ width: "92%" }} />
      <div className="sk-line"  style={{ width: "82%" }} />
      <div className="sk-accent" style={{ width: "30%", marginTop: 6 }} />
      <div className="sk-line"  style={{ width: "90%" }} />
      <div className="sk-line"  style={{ width: "76%" }} />
      <div className="sk-line"  style={{ width: "60%" }} />
    </div>
  );
  if (style === "modern") return (
    <div className="tpl-paper">
      <div className="sk-row" style={{ alignItems: "center", marginBottom: 4 }}>
        <div className="sk-dot" />
        <div className="sk-col" style={{ flex: 1, gap: 3 }}>
          <div className="sk-strong" style={{ width: "70%" }} />
          <div className="sk-line" style={{ width: "50%" }} />
        </div>
      </div>
      <div className="sk-accent" style={{ width: "30%", marginTop: 4 }} />
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "84%" }} />
      <div className="sk-row" style={{ gap: 3, marginTop: 4 }}>
        <div className="sk-line" style={{ width: 18, background: "var(--moss-200)" }} />
        <div className="sk-line" style={{ width: 22, background: "var(--moss-200)" }} />
        <div className="sk-line" style={{ width: 16, background: "var(--moss-200)" }} />
        <div className="sk-line" style={{ width: 26, background: "var(--moss-200)" }} />
      </div>
    </div>
  );
  if (style === "compact") return (
    <div className="tpl-paper" style={{ gap: 5 }}>
      <div className="sk-strong" style={{ width: "55%" }} />
      <div className="sk-line" style={{ width: "82%" }} />
      <div className="sk-row" style={{ marginTop: 4 }}>
        <div className="sk-accent" style={{ width: "22%" }} />
        <div style={{ flex: 1 }} />
      </div>
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "88%" }} />
      <div className="sk-line" style={{ width: "82%" }} />
      <div className="sk-line" style={{ width: "70%" }} />
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "85%" }} />
    </div>
  );
  if (style === "executive") return (
    <div className="tpl-paper">
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 2 }}>
        <div className="sk-strong" style={{ width: "60%", height: 10 }} />
      </div>
      <div style={{ display: "flex", justifyContent: "center" }}>
        <div className="sk-line" style={{ width: "70%" }} />
      </div>
      <div style={{ height: 1, background: "var(--bone-200)", margin: "4px 0" }} />
      <div className="sk-accent" style={{ width: "30%", margin: "0 auto" }} />
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "88%" }} />
      <div className="sk-line" style={{ width: "82%" }} />
    </div>
  );
  if (style === "academic") return (
    <div className="tpl-paper">
      <div className="sk-strong" style={{ width: "50%" }} />
      <div className="sk-line" style={{ width: "65%" }} />
      <div className="sk-accent" style={{ width: "35%", marginTop: 6 }} />
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "94%" }} />
      <div className="sk-line" style={{ width: "82%" }} />
      <div className="sk-accent" style={{ width: "28%", marginTop: 4 }} />
      <div className="sk-line" style={{ width: "92%" }} />
      <div className="sk-line" style={{ width: "78%" }} />
    </div>
  );
  // creative — two-column
  return (
    <div className="tpl-paper" style={{ flexDirection: "row", gap: 6, padding: "10px 10px" }}>
      <div className="sk-col" style={{ width: 28, background: "var(--moss-700)", borderRadius: 3, padding: 6, gap: 4 }}>
        <div className="sk-dot" style={{ background: "var(--moss-200)", width: 12, height: 12 }} />
        <div className="sk-line" style={{ background: "var(--moss-300)", width: "100%" }} />
        <div className="sk-line" style={{ background: "var(--moss-300)", width: "80%" }} />
        <div className="sk-line" style={{ background: "var(--moss-300)", width: "70%" }} />
      </div>
      <div className="sk-col" style={{ flex: 1, gap: 4 }}>
        <div className="sk-strong" style={{ width: "70%" }} />
        <div className="sk-accent" style={{ width: "40%" }} />
        <div className="sk-line" style={{ width: "94%" }} />
        <div className="sk-line" style={{ width: "82%" }} />
        <div className="sk-line" style={{ width: "92%" }} />
      </div>
    </div>
  );
}

function TemplateCard({ tpl, selected, onClick }) {
  return (
    <div className={"tpl-card " + (selected ? "is-selected" : "")} onClick={onClick}>
      <div className="tpl-preview"><TplPreview style={tpl.style} /></div>
      <div className="tpl-meta">
        <span className="name">{tpl.name}</span>
        {tpl.tag && <span className={"tag " + tpl.tag}>{tpl.tagLabel}</span>}
      </div>
    </div>
  );
}

function UploadCard({ onUpload }) {
  const [dragging, setDragging] = React.useState(false);
  const [parsing, setParsing] = React.useState(false);
  const onDrop = (e) => { e.preventDefault(); setDragging(false); setParsing(true); setTimeout(onUpload, 1400); };
  return (
    <div className="upload-card">
      <h2>Have a CV already?</h2>
      <div className="sub">Upload it and we'll extract your sections — name, experience, education, skills — automatically.</div>
      <div
        className={"dropzone " + (dragging ? "is-dragging" : "")}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => { setParsing(true); setTimeout(onUpload, 1400); }}
      >
        <div className="icon-wrap"><Icon name="upload-cloud" size={22} stroke={1.75} /></div>
        <div className="head">Drop your CV here</div>
        <div className="body">or click to browse</div>
        <div className="formats">PDF · DOCX · TXT · up to 10 MB</div>
      </div>

      {parsing && (
        <div className="parse-banner">
          <span className="pulse" />
          <div className="text"><strong>Reading your CV…</strong> Extracting sections with AI. This usually takes 4–8 seconds.</div>
        </div>
      )}

      <div className="divider-or">or import from</div>

      <div className="alt-paths">
        <button className="alt-path">
          <span className="ico"><Icon name="link-2" size={16} stroke={2} /></span>
          <span className="text">
            <span className="l">LinkedIn profile</span>
            <span className="s">Connect and pull your full work history</span>
          </span>
          <Icon name="arrow-right" size={14} stroke={2} />
        </button>
        <button className="alt-path">
          <span className="ico"><Icon name="clipboard" size={16} stroke={2} /></span>
          <span className="text">
            <span className="l">Paste plain text</span>
            <span className="s">From an email, doc, or anywhere else</span>
          </span>
          <Icon name="arrow-right" size={14} stroke={2} />
        </button>
      </div>
    </div>
  );
}

function StartScreen() {
  const [filter, setFilter] = React.useState("all");
  const [selected, setSelected] = React.useState("classic");
  const filters = ["All", "ATS-safe", "Pro", "Academic"];

  const visible = TEMPLATES.filter(t => {
    if (filter === "All" || filter === "all") return true;
    if (filter === "ATS-safe") return t.tag === "ats";
    if (filter === "Pro") return t.tag === "pro";
    if (filter === "Academic") return t.style === "academic";
    return true;
  });

  return (
    <div className="start-wrap">
      <div className="start-head">
        <div className="eyebrow">Step 1 of 3 · Choose a starting point</div>
        <h1>Start your CV</h1>
        <p>Pick a template that fits your field, or upload an existing CV and we'll rebuild it inside CareerPilot — same content, better structure.</p>
      </div>

      <div className="start-grid">
        <div>
          <div className="gallery-head">
            <h2>Templates</h2>
            <span className="sub">{visible.length} of {TEMPLATES.length}</span>
          </div>
          <div className="tpl-filters">
            {filters.map(f => (
              <button key={f} className={"tpl-filter " + (filter === f ? "is-active" : "")} onClick={() => setFilter(f)}>{f}</button>
            ))}
          </div>
          <div className="tpl-grid">
            {visible.map(t => (
              <TemplateCard key={t.id} tpl={t} selected={selected === t.id} onClick={() => setSelected(t.id)} />
            ))}
          </div>
        </div>

        <UploadCard onUpload={() => { window.location.href = "index.html"; }} />
      </div>

      <div className="start-foot">
        <span className="hint"><Icon name="info" size={14} stroke={2} />ATS-safe templates pass automated resume scanners used by 90% of large employers.</span>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn-ghost">Skip — start blank</button>
          <button className="btn btn-primary" onClick={() => { window.location.href = "index.html"; }}>
            Use {TEMPLATES.find(t => t.id === selected).name}
            <Icon name="arrow-right" size={14} stroke={2} />
          </button>
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { StartScreen, TemplateCard, UploadCard, TEMPLATES });
