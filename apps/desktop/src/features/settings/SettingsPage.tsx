import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon, type IconName } from "@/components/ui/Icon";
import { getBackendUrl } from "@/lib/api/client";
import { useTheme } from "@/lib/theme/ThemeProvider";
import { pickWorkspaceFolder } from "@/lib/workspace/folderPicker";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

export function SettingsPage() {
  const { setTheme, theme, toggleTheme } = useTheme();
  const { resetWorkspace, setWorkspace, workspace } = useWorkspace();
  const [workspaceError, setWorkspaceError] = useState<string | null>(null);

  async function changeWorkspace() {
    setWorkspaceError(null);
    try {
      const path = await pickWorkspaceFolder();
      if (path) await setWorkspace(path);
    } catch (reason) {
      setWorkspaceError(
        reason instanceof Error
          ? reason.message
          : "The folder picker is available in the Rune desktop app."
      );
    }
  }

  return (
    <section className="page page-wide settings-page">
      <header className="page-header">
        <p className="eyebrow">Settings</p>
        <h1>Settings</h1>
        <p className="muted">Single-column groups with a local section rail for configuration that will grow over time.</p>
      </header>

      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Settings sections">
          {["Workspace", "AI Models", "Privacy", "Email", "Appearance"].map((item) => (
            <a href={`#${item.toLowerCase().replace(" ", "-")}`} key={item}>
              {item}
            </a>
          ))}
        </nav>

        <div className="settings-stack">
          <Card id="workspace">
            <SectionHeader icon="folder" title="Workspace" />
            <p className="muted">{workspace?.root_path}. Rune keeps academic files in place; scanning is not enabled yet.</p>
            <div className="button-row">
              <Button onClick={() => void changeWorkspace()} variant="secondary">Change workspace folder</Button>
              <Button onClick={() => void resetWorkspace()} variant="destructive">Reset workspace</Button>
            </div>
            {workspaceError && <p className="status-error" style={{ marginTop: "var(--space-3)" }}>{workspaceError}</p>}
          </Card>

          <Card id="ai-models">
            <SectionHeader icon="cpu" title="AI Models" />
            <div className="settings-row">
              <span>
                <strong>Local model provider</strong>
                <small>Ollama auto-detected when available.</small>
              </span>
              <code>llama3.2:3b</code>
            </div>
          </Card>

          <Card id="privacy">
            <SectionHeader icon="shield" title="Privacy" />
            <div className="settings-row">
              <span>
                <strong>Local-first mode</strong>
                <small>Cloud providers remain opt-in per feature.</small>
              </span>
              <Icon name="lock" size={20} />
            </div>
          </Card>

          <Card id="email">
            <SectionHeader icon="mail" title="Email" />
            <p className="muted">Deadline extraction is approval-gated; no automatic task creation.</p>
          </Card>

          <Card id="appearance">
            <SectionHeader icon={theme === "dark" ? "moon" : "sun"} title="Appearance" />
            <div className="theme-options" role="group" aria-label="Theme">
              <Button variant={theme === "light" ? "primary" : "secondary"} onClick={() => setTheme("light")}>
                Light
              </Button>
              <Button variant={theme === "dark" ? "primary" : "secondary"} onClick={() => setTheme("dark")}>
                Dark
              </Button>
              <Button variant="ghost" onClick={toggleTheme}>
                Toggle
              </Button>
            </div>
          </Card>

          <Card>
            <SectionHeader icon="database" title="Development" />
            <dl className="status-list">
              <div>
                <dt>Backend URL</dt>
                <dd>
                  <code>{getBackendUrl()}</code>
                </dd>
              </div>
              <div>
                <dt>Override</dt>
                <dd>
                  Set <code>VITE_BACKEND_URL</code> in <code>apps/desktop/.env</code>
                </dd>
              </div>
            </dl>
          </Card>
        </div>
      </div>
    </section>
  );
}

function SectionHeader({ icon, title }: { icon: IconName; title: string }) {
  return (
    <div className="settings-section-header">
      <Icon name={icon} size={20} />
      <h2>{title}</h2>
    </div>
  );
}
