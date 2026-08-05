import { NavLink } from "react-router-dom";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Icon, type IconName } from "@/components/ui/Icon";

interface NavItem {
  to: string;
  label: string;
  icon: IconName;
}

const primaryNav: NavItem[] = [
  { to: "/", label: "Home", icon: "home" },
  { to: "/chat", label: "Chat", icon: "message" },
  { to: "/documents", label: "Documents", icon: "fileText" },
  { to: "/learning", label: "Learning", icon: "book" },
  { to: "/graph", label: "Knowledge Graph", icon: "graph" },
  { to: "/tasks", label: "Tasks", icon: "tasks" },
  { to: "/email", label: "Email", icon: "mail" },
];

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand">
        <span className="brand-mark">R</span>
        <div>
          <p className="brand-name">Rune</p>
          <p className="brand-tagline">Your knowledge stays yours.</p>
        </div>
      </div>

      <button className="workspace-card" type="button">
        <span className="workspace-icon">
          <Icon name="folder" size={18} />
        </span>
        <span>
          <span>Academic Workspace</span>
          <small>3 courses indexed</small>
        </span>
      </button>

      <nav className="nav">
        {primaryNav.map((item) => (
          <NavLink
            className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            end={item.to === "/"}
            key={item.to}
            to={item.to}
          >
            <Icon name={item.icon} size={20} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sync-card">
          <div className="sync-title">
            <span className="pulse-dot" />
            <span>Indexing workspace</span>
          </div>
          <ProgressBar value={72} label="Embedding notes" />
        </div>
        <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/settings">
          <Icon name="settings" size={20} />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}
