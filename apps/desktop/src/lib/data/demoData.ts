export interface Course {
  id: string;
  name: string;
  shortName: string;
  mastery: number;
  accent: "blue" | "amber" | "green" | "violet" | "rose";
}

export interface FocusItem {
  id: string;
  title: string;
  meta: string;
  tone: "warning" | "success" | "info";
}

export interface DocumentItem {
  id: string;
  title: string;
  course: string;
  type: "pdf" | "docx" | "md";
  status: "indexed" | "processing" | "failed";
  modified: string;
  chunks: number;
}

export interface Deadline {
  id: string;
  title: string;
  course: string;
  due: string;
  urgent: boolean;
  complete: boolean;
}

export const courses: Course[] = [
  { id: "os", name: "Operating Systems", shortName: "OS", mastery: 62, accent: "blue" },
  { id: "algo", name: "Algorithms", shortName: "Algo", mastery: 78, accent: "green" },
  { id: "db", name: "Databases", shortName: "DB", mastery: 41, accent: "amber" },
];

export const focusItems: FocusItem[] = [
  {
    id: "focus-process",
    title: "Review: Process Scheduling",
    meta: "Operating Systems · weak spot, last touched 9 days ago",
    tone: "warning",
  },
  {
    id: "focus-dp",
    title: "Practice: 5 questions on Dynamic Programming",
    meta: "Algorithms · predicted exam weight is high",
    tone: "info",
  },
  {
    id: "focus-db",
    title: "Deadline in 2 days: Database project",
    meta: "Databases · finish normalization write-up",
    tone: "warning",
  },
];

export const recentActivity = [
  { id: "chat-os", title: "Continue: Explain chapter 4", meta: "Operating Systems · 18 minutes ago" },
  { id: "doc-scan", title: "Indexed 12 new lecture slides", meta: "Workspace sync · today" },
];

export const deadlines: Deadline[] = [
  { id: "db-project", title: "Database project", course: "Databases", due: "2d", urgent: true, complete: false },
  { id: "algo-midterm", title: "Algorithms midterm", course: "Algorithms", due: "9d", urgent: false, complete: false },
  { id: "os-lab", title: "Thread scheduling lab", course: "Operating Systems", due: "Completed", urgent: false, complete: true },
];

export const documents: DocumentItem[] = [
  {
    id: "os-slides",
    title: "CPU Scheduling — Lecture 04.pdf",
    course: "Operating Systems",
    type: "pdf",
    status: "indexed",
    modified: "Today",
    chunks: 42,
  },
  {
    id: "algo-notes",
    title: "Dynamic Programming Notes.md",
    course: "Algorithms",
    type: "md",
    status: "processing",
    modified: "Yesterday",
    chunks: 18,
  },
  {
    id: "db-normalization",
    title: "Normalization Study Guide.docx",
    course: "Databases",
    type: "docx",
    status: "indexed",
    modified: "2 days ago",
    chunks: 31,
  },
  {
    id: "db-scan",
    title: "ER Diagram Scan.pdf",
    course: "Databases",
    type: "pdf",
    status: "failed",
    modified: "4 days ago",
    chunks: 0,
  },
];

export const chatMessages = [
  {
    id: "user-1",
    role: "user",
    body: "Explain why round-robin scheduling can improve responsiveness but hurt throughput.",
  },
  {
    id: "assistant-1",
    role: "assistant",
    body:
      "Round-robin gives each process a short time slice, so interactive jobs do not wait behind one long-running task. That improves perceived responsiveness. The tradeoff is context-switch overhead: if the quantum is too small, the CPU spends more time switching than doing useful work.",
    sources: ["CPU Scheduling — Lecture 04.pdf · p. 12", "OS Notes · section 3.2"],
  },
];

export const graphNodes = [
  { id: "scheduling", label: "Scheduling", mastery: 62, weight: 44, x: 310, y: 170 },
  { id: "threads", label: "Threads", mastery: 74, weight: 34, x: 490, y: 120 },
  { id: "deadlock", label: "Deadlock", mastery: 38, weight: 38, x: 530, y: 310 },
  { id: "memory", label: "Memory", mastery: 56, weight: 30, x: 250, y: 330 },
  { id: "io", label: "I/O", mastery: 68, weight: 24, x: 130, y: 210 },
  { id: "sync", label: "Synchronization", mastery: 45, weight: 36, x: 390, y: 260 },
];

export const graphEdges = [
  ["scheduling", "threads", 2],
  ["threads", "sync", 3],
  ["sync", "deadlock", 3],
  ["scheduling", "sync", 2],
  ["memory", "deadlock", 1],
  ["io", "scheduling", 1],
] as const;

export const emailExtractions = [
  {
    id: "email-1",
    title: "New deadline detected",
    summary: "Professor Mensah moved the database checkpoint to Friday at 5 PM.",
    action: "Create task: Database checkpoint · due Friday",
  },
];
