import { open } from "@tauri-apps/plugin-dialog";

/** Open the platform's directory picker from the Tauri desktop shell. */
export async function pickWorkspaceFolder(): Promise<string | null> {
  const selection = await open({ directory: true, multiple: false, title: "Choose academic workspace" });
  return typeof selection === "string" ? selection : null;
}
