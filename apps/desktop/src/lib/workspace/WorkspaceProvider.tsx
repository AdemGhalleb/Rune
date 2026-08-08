import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { deleteWorkspace, fetchWorkspace, putWorkspace, type Workspace } from "@/lib/api/client";

interface WorkspaceContextValue {
  workspace: Workspace | null;
  loading: boolean;
  error: string | null;
  setWorkspace: (rootPath: string, name?: string) => Promise<void>;
  resetWorkspace: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspace, setWorkspaceState] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchWorkspace()
      .then((current) => {
        if (!cancelled) {
          setWorkspaceState(current);
          setError(null);
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Could not reach backend");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<WorkspaceContextValue>(
    () => ({
      workspace,
      loading,
      error,
      async setWorkspace(rootPath, name) {
        const saved = await putWorkspace({ root_path: rootPath, name });
        setWorkspaceState(saved);
        setError(null);
      },
      async resetWorkspace() {
        await deleteWorkspace();
        setWorkspaceState(null);
      },
    }),
    [error, loading, workspace],
  );

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace(): WorkspaceContextValue {
  const context = useContext(WorkspaceContext);
  if (!context) throw new Error("useWorkspace must be used within WorkspaceProvider");
  return context;
}
