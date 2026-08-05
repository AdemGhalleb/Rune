import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { emailExtractions } from "@/lib/data/demoData";

export function EmailPage() {
  return (
    <section className="page page-reading">
      <header className="page-header">
        <p className="eyebrow">Email</p>
        <h1>Approval-gated academic signals.</h1>
        <p className="muted">Rune can surface likely deadlines, but it never creates tasks automatically.</p>
      </header>

      {emailExtractions.map((extraction) => (
        <Card className="email-extraction" key={extraction.id}>
          <Badge tone="warning">{extraction.title}</Badge>
          <h2>{extraction.summary}</h2>
          <p className="muted">{extraction.action}</p>
          <div className="button-row">
            <Button variant="primary">
              <Icon name="check" size={18} />
              Approve
            </Button>
            <Button variant="ghost">Dismiss</Button>
          </div>
        </Card>
      ))}
    </section>
  );
}
