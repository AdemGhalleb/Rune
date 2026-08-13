import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  fetchWorkspaceDocumentSummary,
  fetchWorkspaceDocuments,
  type DocumentSummary,
  type WorkspaceDocument,
} from "@/lib/api/client";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

export function DocumentsPage() {
  const { workspace, triggerScan, scanning } = useWorkspace();
  const [query, setQuery] = useState("");
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);
  const [summary, setSummary] = useState<DocumentSummary | null>(null);
  const [loadingFiles, setLoadingFiles] = useState<boolean>(false);

  useEffect(() => {
    if (!workspace) {
      setDocuments([]);
      setSummary(null);
      return;
    }

    let cancelled = false;
    setLoadingFiles(true);

    Promise.all([
      fetchWorkspaceDocumentSummary(),
      fetchWorkspaceDocuments({ search: query || undefined, limit: 100 }),
    ])
      .then(([docSummary, docList]) => {
        if (!cancelled) {
          setSummary(docSummary);
          setDocuments(docList.items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSummary(null);
          setDocuments([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingFiles(false);
      });

    return () => {
      cancelled = true;
    };
  }, [workspace, query, scanning]);

  const totalDocuments = summary?.total_supported ?? documents.length;

  return (
    <section className="page page-wide">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Documents</p>
          <h1>Your material, indexed in place.</h1>
          <p className="muted">
            {workspace
              ? `Workspace: ${workspace.name} (${totalDocuments.toLocaleString()} supported documents)`
              : "Files are referenced where they live."}
          </p>
        </div>
        <Button onClick={() => void triggerScan()} variant="primary" disabled={scanning || !workspace}>
          <Icon name="sparkle" size={18} />
          {scanning ? "Scanning…" : "Rescan workspace"}
        </Button>
      </header>

      <div className="documents-summary-grid" aria-live="polite">
        <Card>
          <div className="document-summary-stat">
            <span className="muted">Ready</span>
            <strong>{summary?.ready ?? 0}</strong>
          </div>
        </Card>
        <Card>
          <div className="document-summary-stat">
            <span className="muted">Processing</span>
            <strong>{summary?.processing ?? 0}</strong>
          </div>
        </Card>
        <Card>
          <div className="document-summary-stat">
            <span className="muted">Not started</span>
            <strong>{summary?.not_started ?? 0}</strong>
          </div>
        </Card>
        <Card>
          <div className="document-summary-stat">
            <span className="muted">Failed</span>
            <strong>{summary?.failed ?? 0}</strong>
          </div>
        </Card>
      </div>

      <Card>
        <div className="documents-toolbar">
          <label className="search-field">
            <Icon name="search" size={18} />
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by filename or path…"
              value={query}
            />
          </label>
          <Button variant="secondary">{totalDocuments} supported</Button>
        </div>

        <div className="document-list" aria-live="polite">
          {loadingFiles && (
            <div className="skeleton-preview" aria-label="Loading document index">
              <Skeleton className="skeleton-title" />
              <Skeleton />
              <Skeleton className="skeleton-short" />
            </div>
          )}

          {!loadingFiles && documents.length === 0 && (
            <EmptyState
              action={
                <Button onClick={() => void triggerScan()} variant="primary">
                  Scan workspace files
                </Button>
              }
              description={
                query
                  ? `No supported documents matching "${query}" were found.`
                  : "Rune hasn't indexed any supported documents in this workspace yet."
              }
              icon="folder"
              title="No documents found"
            />
          )}

          {!loadingFiles &&
            documents.map((file) => (
              <div className="document-row" key={file.id}>
                <span className={`file-icon file-${file.extension.replace('.', '') || 'txt'}`}>
                  <Icon name="fileText" size={18} />
                </span>
                <span className="document-title">
                  <strong>{file.filename}</strong>
                  <small>{file.relative_path}</small>
                </span>
                <Badge tone={documentStatusTone(file.document_status)}>{file.document_status.replace("_", " ")}</Badge>
                <small className="muted">{formatBytes(file.size_bytes)}</small>
                <span className="document-status">
                  <span className={`status-dot status-${fsStatusTone(file.fs_status)}`} />
                  {file.document_status}
                </span>
              </div>
            ))}
        </div>
      </Card>
    </section>
  );
}

function fsStatusTone(status: string): "success" | "warning" | "error" | "info" {
  switch (status) {
    case "unchanged":
      return "success";
    case "new":
    case "modified":
      return "warning";
    case "error":
      return "error";
    default:
      return "info";
  }
}

function documentStatusTone(status: WorkspaceDocument["document_status"]): "neutral" | "warning" | "success" | "error" {
  switch (status) {
    case "ready":
      return "success";
    case "processing":
      return "warning";
    case "failed":
      return "error";
    default:
      return "neutral";
  }
}
