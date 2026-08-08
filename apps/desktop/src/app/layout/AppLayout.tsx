import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import { CommandPalette } from "@/components/layout/CommandPalette";
import { Sidebar } from "@/components/layout/Sidebar";
import { CourseSwitcher } from "@/components/workspace/CourseSwitcher";
import { Icon } from "@/components/ui/Icon";
import { WorkspaceSetup } from "@/components/workspace/WorkspaceSetup";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

export function AppLayout() {
  const { loading, workspace } = useWorkspace();
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setPaletteOpen(true);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (loading) return <main className="workspace-setup-page">Loading workspace…</main>;
  if (!workspace) return <WorkspaceSetup />;

  return (
    <div className="app-shell">
      <Sidebar />
      <main className="main">
        <header className="topbar">
          <CourseSwitcher />
          <button className="command-trigger" onClick={() => setPaletteOpen(true)} type="button">
            <Icon name="search" size={18} />
            <span>Search or jump anywhere</span>
            <kbd>Ctrl K</kbd>
          </button>
        </header>
        <div className="view-transition">
          <Outlet />
        </div>
      </main>
      <CommandPalette onOpenChange={setPaletteOpen} open={paletteOpen} />
    </div>
  );
}
