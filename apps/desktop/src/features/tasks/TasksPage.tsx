import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { deadlines } from "@/lib/data/demoData";

export function TasksPage() {
  return (
    <section className="page page-reading">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Tasks</p>
          <h1>Deadlines that stay accountable.</h1>
          <p className="muted">Email-created tasks will require approval before appearing here.</p>
        </div>
        <Button variant="primary">
          <Icon name="plus" size={18} />
          Add task
        </Button>
      </header>

      <Card>
        <div className="deadline-list">
          {deadlines.map((deadline) => (
            <div className="deadline-row deadline-card" key={deadline.id}>
              <button className={deadline.complete ? "checkbox checked" : "checkbox"} type="button" aria-label="Toggle task">
                {deadline.complete && <Icon name="check" size={14} />}
              </button>
              <span>
                <strong>{deadline.title}</strong>
                <small>
                  <Badge tone={deadline.course === "Databases" ? "amber" : "blue"}>{deadline.course}</Badge>
                </small>
              </span>
              <span className={deadline.urgent ? "due-warning" : "due-muted"}>{deadline.due}</span>
            </div>
          ))}
        </div>
      </Card>
    </section>
  );
}
