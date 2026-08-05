import { getBackendUrl } from "@/lib/api/client";

export function SettingsPage() {
  return (
    <section className="page">
      <header className="page-header">
        <h1>Settings</h1>
        <p className="muted">Provider and workspace configuration will live here in later milestones.</p>
      </header>

      <div className="card">
        <h2>Development</h2>
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
      </div>
    </section>
  );
}
