import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Skeleton";
import { fetchWorkspaceFiles, type WorkspaceFile } from "@/lib/api/client";
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
  const [files, setFiles] = useState<WorkspaceFile[]>([]);
  const [totalFiles, setTotalFiles] = useState<number>(0);
  const [loadingFiles, setLoadingFiles] = useState<boolean>(false);

  useEffect(() => {
    if (!workspace) {
      setFiles([]);
      setTotalFiles(0);
      return;
    }

    let cancelled = false;
    setLoadingFiles(true);

    fetchWorkspaceFiles({ search: query, limit: 100 })
      .then((res) => {
        if (!cancelled) {
          setFiles(res.items);
          setTotalFiles(res.total);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setFiles([]);
          setTotalFiles(0);
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingFiles(false);
      });

    return () => {
      cancelled = true;
    };
  }, [workspace, query, scanning]);

  return (
    <section className="page page-wide">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Documents</p>
          <h1>Your material, indexed in place.</h1>
          <p className="muted">
            {workspace
              ? `Workspace: ${workspace.name} (${totalFiles.toLocaleString()} files)`
              : "Files are referenced where they live."}
          </p>
        </div>
        <Button onClick={() => void triggerScan()} variant="primary" disabled={scanning || !workspace}>
          <Icon name="sparkle" size={18} />
          {scanning ? "Scanning…" : "Rescan workspace"}
        </Button>
      </header>

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
          <Button variant="secondary">{totalFiles} total items</Button>
        </div>

        <div className="document-list" aria-live="polite">
          {loadingFiles && (
            <div className="skeleton-preview" aria-label="Loading workspace files">
              <Skeleton className="skeleton-title" />
              <Skeleton />
              <Skeleton className="skeleton-short" />
            </div>
          )}

          {!loadingFiles && files.length === 0 && (
            <EmptyState
              action={
                <Button onClick={() => void triggerScan()} variant="primary">
                  Scan workspace files
                </Button>
              }
              description={
                query
                  ? `No files matching "${query}" were found.`
                  : "Rune hasn't indexed any files in this workspace yet."
              }
              icon="folder"
              title="No documents found"
            />
          )}

          {!loadingFiles &&
            files.map((file) => (
              <div className="document-row" key={file.id}>
                <span className={`file-icon file-${file.category}`}>
                  <Icon name="fileText" size={18} />
                </span>
                <span className="document-title">
                  <strong>{file.filename}</strong>
                  <small>{file.relative_path}</small>
                </span>
                <Badge tone="neutral">{file.category}</Badge>
                <small className="muted">{formatBytes(file.size_bytes)}</small>
                <span className="document-status">
                  <span className={`status-dot status-${fsStatusTone(file.fs_status)}`} />
                  {file.fs_status}
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
