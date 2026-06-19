// Shared chrome: AppSidebar + AppHeader. Used by all four UI kits.
// Load AFTER React + Babel.

const SIDEBAR_ITEMS = [
  { id: "creator",  label: "CV Creator",         icon: "file-text" },
  { id: "analysis", label: "Analysis",           icon: "target" },
  { id: "agent",    label: "Job Agent",          icon: "briefcase" },
  { id: "sim",      label: "Interview Sim",      icon: "mic" },
];

function Icon({ name, size = 18, stroke = 1.75, className = "" }) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (window.lucide && ref.current) {
      ref.current.innerHTML = "";
      const el = document.createElement("i");
      el.setAttribute("data-lucide", name);
      ref.current.appendChild(el);
      window.lucide.createIcons({ attrs: { width: size, height: size, "stroke-width": stroke } });
    }
  }, [name, size, stroke]);
  return <span ref={ref} className={"icon " + className} style={{ display: "inline-flex", width: size, height: size }} />;
}

function AppSidebar({ active = "creator", brand = "CareerPilot" }) {
  return (
    <aside className="app-sidebar">
      <div className="brand">
        <img src="../../assets/logo-mark.svg" width="28" height="28" alt="" />
        <span className="brand-name">{brand}</span>
      </div>
      <nav>
        {SIDEBAR_ITEMS.map(item => {
          const href = `../${item.id === "creator" ? "cv-creator" : item.id === "analysis" ? "cv-analysis" : item.id === "agent" ? "job-agent" : "interview-sim"}/index.html`;
          return (
            <a key={item.id} href={href} className={"nav-item " + (item.id === active ? "is-active" : "")}>
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
            </a>
          );
        })}
      </nav>
      <div className="sidebar-foot">
        <div className="user-row">
          <div className="user-av">MH</div>
          <div className="user-meta">
            <div className="user-name">Maya Hernandez</div>
            <div className="user-sub">Pro plan</div>
          </div>
          <Icon name="settings" size={16} />
        </div>
      </div>
    </aside>
  );
}

function AppHeader({ title, sub, right }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1 className="header-title">{title}</h1>
        {sub && <span className="header-sub">{sub}</span>}
      </div>
      <div className="header-right">{right}</div>
    </header>
  );
}

function AIBadge({ label = "AI" }) {
  return (
    <span className="ai-badge">
      <Icon name="sparkles" size={11} stroke={2} />
      {label}
    </span>
  );
}

Object.assign(window, { Icon, AppSidebar, AppHeader, AIBadge, SIDEBAR_ITEMS });
