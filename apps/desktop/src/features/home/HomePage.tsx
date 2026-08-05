import { useEffect, useState } from "react";
import { fetchHealth, type HealthResponse } from "@/lib/api/client";

export function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await fetchHealth();
        if (!cancelled) {
          setHealth(data);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not reach backend");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="page">
      <header className="page-header">
        <h1>Welcome to Rune</h1>
        <p className="muted">
          Local-first AI academic companion. Foundation milestone — stack connectivity check.
        </p>
      </header>

      <div className="card">
        <h2>Backend status</h2>
        {loading && <p className="muted">Checking local backend…</p>}
        {!loading && health && (
          <dl className="status-list">
            <div>
              <dt>Status</dt>
              <dd className="status-ok">{health.status}</dd>
            </div>
            <div>
              <dt>App</dt>
              <dd>{health.app}</dd>
            </div>
            <div>
              <dt>Version</dt>
              <dd>{health.version}</dd>
            </div>
          </dl>
        )}
        {!loading && error && (
          <p className="status-error">
            {error}. Start the backend with <code>npm run dev:backend</code> from the repo root.
          </p>
        )}
      </div>
    </section>
  );
}
