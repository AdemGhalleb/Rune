import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "./layout/AppLayout";
import { ChatPage } from "@/features/chat/ChatPage";
import { DocumentsPage } from "@/features/documents/DocumentsPage";
import { EmailPage } from "@/features/email/EmailPage";
import { GraphPage } from "@/features/graph/GraphPage";
import { HomePage } from "@/features/home/HomePage";
import { LearningPage } from "@/features/learning/LearningPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { TasksPage } from "@/features/tasks/TasksPage";
import { ThemeProvider } from "@/lib/theme/ThemeProvider";

export function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/documents" element={<DocumentsPage />} />
            <Route path="/learning" element={<LearningPage />} />
            <Route path="/graph" element={<GraphPage />} />
            <Route path="/tasks" element={<TasksPage />} />
            <Route path="/email" element={<EmailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
