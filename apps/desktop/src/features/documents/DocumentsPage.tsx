import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Skeleton";
import { documents } from "@/lib/data/demoData";

export function DocumentsPage() {
  const [query, setQuery] = useState("");

  const filteredDocuments = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    if (!normalizedQuery) {
      return documents;
    }
    return documents.filter((document) =>
      `${document.title} ${document.course} ${document.type}`.toLowerCase().includes(normalizedQuery),
    );
  }, [query]);

  return (
    <section className="page page-wide">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Documents</p>
          <h1>Your material, indexed in place.</h1>
          <p className="muted">Files are referenced where they live. This list uses temporary document data.</p>
        </div>
        <Button variant="primary">
          <Icon name="folder" size={18} />
          Select workspace
        </Button>
      </header>

      <Card>
        <div className="documents-toolbar">
          <label className="search-field">
            <Icon name="search" size={18} />
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents, courses, or file types"
              value={query}
            />
          </label>
          <Button variant="secondary">List view</Button>
        </div>

        <div className="document-list" aria-live="polite">
          {filteredDocuments.length === 0 ? (
            <EmptyState
              action={<Button variant="primary">Select your workspace folder</Button>}
              description="Choose the academic folder Rune should index. Your files stay where they are."
              icon="folder"
              title="No matching documents"
            />
          ) : (
            filteredDocuments.map((document) => (
              <button className="document-row" key={document.id} type="button">
                <span className={`file-icon file-${document.type}`}>
                  <Icon name="fileText" size={18} />
                </span>
                <span className="document-title">
                  <strong>{document.title}</strong>
                  <small>
                    {document.chunks > 0 ? `${document.chunks} chunks` : "Needs attention"} · {document.modified}
                  </small>
                </span>
                <Badge tone="neutral">{document.course}</Badge>
                <span className="document-status">
                  <span className={`status-dot status-${statusTone(document.status)}`} />
                  {document.status}
                </span>
              </button>
            ))
          )}
        </div>

        <div className="skeleton-preview" aria-label="Loading preview example">
          <Skeleton className="skeleton-title" />
          <Skeleton />
          <Skeleton className="skeleton-short" />
        </div>
      </Card>
    </section>
  );
}

function statusTone(status: string) {
  if (status === "indexed") {
    return "success";
  }
  if (status === "failed") {
    return "error";
  }
  return "info";
}
