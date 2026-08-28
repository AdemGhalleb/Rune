const DEFAULT_BACKEND_URL = "http://127.0.0.1:18742";

export interface HealthResponse {
  status: string;
  version: string;
  app: string;
}

export interface Workspace {
  id: number;
  root_path: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceSetRequest {
  root_path: string;
  name?: string;
}

export interface ScanJob {
  id: number;
  workspace_id: number;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  started_at: string | null;
  finished_at: string | null;
  files_discovered: number;
  files_processed: number;
  error: string | null;
}

export interface WorkspaceFile {
  id: number;
  workspace_id: number;
  relative_path: string;
  filename: string;
  extension: string;
  category: string;
  size_bytes: number;
  modified_at: string;
  fs_status: string;
  last_scanned_at: string;
}

export interface WorkspaceFileList {
  items: WorkspaceFile[];
  total: number;
  offset: number;
  limit: number;
}

export interface WorkspaceOverview {
  workspace_id: number;
  total_files: number;
  total_size_bytes: number;
  files_by_category: Record<string, number>;
  files_by_status: Record<string, number>;
  pending_changes_count: number;
  recent_files: WorkspaceFile[];
  latest_scan: ScanJob | null;
}

export interface DocumentSummary {
  total_supported: number;
  not_started: number;
  processing: number;
  ready: number;
  failed: number;
}

export interface WorkspaceDocument {
  id: number;
  workspace_file_id: number;
  filename: string;
  relative_path: string;
  extension: string;
  category: string;
  size_bytes: number;
  fs_status: string;
  modified_at: string;
  extraction_status: string;
  chunking_status: string;
  document_status: "not_started" | "processing" | "ready" | "failed";
}

export interface WorkspaceDocumentList {
  items: WorkspaceDocument[];
  total: number;
  offset: number;
  limit: number;
}

export interface LlmStatus { available: boolean; model: string }
export interface Conversation { id: number; title: string | null; created_at: string; updated_at: string }
export interface ChatMessage { id: number; conversation_id: number; role: "user" | "assistant"; content: string; status: "pending" | "streaming" | "complete" | "failed" | "cancelled"; model_used: string | null; error: string | null; created_at: string; updated_at: string }
export interface ConversationDetail extends Conversation { messages: ChatMessage[] }
export interface MessageSource { id: number; chunk_id: number; workspace_file_id: number; filename: string; rank: number; relevance_score: number | null }

function getBackendBaseUrl(): string {
  return import.meta.env.VITE_BACKEND_URL ?? DEFAULT_BACKEND_URL;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export function getBackendUrl(): string {
  return getBackendBaseUrl();
}

async function apiJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getBackendBaseUrl()}${path}`, init);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<T>;
}

export function fetchLlmStatus(): Promise<LlmStatus> { return apiJson("/api/v1/llm/status"); }
export function fetchConversations(): Promise<Conversation[]> { return apiJson("/api/v1/conversations"); }
export function createConversation(title?: string): Promise<Conversation> { return apiJson("/api/v1/conversations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) }); }
export function fetchConversation(id: number): Promise<ConversationDetail> { return apiJson(`/api/v1/conversations/${id}`); }
export function fetchMessageSources(id: number): Promise<MessageSource[]> { return apiJson(`/api/v1/messages/${id}/sources`); }

export async function streamMessage(id: number, content: string, onEvent: (event: string, data: Record<string, unknown>) => void, signal: AbortSignal): Promise<void> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/conversations/${id}/messages`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }), signal });
  if (!response.ok || !response.body) throw new Error(`Backend returned ${response.status}`);
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = "";
  for (;;) { const result = await reader.read(); if (result.done) break; buffer += decoder.decode(result.value, { stream: true }); const blocks = buffer.split("\n\n"); buffer = blocks.pop() ?? ""; for (const block of blocks) { const event = block.match(/^event: (.+)$/m)?.[1] ?? "message"; const raw = block.match(/^data: (.+)$/m)?.[1]; if (raw) onEvent(event, JSON.parse(raw) as Record<string, unknown>); } }
}

export async function fetchWorkspace(): Promise<Workspace | null> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<Workspace | null>;
}

export async function putWorkspace(payload: WorkspaceSetRequest): Promise<Workspace> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string | Array<{ msg?: string }>;
    } | null;
    let message: string | undefined;
    if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      message = body.detail[0].msg;
    }
    throw new Error(message ?? `Backend returned ${response.status}`);
  }
  return response.json() as Promise<Workspace>;
}

export async function deleteWorkspace(): Promise<void> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
}

export async function postWorkspaceScan(): Promise<ScanJob> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<ScanJob>;
}

export async function fetchWorkspaceScanLatest(): Promise<ScanJob | null> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan/latest`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<ScanJob | null>;
}

export async function postWorkspaceScanCancel(): Promise<{ cancelled: boolean }> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan/cancel`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<{ cancelled: boolean }>;
}

export async function fetchWorkspaceOverview(): Promise<WorkspaceOverview> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/overview`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<WorkspaceOverview>;
}

export async function fetchWorkspaceFiles(params?: {
  category?: string;
  fs_status?: string;
  search?: string;
  offset?: number;
  limit?: number;
}): Promise<WorkspaceFileList> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.fs_status) query.set("fs_status", params.fs_status);
  if (params?.search) query.set("search", params.search);
  if (params?.offset !== undefined) query.set("offset", params.offset.toString());
  if (params?.limit !== undefined) query.set("limit", params.limit.toString());

  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/files?${query.toString()}`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<WorkspaceFileList>;
}

export async function fetchWorkspaceDocumentSummary(): Promise<DocumentSummary> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/documents/summary`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<DocumentSummary>;
}

export async function fetchWorkspaceDocuments(params?: {
  document_status?: string;
  search?: string;
  offset?: number;
  limit?: number;
}): Promise<WorkspaceDocumentList> {
  const query = new URLSearchParams();
  if (params?.document_status) query.set("document_status", params.document_status);
  if (params?.search) query.set("search", params.search);
  if (params?.offset !== undefined) query.set("offset", params.offset.toString());
  if (params?.limit !== undefined) query.set("limit", params.limit.toString());

  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/documents?${query.toString()}`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<WorkspaceDocumentList>;
}

// --- Study Generation (Phase 5A) ---

export interface StudyCitation {
  chunk_id: number;
  workspace_file_id: number;
  filename: string;
  snippet: string;
  relevance_score: number | null;
}

export interface SummaryRequest {
  topic?: string | null;
  workspace_file_id?: number | null;
}

export interface SummaryResponse {
  topic: string;
  title: string;
  overview: string;
  key_points: string[];
  citations: StudyCitation[];
}

export interface FlashcardsRequest {
  topic?: string | null;
  workspace_file_id?: number | null;
  count?: number;
}

export interface FlashcardItem {
  question: string;
  answer: string;
  citations: StudyCitation[];
}

export interface FlashcardSetResponse {
  topic: string;
  cards: FlashcardItem[];
}

export interface QuizRequest {
  topic?: string | null;
  workspace_file_id?: number | null;
  count?: number;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  citations: StudyCitation[];
}

export interface QuizResponse {
  topic: string;
  questions: QuizQuestion[];
}

export interface ExplanationRequest {
  topic: string;
  workspace_file_id?: number | null;
}

export interface ExplanationResponse {
  topic: string;
  explanation: string;
  key_takeaways: string[];
  citations: StudyCitation[];
}

export function generateSummary(payload: SummaryRequest): Promise<SummaryResponse> {
  return apiJson("/api/v1/study/summary", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function generateFlashcards(payload: FlashcardsRequest): Promise<FlashcardSetResponse> {
  return apiJson("/api/v1/study/flashcards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function generateQuiz(payload: QuizRequest): Promise<QuizResponse> {
  return apiJson("/api/v1/study/quiz", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function generateExplanation(payload: ExplanationRequest): Promise<ExplanationResponse> {
  return apiJson("/api/v1/study/explain", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

// --- Phase 5B: Study Persistence ---

export interface FlashcardItemPersisted {
  id: number;
  card_index: number;
  question: string;
  answer: string;
  review_count: number;
  state: "new" | "learning" | "shaky" | "mastered" | string;
  last_reviewed_at: string | null;
  citations: StudyCitation[];
}

export interface QuizQuestionPersisted {
  id: number;
  question_index: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  citations: StudyCitation[];
}

export interface QuizAttemptCreate {
  score: number;
  total_questions: number;
  answers: Record<string, number>;
}

export interface QuizAttemptResponse {
  id: number;
  session_id: number;
  score: number;
  total_questions: number;
  answers: Record<string, number>;
  completed_at: string;
  created_at: string;
}

export interface StudySessionCreate {
  session_type: "summary" | "flashcards" | "quiz" | "explanation" | string;
  title: string;
  topic?: string | null;
  workspace_file_id?: number | null;
  summary_data?: SummaryResponse | null;
  flashcards_data?: FlashcardSetResponse | null;
  quiz_data?: QuizResponse | null;
  explanation_data?: ExplanationResponse | null;
}

export interface StudySessionSummary {
  id: number;
  workspace_id: number;
  session_type: "summary" | "flashcards" | "quiz" | "explanation" | string;
  title: string;
  topic: string | null;
  workspace_file_id: number | null;
  created_at: string;
  updated_at: string;
  item_count: number;
  attempt_count: number;
  best_score: number | null;
}

export interface StudySessionDetail {
  id: number;
  workspace_id: number;
  session_type: "summary" | "flashcards" | "quiz" | "explanation" | string;
  title: string;
  topic: string | null;
  workspace_file_id: number | null;
  created_at: string;
  updated_at: string;
  summary_data: SummaryResponse | null;
  flashcards: FlashcardItemPersisted[];
  quiz_questions: QuizQuestionPersisted[];
  quiz_attempts: QuizAttemptResponse[];
  explanation_data: ExplanationResponse | null;
  citations: StudyCitation[];
}

export function createStudySession(payload: StudySessionCreate): Promise<StudySessionDetail> {
  return apiJson("/api/v1/study/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function listStudySessions(params?: {
  session_type?: string;
  workspace_file_id?: number;
}): Promise<StudySessionSummary[]> {
  const query = new URLSearchParams();
  if (params?.session_type) query.set("session_type", params.session_type);
  if (params?.workspace_file_id !== undefined)
    query.set("workspace_file_id", String(params.workspace_file_id));
  const queryString = query.toString() ? `?${query.toString()}` : "";
  return apiJson(`/api/v1/study/sessions${queryString}`);
}

export function getStudySession(sessionId: number): Promise<StudySessionDetail> {
  return apiJson(`/api/v1/study/sessions/${sessionId}`);
}

export function deleteStudySession(sessionId: number): Promise<void> {
  return apiVoid(`/api/v1/study/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export function reviewFlashcard(
  sessionId: number,
  cardId: number,
  state: "learning" | "shaky" | "mastered",
): Promise<FlashcardItemPersisted> {
  return apiJson(`/api/v1/study/sessions/${sessionId}/flashcards/${cardId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ state }),
  });
}

export function recordQuizAttempt(
  sessionId: number,
  payload: QuizAttemptCreate,
): Promise<QuizAttemptResponse> {
  return apiJson(`/api/v1/study/sessions/${sessionId}/quiz/attempt`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getQuizAttempts(sessionId: number): Promise<QuizAttemptResponse[]> {
  return apiJson(`/api/v1/study/sessions/${sessionId}/quiz/attempts`);
}

