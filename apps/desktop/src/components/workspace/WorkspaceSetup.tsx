import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { pickWorkspaceFolder } from "@/lib/workspace/folderPicker";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

export function WorkspaceSetup() {
  const { error: backendError, setWorkspace } = useWorkspace();
  const [rootPath, setRootPath] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function chooseFolder() {
    try {
      const selected = await pickWorkspaceFolder();
      if (selected) setRootPath(selected);
    } catch {
      setError("The folder picker is available in the Rune desktop app. Enter a folder path to use the browser dev server.");
    }
  }

  async function continueToRune(event: React.FormEvent) {
    event.preventDefault();
    if (!rootPath.trim()) {
      setError("Choose or enter an academic workspace folder first.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await setWorkspace(rootPath.trim());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save this workspace.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="workspace-setup-page">
      <Card className="workspace-setup-card">
        <span className="empty-state-icon">
          <Icon name="folder" size={24} />
        </span>
        <p className="eyebrow">Set up Rune</p>
        <h1>Your academic workspace</h1>
        <p className="muted">Choose the folder where you keep your course material. Rune will keep your files in place; folder scanning is not enabled yet.</p>
        <form className="workspace-form" onSubmit={continueToRune}>
          <label htmlFor="workspace-path">Workspace folder</label>
          <div className="workspace-path-row">
            <input
              id="workspace-path"
              onChange={(event) => setRootPath(event.target.value)}
              placeholder="Choose a folder"
              value={rootPath}
            />
            <Button onClick={() => void chooseFolder()} type="button" variant="secondary">
              Browse
            </Button>
          </div>
          {(error || backendError) && <p className="status-error">{error ?? backendError}</p>}
          <Button isLoading={saving} type="submit" variant="primary">
            Use this workspace
          </Button>
        </form>
      </Card>
    </main>
  );
}
