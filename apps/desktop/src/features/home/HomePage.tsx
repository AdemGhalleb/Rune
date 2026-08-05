import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Skeleton } from "@/components/ui/Skeleton";
import { fetchHealth, type HealthResponse } from "@/lib/api/client";
import { courses, deadlines, focusItems, recentActivity } from "@/lib/data/demoData";

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
    <section className="page page-wide">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Dashboard</p>
          <h1>Good afternoon, Alex.</h1>
          <p className="muted">A calm read on what deserves attention next.</p>
        </div>
        <Button variant="primary">
          <Icon name="sparkle" size={18} />
          Start focused review
        </Button>
      </header>

      <div className="dashboard-grid">
        <Card className="focus-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Today's Focus</p>
              <h2>Mastery-ranked recommendations</h2>
            </div>
            <Badge tone="warning">3 waiting</Badge>
          </div>
          <div className="focus-list">
            {focusItems.map((item) => (
              <button className="focus-row" key={item.id} type="button">
                <span className={`status-dot status-${item.tone}`} />
                <span>
                  <strong>{item.title}</strong>
                  <small>{item.meta}</small>
                </span>
                <Icon name="arrowRight" size={18} />
              </button>
            ))}
          </div>
        </Card>

        <Card>
          <div className="section-heading">
            <div>
              <p className="eyebrow">Courses</p>
              <h2>Semester state</h2>
            </div>
            <Button variant="ghost" aria-label="Add course">
              <Icon name="plus" size={18} />
            </Button>
          </div>
          <div className="course-grid">
            {courses.map((course) => (
              <button className="course-card" key={course.id} type="button">
                <Badge tone={course.accent}>{course.shortName}</Badge>
                <strong>{course.name}</strong>
                <ProgressBar value={course.mastery} label="Mastery" />
              </button>
            ))}
          </div>
        </Card>

        <Card className="dashboard-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Recent Activity</p>
              <h2>Pick up where you left off</h2>
            </div>
          </div>
          <div className="quiet-list">
            {recentActivity.map((activity) => (
              <button className="quiet-row" key={activity.id} type="button">
                <Icon name="clock" size={18} />
                <span>
                  <strong>{activity.title}</strong>
                  <small>{activity.meta}</small>
                </span>
              </button>
            ))}
          </div>
        </Card>

        <Card className="dashboard-panel">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Upcoming</p>
              <h2>Deadlines</h2>
            </div>
          </div>
          <div className="deadline-list">
            {deadlines.slice(0, 2).map((deadline) => (
              <div className="deadline-row" key={deadline.id}>
                <span className={deadline.complete ? "checkbox checked" : "checkbox"} aria-hidden="true">
                  {deadline.complete && <Icon name="check" size={14} />}
                </span>
                <span>
                  <strong>{deadline.title}</strong>
                  <small>{deadline.course}</small>
                </span>
                <span className={deadline.urgent ? "due-warning" : "due-muted"}>{deadline.due}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="backend-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Local System</p>
              <h2>Backend status</h2>
            </div>
            {loading && <Skeleton className="status-skeleton" />}
            {!loading && health && <Badge tone="success">{health.status}</Badge>}
            {!loading && error && <Badge tone="error">Offline</Badge>}
          </div>
          {loading && <p className="muted">Checking the local process...</p>}
          {!loading && health && (
            <p className="muted">
              {health.app} {health.version} is reachable on this machine.
            </p>
          )}
          {!loading && error && (
            <p className="status-error">
              {error}. Start the backend with <code>npm run dev:backend</code>.
            </p>
          )}
        </Card>
      </div>
    </section>
  );
}
