import { NavLink, useNavigate } from "react-router-dom";
import { Icon, type IconName } from "@/components/ui/Icon";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

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
  const { workspace, syncStatusText, scanning, overview, triggerScan } = useWorkspace();
  const navigate = useNavigate();

  return (
    <aside className="sidebar" aria-label="Primary navigation">
      <div className="brand">
        <span className="brand-mark">R</span>
        <div>
          <p className="brand-name">Rune</p>
          <p className="brand-tagline">Your knowledge stays yours.</p>
        </div>
      </div>

      <button className="workspace-card" onClick={() => navigate("/settings#workspace")} type="button">
        <span className="workspace-icon">
          <Icon name="folder" size={18} />
        </span>
        <span>
          <span>{workspace?.name ?? "Academic Workspace"}</span>
          <small>Workspace selected</small>
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
        <div
          className={`sync-card ${scanning ? "syncing" : ""}`}
          onClick={() => void triggerScan()}
          role="button"
          tabIndex={0}
          title="Click to check workspace for updates"
        >
          <div className="sync-status">
            <span className={`status-dot ${scanning ? "status-warning" : "status-success"}`} />
            <span>
              <strong>{syncStatusText}</strong>
              {overview && (
                <small>{overview.total_files.toLocaleString()} files indexed</small>
              )}
            </span>
          </div>
        </div>
        <NavLink className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")} to="/settings">
          <Icon name="settings" size={20} />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}
