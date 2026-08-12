import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  deleteWorkspace,
  fetchWorkspace,
  fetchWorkspaceOverview,
  postWorkspaceScan,
  putWorkspace,
  type ScanJob,
  type Workspace,
  type WorkspaceOverview,
} from "@/lib/api/client";

interface WorkspaceContextValue {
  workspace: Workspace | null;
  overview: WorkspaceOverview | null;
  loading: boolean;
  scanning: boolean;
  syncStatusText: string;
  error: string | null;
  setWorkspace: (rootPath: string, name?: string) => Promise<void>;
  resetWorkspace: () => Promise<void>;
  triggerScan: () => Promise<void>;
  refreshOverview: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspace, setWorkspaceState] = useState<Workspace | null>(null);
  const [overview, setOverview] = useState<WorkspaceOverview | null>(null);
  const [scanning, setScanning] = useState<boolean>(false);
  const [syncStatusText, setSyncStatusText] = useState<string>("Checking your workspace…");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activePollCleanupRef = useRef<(() => void) | null>(null);

  const loadOverview = useCallback(async () => {
    try {
      const data = await fetchWorkspaceOverview();
      setOverview(data);
      return data;
    } catch {
      return null;
    }
  }, []);

  const pollScanJob = useCallback((initialJob: ScanJob) => {
    if (activePollCleanupRef.current) {
      activePollCleanupRef.current();
    }

    let active = true;
    let currentJob = initialJob;

    const interval = setInterval(async () => {
      if (!active) return;

      if (currentJob.status === "running" || currentJob.status === "queued") {
        const count = currentJob.files_discovered;
        setSyncStatusText(count > 0 ? `${count.toLocaleString()} files found so far` : "Scanning workspace…");
      }

      const ov = await loadOverview();
      if (ov?.latest_scan) {
        currentJob = ov.latest_scan;
      }

      if (currentJob.status === "completed" || currentJob.status === "failed" || currentJob.status === "cancelled") {
        active = false;
        clearInterval(interval);
        setScanning(false);
        if (currentJob.status === "completed") {
          const total = ov?.total_files ?? 0;
          setSyncStatusText(total > 0 ? "Rune is up to date" : "Workspace is empty");
        } else if (currentJob.status === "cancelled") {
          setSyncStatusText("Scan cancelled");
        } else {
          setSyncStatusText("Scan encountered an error");
        }
      }
    }, 1000);

    const cleanup = () => {
      active = false;
      clearInterval(interval);
    };

    activePollCleanupRef.current = cleanup;
    return cleanup;
  }, [loadOverview]);

  const triggerScan = useCallback(async () => {
    try {
      setScanning(true);
      setSyncStatusText("Checking your workspace…");
      const job = await postWorkspaceScan();
      pollScanJob(job);
    } catch (err) {
      setScanning(false);
      setSyncStatusText("Sync error");
    }
  }, [pollScanJob]);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      try {
        const current = await fetchWorkspace();
        if (!cancelled) {
          setWorkspaceState(current);
          setError(null);
          if (current) {
            const ov = await loadOverview();
            if (ov?.latest_scan && (ov.latest_scan.status === "running" || ov.latest_scan.status === "queued")) {
              setScanning(true);
              pollScanJob(ov.latest_scan);
            } else {
              void triggerScan();
            }
          }
        }
      } catch (reason: unknown) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not reach backend");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void init();
    return () => {
      cancelled = true;
      if (activePollCleanupRef.current) {
        activePollCleanupRef.current();
      }
    };
  }, [loadOverview, pollScanJob, triggerScan]);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      workspace,
      overview,
      loading,
      scanning,
      syncStatusText,
      error,
      async setWorkspace(rootPath, name) {
        const saved = await putWorkspace({ root_path: rootPath, name });
        setWorkspaceState(saved);
        setError(null);
        void triggerScan();
      },
      async resetWorkspace() {
        await deleteWorkspace();
        setWorkspaceState(null);
        setOverview(null);
        setScanning(false);
        setSyncStatusText("No workspace selected");
      },
      triggerScan,
      refreshOverview: async () => {
        await loadOverview();
      },
    }),
    [error, loading, loadOverview, overview, scanning, syncStatusText, triggerScan, workspace],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return context;
}
