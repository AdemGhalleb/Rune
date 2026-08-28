import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Icon } from "@/components/ui/Icon";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Tabs } from "@/components/ui/Tabs";
import {
  type ExplanationResponse,
  type FlashcardItemPersisted,
  type FlashcardSetResponse,
  type QuizAttemptResponse,
  type QuizQuestionPersisted,
  type QuizResponse,
  type StudySessionDetail,
  type StudySessionSummary,
  type SummaryResponse,
  type WorkspaceDocument,
  createStudySession,
  deleteStudySession,
  fetchLlmStatus,
  fetchWorkspaceDocuments,
  generateExplanation,
  generateFlashcards,
  generateQuiz,
  generateSummary,
  getStudySession,
  listStudySessions,
  recordQuizAttempt,
  reviewFlashcard,
} from "@/lib/api/client";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

const tabs = [
  { id: "summary", label: "Summarize" },
  { id: "flashcards", label: "Flashcards" },
  { id: "quiz", label: "Quiz Mode" },
  { id: "explain", label: "Explain Concept" },
  { id: "history", label: "Saved Sessions" },
];

export function LearningPage() {
  const { workspace } = useWorkspace();
  const [activeTab, setActiveTab] = useState("summary");

  // Material selection state
  const [topic, setTopic] = useState("");
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
  const [itemCount, setItemCount] = useState(5);
  const [documents, setDocuments] = useState<WorkspaceDocument[]>([]);

  // LLM Status
  const [llmOnline, setLlmOnline] = useState(true);

  // Generation status
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Active Persistent Session State
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [persistedCards, setPersistedCards] = useState<FlashcardItemPersisted[]>([]);
  const [persistedQuestions, setPersistedQuestions] = useState<QuizQuestionPersisted[]>([]);
  const [quizAttempts, setQuizAttempts] = useState<QuizAttemptResponse[]>([]);

  // Study Results State (in-memory or active)
  const [summaryData, setSummaryData] = useState<SummaryResponse | null>(null);
  const [flashcardData, setFlashcardData] = useState<FlashcardSetResponse | null>(null);
  const [quizData, setQuizData] = useState<QuizResponse | null>(null);
  const [explanationData, setExplanationData] = useState<ExplanationResponse | null>(null);

  // Flashcard runner state
  const [cardIndex, setCardIndex] = useState(0);
  const [cardFlipped, setCardFlipped] = useState(false);

  // Quiz runner state
  const [quizIndex, setQuizIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [quizSubmitted, setQuizSubmitted] = useState(false);
  const [quizScore, setQuizScore] = useState(0);
  const [quizFinished, setQuizFinished] = useState(false);
  const [userAnswers, setUserAnswers] = useState<Record<string, number>>({});

  // History List State
  const [savedSessions, setSavedSessions] = useState<StudySessionSummary[]>([]);
  const [historyFilter, setHistoryFilter] = useState<string>("all");

  useEffect(() => {
    void fetchLlmStatus().then(
      (status) => setLlmOnline(status.available),
      () => setLlmOnline(false),
    );
  }, []);

  useEffect(() => {
    if (workspace) {
      void fetchWorkspaceDocuments({ limit: 100 }).then(
        (res) => setDocuments(res.items.filter((d) => d.document_status === "ready")),
        () => setDocuments([]),
      );
      void refreshSavedSessions();
    }
  }, [workspace]);

  async function refreshSavedSessions() {
    try {
      const sessions = await listStudySessions();
      setSavedSessions(sessions);
    } catch {
      setSavedSessions([]);
    }
  }

  // Handlers for Generation
  async function handleGenerateSummary() {
    setLoading(true);
    setErrorMessage(null);
    setSaveSuccessMsg(null);
    setActiveSessionId(null);
    try {
      const res = await generateSummary({
        topic: topic.trim() || undefined,
        workspace_file_id: selectedDocId || undefined,
      });
      setSummaryData(res);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Summary generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateFlashcards() {
    setLoading(true);
    setErrorMessage(null);
    setSaveSuccessMsg(null);
    setActiveSessionId(null);
    setPersistedCards([]);
    try {
      const res = await generateFlashcards({
        topic: topic.trim() || undefined,
        workspace_file_id: selectedDocId || undefined,
        count: itemCount,
      });
      setFlashcardData(res);
      setCardIndex(0);
      setCardFlipped(false);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Flashcard generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateQuiz() {
    setLoading(true);
    setErrorMessage(null);
    setSaveSuccessMsg(null);
    setActiveSessionId(null);
    setPersistedQuestions([]);
    setQuizAttempts([]);
    try {
      const res = await generateQuiz({
        topic: topic.trim() || undefined,
        workspace_file_id: selectedDocId || undefined,
        count: itemCount,
      });
      setQuizData(res);
      setQuizIndex(0);
      setSelectedOption(null);
      setQuizSubmitted(false);
      setQuizScore(0);
      setQuizFinished(false);
      setUserAnswers({});
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Quiz generation failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateExplanation() {
    if (!topic.trim()) {
      setErrorMessage("Please enter a topic or concept to explain.");
      return;
    }
    setLoading(true);
    setErrorMessage(null);
    setSaveSuccessMsg(null);
    setActiveSessionId(null);
    try {
      const res = await generateExplanation({
        topic: topic.trim(),
        workspace_file_id: selectedDocId || undefined,
      });
      setExplanationData(res);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Explanation generation failed");
    } finally {
      setLoading(false);
    }
  }

  // Persistence: Save current active session
  async function handleSaveSession() {
    setLoading(true);
    setErrorMessage(null);
    try {
      let created: StudySessionDetail | null = null;
      if (activeTab === "summary" && summaryData) {
        created = await createStudySession({
          session_type: "summary",
          title: summaryData.title,
          topic: summaryData.topic,
          workspace_file_id: selectedDocId,
          summary_data: summaryData,
        });
      } else if (activeTab === "flashcards" && flashcardData) {
        created = await createStudySession({
          session_type: "flashcards",
          title: `${flashcardData.topic} Flashcards`,
          topic: flashcardData.topic,
          workspace_file_id: selectedDocId,
          flashcards_data: flashcardData,
        });
        setPersistedCards(created.flashcards);
      } else if (activeTab === "quiz" && quizData) {
        created = await createStudySession({
          session_type: "quiz",
          title: `${quizData.topic} Quiz`,
          topic: quizData.topic,
          workspace_file_id: selectedDocId,
          quiz_data: quizData,
        });
        setPersistedQuestions(created.quiz_questions);
        setQuizAttempts(created.quiz_attempts);
      } else if (activeTab === "explain" && explanationData) {
        created = await createStudySession({
          session_type: "explanation",
          title: `${explanationData.topic} Concept`,
          topic: explanationData.topic,
          workspace_file_id: selectedDocId,
          explanation_data: explanationData,
        });
      }

      if (created) {
        setActiveSessionId(created.id);
        setSaveSuccessMsg("Session saved to study library!");
        void refreshSavedSessions();
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to save session");
    } finally {
      setLoading(false);
    }
  }

  // Load a saved session
  async function handleLoadSession(sessionSummary: StudySessionSummary) {
    setLoading(true);
    setErrorMessage(null);
    setSaveSuccessMsg(null);
    try {
      const detail = await getStudySession(sessionSummary.id);
      setActiveSessionId(detail.id);
      setTopic(detail.topic || "");
      setSelectedDocId(detail.workspace_file_id);

      if (detail.session_type === "summary" && detail.summary_data) {
        setSummaryData(detail.summary_data);
        setActiveTab("summary");
      } else if (detail.session_type === "flashcards") {
        setPersistedCards(detail.flashcards);
        setFlashcardData({
          topic: detail.topic || detail.title,
          cards: detail.flashcards.map((fc) => ({
            question: fc.question,
            answer: fc.answer,
            citations: fc.citations,
          })),
        });
        setCardIndex(0);
        setCardFlipped(false);
        setActiveTab("flashcards");
      } else if (detail.session_type === "quiz") {
        setPersistedQuestions(detail.quiz_questions);
        setQuizAttempts(detail.quiz_attempts);
        setQuizData({
          topic: detail.topic || detail.title,
          questions: detail.quiz_questions.map((q) => ({
            question: q.question,
            options: q.options,
            correct_index: q.correct_index,
            explanation: q.explanation,
            citations: q.citations,
          })),
        });
        setQuizIndex(0);
        setSelectedOption(null);
        setQuizSubmitted(false);
        setQuizScore(0);
        setQuizFinished(false);
        setUserAnswers({});
        setActiveTab("quiz");
      } else if (detail.session_type === "explanation" && detail.explanation_data) {
        setExplanationData(detail.explanation_data);
        setActiveTab("explain");
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load session");
    } finally {
      setLoading(false);
    }
  }

  async function handleDeleteSession(sessionId: number, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await deleteStudySession(sessionId);
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
      }
      void refreshSavedSessions();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to delete session");
    }
  }

  // Flashcard review rating
  async function handleFlashcardReview(state: "mastered" | "shaky" | "learning") {
    if (!activeSessionId || !persistedCards[cardIndex]) return;
    const card = persistedCards[cardIndex];
    try {
      const updated = await reviewFlashcard(activeSessionId, card.id, state);
      setPersistedCards((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c)),
      );
      if (cardIndex + 1 < persistedCards.length) {
        setCardIndex((prev) => prev + 1);
        setCardFlipped(false);
      }
    } catch {
      // Graceful fallback
    }
  }

  // Quiz submission & persistence
  async function handleQuizSubmit() {
    if (selectedOption === null || !quizData) return;
    const currentQ = quizData.questions[quizIndex];
    const isCorrect = selectedOption === currentQ.correct_index;
    const updatedAnswers = { ...userAnswers, [String(quizIndex)]: selectedOption };
    setUserAnswers(updatedAnswers);

    const newScore = quizScore + (isCorrect ? 1 : 0);
    if (isCorrect) {
      setQuizScore(newScore);
    }
    setQuizSubmitted(true);

    // If this is the last question and we have an active saved session, record the attempt
    if (quizIndex + 1 >= quizData.questions.length && activeSessionId) {
      try {
        const attempt = await recordQuizAttempt(activeSessionId, {
          score: newScore,
          total_questions: quizData.questions.length,
          answers: updatedAnswers,
        });
        setQuizAttempts((prev) => [attempt, ...prev]);
      } catch {
        // Fallback
      }
    }
  }

  function handleQuizNext() {
    if (!quizData) return;
    if (quizIndex + 1 < quizData.questions.length) {
      setQuizIndex((prev) => prev + 1);
      setSelectedOption(null);
      setQuizSubmitted(false);
    } else {
      setQuizFinished(true);
    }
  }

  function handleQuizReset() {
    setQuizIndex(0);
    setSelectedOption(null);
    setQuizSubmitted(false);
    setQuizScore(0);
    setQuizFinished(false);
    setUserAnswers({});
  }

  const filteredSessions = savedSessions.filter((s) => {
    if (historyFilter === "all") return true;
    return s.session_type === historyFilter;
  });

  return (
    <section className="page page-reading learning-page">
      <header className="page-header">
        <p className="eyebrow">Study Intelligence</p>
        <h1>Grounded study material from your workspace.</h1>
        <p className="muted">
          Generate, practice, and persist summaries, flashcards, quizzes, and explanations verified against your academic documents.
        </p>
      </header>

      {!llmOnline && (
        <Card className="ollama-banner">
          <Icon name="cpu" size={20} />
          <div>
            <strong>Ollama is offline</strong>
            <p className="muted">
              Start Ollama locally with <code>ollama serve</code> to generate study materials.
            </p>
          </div>
        </Card>
      )}

      <Tabs activeId={activeTab} items={tabs} onChange={setActiveTab} />

      {activeTab !== "history" && (
        <Card>
          <p className="eyebrow">Study Focus</p>
          <div className="study-controls">
            <input
              className="study-input"
              disabled={loading}
              onChange={(e) => setTopic(e.target.value)}
              placeholder={
                activeTab === "explain"
                  ? "Enter concept to explain (e.g. TCP Slow Start, Dijkstra's algorithm)..."
                  : "Optional topic or concept (e.g. Memory Virtualization, Lecture 3)..."
              }
              type="text"
              value={topic}
            />

            <select
              className="study-select"
              disabled={loading}
              onChange={(e) => setSelectedDocId(e.target.value ? Number(e.target.value) : null)}
              value={selectedDocId ?? ""}
            >
              <option value="">All workspace documents</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.workspace_file_id}>
                  {doc.filename}
                </option>
              ))}
            </select>

            {(activeTab === "flashcards" || activeTab === "quiz") && (
              <select
                className="study-select"
                disabled={loading}
                onChange={(e) => setItemCount(Number(e.target.value))}
                value={itemCount}
              >
                <option value={3}>3 items</option>
                <option value={5}>5 items</option>
                <option value={10}>10 items</option>
              </select>
            )}

            {activeTab === "summary" && (
              <Button disabled={loading || !llmOnline} onClick={() => void handleGenerateSummary()} variant="primary">
                {loading ? "Generating..." : "Generate Summary"}
              </Button>
            )}

            {activeTab === "flashcards" && (
              <Button disabled={loading || !llmOnline} onClick={() => void handleGenerateFlashcards()} variant="primary">
                {loading ? "Generating..." : "Generate Flashcards"}
              </Button>
            )}

            {activeTab === "quiz" && (
              <Button disabled={loading || !llmOnline} onClick={() => void handleGenerateQuiz()} variant="primary">
                {loading ? "Generating..." : "Generate Quiz"}
              </Button>
            )}

            {activeTab === "explain" && (
              <Button disabled={loading || !llmOnline} onClick={() => void handleGenerateExplanation()} variant="primary">
                {loading ? "Explaining..." : "Explain Concept"}
              </Button>
            )}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "12px" }}>
            <div>
              {activeSessionId ? (
                <Badge tone="green">✓ Saved in Study Library (ID #{activeSessionId})</Badge>
              ) : (
                ((activeTab === "summary" && summaryData) ||
                  (activeTab === "flashcards" && flashcardData) ||
                  (activeTab === "quiz" && quizData) ||
                  (activeTab === "explain" && explanationData)) && (
                  <Button disabled={loading} onClick={() => void handleSaveSession()} variant="secondary">
                    <Icon name="bookmark" size={14} /> Save Session to Library
                  </Button>
                )
              )}
            </div>

            {saveSuccessMsg && (
              <small style={{ color: "var(--success)" }}>{saveSuccessMsg}</small>
            )}
          </div>

          {errorMessage && (
            <p className="status-error" style={{ marginTop: "12px", color: "var(--error)" }}>
              {errorMessage}
            </p>
          )}
        </Card>
      )}

      {/* --- TAB 1: SUMMARY --- */}
      {activeTab === "summary" && (
        <>
          {summaryData ? (
            <Card className="recommendation-card">
              <Badge tone="blue">Summary</Badge>
              <h2>{summaryData.title}</h2>
              <p style={{ fontSize: "15px", lineHeight: "24px" }}>{summaryData.overview}</p>

              {summaryData.key_points.length > 0 && (
                <div>
                  <h3 style={{ fontSize: "15px", margin: "16px 0 8px" }}>Key Takeaways</h3>
                  <ul className="study-points-list">
                    {summaryData.key_points.map((pt, idx) => (
                      <li className="study-point-item" key={idx}>
                        <span className="study-point-icon">
                          <Icon name="check" size={16} />
                        </span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {summaryData.citations.length > 0 && (
                <div style={{ marginTop: "16px" }}>
                  <p className="eyebrow">Source Grounding</p>
                  <div className="study-citation-grid">
                    {summaryData.citations.map((cite, idx) => (
                      <div className="study-citation-card" key={idx}>
                        <div className="study-citation-header">
                          <Icon name="fileText" size={16} />
                          <span>{cite.filename}</span>
                          {cite.relevance_score !== null && (
                            <small className="muted">({Math.round(cite.relevance_score * 100)}% match)</small>
                          )}
                        </div>
                        <p className="study-citation-snippet">"{cite.snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ) : (
            !loading && (
              <EmptyState
                action={
                  <Button disabled={!llmOnline} onClick={() => void handleGenerateSummary()} variant="primary">
                    Create your first summary
                  </Button>
                }
                description="Pick a topic or document above and generate an overview grounded in your notes."
                icon="book"
                title="No summary generated yet"
              />
            )
          )}
        </>
      )}

      {/* --- TAB 2: FLASHCARDS --- */}
      {activeTab === "flashcards" && (
        <>
          {flashcardData && flashcardData.cards.length > 0 ? (
            <div style={{ display: "grid", gap: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                  <Badge tone="blue">
                    Card {cardIndex + 1} of {flashcardData.cards.length}
                  </Badge>
                  {persistedCards[cardIndex] && (
                    <Badge
                      tone={
                        persistedCards[cardIndex].state === "mastered"
                          ? "green"
                          : persistedCards[cardIndex].state === "shaky"
                            ? "amber"
                            : "neutral"
                      }
                    >
                      {persistedCards[cardIndex].state.toUpperCase()} (Reviewed {persistedCards[cardIndex].review_count}x)
                    </Badge>
                  )}
                </div>
                <small className="muted">Click card or space to flip</small>
              </div>

              <button
                aria-pressed={cardFlipped}
                className={`flashcard ${cardFlipped ? "flipped" : ""}`}
                onClick={() => setCardFlipped((v) => !v)}
                type="button"
              >
                <span className="flashcard-face flashcard-front">
                  <small>Question</small>
                  <strong>{flashcardData.cards[cardIndex]?.question}</strong>
                  <span className="muted" style={{ fontSize: "12px", marginTop: "12px" }}>
                    (Click to reveal answer)
                  </span>
                </span>
                <span className="flashcard-face flashcard-back">
                  <small>Answer</small>
                  <strong>{flashcardData.cards[cardIndex]?.answer}</strong>

                  {flashcardData.cards[cardIndex]?.citations.length > 0 && (
                    <div style={{ marginTop: "16px", display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
                      {flashcardData.cards[cardIndex].citations.map((c, i) => (
                        <span className="citation-chip" key={i}>
                          <Icon name="fileText" size={14} />
                          <small>{c.filename}</small>
                        </span>
                      ))}
                    </div>
                  )}
                </span>
              </button>

              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", alignItems: "center" }}>
                <Button
                  disabled={cardIndex === 0}
                  onClick={() => {
                    setCardIndex((prev) => Math.max(0, prev - 1));
                    setCardFlipped(false);
                  }}
                  variant="secondary"
                >
                  Previous
                </Button>

                {activeSessionId && cardFlipped ? (
                  <div style={{ display: "flex", gap: "8px" }}>
                    <Button onClick={() => void handleFlashcardReview("shaky")} variant="secondary">
                      Still Shaky
                    </Button>
                    <Button onClick={() => void handleFlashcardReview("mastered")} variant="primary">
                      Got it!
                    </Button>
                  </div>
                ) : (
                  <Button onClick={() => setCardFlipped((v) => !v)} variant="secondary">
                    {cardFlipped ? "Show Question" : "Flip to Answer"}
                  </Button>
                )}

                <Button
                  disabled={cardIndex === flashcardData.cards.length - 1}
                  onClick={() => {
                    setCardIndex((prev) => Math.min(flashcardData.cards.length - 1, prev + 1));
                    setCardFlipped(false);
                  }}
                  variant="primary"
                >
                  Next Card
                </Button>
              </div>
            </div>
          ) : (
            !loading && (
              <EmptyState
                action={
                  <Button disabled={!llmOnline} onClick={() => void handleGenerateFlashcards()} variant="primary">
                    Generate flashcard deck
                  </Button>
                }
                description="Extract active recall flashcards from your study materials with source citations."
                icon="sparkle"
                title="No flashcards generated yet"
              />
            )
          )}
        </>
      )}

      {/* --- TAB 3: QUIZ --- */}
      {activeTab === "quiz" && (
        <>
          {quizData && quizData.questions.length > 0 ? (
            quizFinished ? (
              <Card className="session-card">
                <Icon name="target" size={32} />
                <h2>Quiz Completed!</h2>
                <p className="muted">
                  You scored {quizScore} out of {quizData.questions.length} (
                  {Math.round((quizScore / quizData.questions.length) * 100)}%).
                </p>
                <ProgressBar
                  label="Score"
                  value={Math.round((quizScore / quizData.questions.length) * 100)}
                />

                {quizAttempts.length > 0 && (
                  <div style={{ width: "100%", marginTop: "16px", textAlign: "left" }}>
                    <p className="eyebrow">Attempt History</p>
                    <div style={{ display: "grid", gap: "8px", marginTop: "8px" }}>
                      {quizAttempts.map((att, i) => (
                        <div
                          key={att.id || i}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            padding: "8px 12px",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: "6px",
                            fontSize: "13px",
                          }}
                        >
                          <span>Attempt #{quizAttempts.length - i}</span>
                          <strong>
                            {att.score} / {att.total_questions} ({Math.round((att.score / att.total_questions) * 100)}%)
                          </strong>
                          <span className="muted">{new Date(att.completed_at).toLocaleDateString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
                  <Button onClick={handleQuizReset} variant="secondary">
                    Retake Quiz
                  </Button>
                  <Button onClick={() => void handleGenerateQuiz()} variant="primary">
                    New Quiz
                  </Button>
                </div>
              </Card>
            ) : (
              <Card className="quiz-card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <p className="eyebrow">
                    Question {quizIndex + 1} of {quizData.questions.length}
                  </p>
                  <small className="muted">
                    Current Score: {quizScore} / {quizIndex + (quizSubmitted ? 1 : 0)}
                  </small>
                </div>

                <h2>{quizData.questions[quizIndex]?.question}</h2>

                <div style={{ display: "grid", gap: "8px" }}>
                  {quizData.questions[quizIndex]?.options.map((opt, optIdx) => {
                    const isSelected = selectedOption === optIdx;
                    const isCorrect = optIdx === quizData.questions[quizIndex].correct_index;
                    let extraClass = "";
                    if (quizSubmitted) {
                      if (isCorrect) extraClass = "correct";
                      else if (isSelected && !isCorrect) extraClass = "incorrect";
                    } else if (isSelected) {
                      extraClass = "selected";
                    }

                    return (
                      <button
                        className={`option-row ${extraClass}`}
                        disabled={quizSubmitted}
                        key={optIdx}
                        onClick={() => setSelectedOption(optIdx)}
                        type="button"
                      >
                        <strong>{String.fromCharCode(65 + optIdx)}.</strong> {opt}
                      </button>
                    );
                  })}
                </div>

                {quizSubmitted ? (
                  <div style={{ marginTop: "12px", display: "grid", gap: "12px" }}>
                    <div
                      style={{
                        padding: "12px 16px",
                        borderRadius: "8px",
                        background:
                          selectedOption === quizData.questions[quizIndex].correct_index
                            ? "var(--success-subtle, rgba(46, 160, 67, 0.15))"
                            : "var(--error-subtle, rgba(248, 81, 73, 0.15))",
                      }}
                    >
                      <strong>
                        {selectedOption === quizData.questions[quizIndex].correct_index
                          ? "✓ Correct!"
                          : "✕ Incorrect"}
                      </strong>
                      <p style={{ marginTop: "4px", fontSize: "14px", lineHeight: "20px" }}>
                        {quizData.questions[quizIndex].explanation}
                      </p>
                    </div>

                    {quizData.questions[quizIndex].citations.length > 0 && (
                      <div className="study-citation-grid">
                        {quizData.questions[quizIndex].citations.map((c, i) => (
                          <div className="study-citation-card" key={i}>
                            <div className="study-citation-header">
                              <Icon name="fileText" size={14} />
                              <span>{c.filename}</span>
                            </div>
                            <p className="study-citation-snippet">"{c.snippet}"</p>
                          </div>
                        ))}
                      </div>
                    )}

                    <Button onClick={handleQuizNext} variant="primary">
                      {quizIndex + 1 < quizData.questions.length ? "Next Question" : "View Results"}
                    </Button>
                  </div>
                ) : (
                  <Button
                    disabled={selectedOption === null}
                    onClick={() => void handleQuizSubmit()}
                    variant="primary"
                  >
                    Submit Answer
                  </Button>
                )}
              </Card>
            )
          ) : (
            !loading && (
              <EmptyState
                action={
                  <Button disabled={!llmOnline} onClick={() => void handleGenerateQuiz()} variant="primary">
                    Create practice quiz
                  </Button>
                }
                description="Test your understanding with multiple-choice questions grounded directly in your syllabus."
                icon="target"
                title="No quiz loaded"
              />
            )
          )}
        </>
      )}

      {/* --- TAB 4: EXPLAIN --- */}
      {activeTab === "explain" && (
        <>
          {explanationData ? (
            <Card className="recommendation-card">
              <Badge tone="blue">Explanation</Badge>
              <h2>{explanationData.topic}</h2>
              <p style={{ fontSize: "15px", lineHeight: "24px", whiteSpace: "pre-line" }}>
                {explanationData.explanation}
              </p>

              {explanationData.key_takeaways.length > 0 && (
                <div>
                  <h3 style={{ fontSize: "15px", margin: "16px 0 8px" }}>Key Takeaways</h3>
                  <ul className="study-points-list">
                    {explanationData.key_takeaways.map((takeaway, idx) => (
                      <li className="study-point-item" key={idx}>
                        <span className="study-point-icon">
                          <Icon name="zap" size={16} />
                        </span>
                        <span>{takeaway}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {explanationData.citations.length > 0 && (
                <div style={{ marginTop: "16px" }}>
                  <p className="eyebrow">Grounding References</p>
                  <div className="study-citation-grid">
                    {explanationData.citations.map((cite, idx) => (
                      <div className="study-citation-card" key={idx}>
                        <div className="study-citation-header">
                          <Icon name="fileText" size={16} />
                          <span>{cite.filename}</span>
                          {cite.relevance_score !== null && (
                            <small className="muted">({Math.round(cite.relevance_score * 100)}% match)</small>
                          )}
                        </div>
                        <p className="study-citation-snippet">"{cite.snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ) : (
            !loading && (
              <EmptyState
                action={
                  <Button
                    disabled={!llmOnline || !topic.trim()}
                    onClick={() => void handleGenerateExplanation()}
                    variant="primary"
                  >
                    Explain concept
                  </Button>
                }
                description="Type a concept in the Study Focus box above and Rune will break it down using your course material."
                icon="zap"
                title="Enter a concept to explain"
              />
            )
          )}
        </>
      )}

      {/* --- TAB 5: SAVED SESSIONS (HISTORY) --- */}
      {activeTab === "history" && (
        <div style={{ display: "grid", gap: "16px" }}>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
            <span className="muted" style={{ fontSize: "13px", marginRight: "8px" }}>Filter:</span>
            {["all", "summary", "flashcards", "quiz", "explanation"].map((ft) => (
              <Button
                key={ft}
                onClick={() => setHistoryFilter(ft)}
                size="sm"
                variant={historyFilter === ft ? "primary" : "secondary"}
              >
                {ft === "all" ? "All Saved" : ft.charAt(0).toUpperCase() + ft.slice(1)}
              </Button>
            ))}
          </div>

          {filteredSessions.length > 0 ? (
            <div style={{ display: "grid", gap: "12px" }}>
              {filteredSessions.map((session) => (
                <Card
                  key={session.id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "16px 20px",
                    cursor: "pointer",
                    border: activeSessionId === session.id ? "1px solid var(--accent-primary)" : undefined,
                  }}
                >
                  <div
                    onClick={() => void handleLoadSession(session)}
                    style={{ flex: 1, display: "grid", gap: "4px" }}
                  >
                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      <Badge
                        tone={
                          session.session_type === "quiz"
                            ? "amber"
                            : session.session_type === "flashcards"
                              ? "green"
                              : session.session_type === "summary"
                                ? "blue"
                                : "violet"
                        }
                      >
                        {session.session_type.toUpperCase()}
                      </Badge>
                      <strong>{session.title}</strong>
                      {activeSessionId === session.id && (
                        <small style={{ color: "var(--accent-primary)" }}>(Active)</small>
                      )}
                    </div>

                    <div style={{ display: "flex", gap: "16px", fontSize: "13px", color: "var(--text-secondary)" }}>
                      <span>Saved: {new Date(session.created_at).toLocaleDateString()}</span>
                      {session.item_count > 0 && <span>{session.item_count} items</span>}
                      {session.attempt_count > 0 && (
                        <span>
                          {session.attempt_count} attempts {session.best_score !== null && `(Best: ${session.best_score})`}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <Button onClick={() => void handleLoadSession(session)} size="sm" variant="secondary">
                      Open / Practice
                    </Button>
                    <Button
                      onClick={(e) => void handleDeleteSession(session.id, e)}
                      size="sm"
                      variant="ghost"
                    >
                      <Icon name="trash" size={16} />
                    </Button>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <EmptyState
              action={
                <Button onClick={() => setActiveTab("summary")} variant="primary">
                  Create study session
                </Button>
              }
              description="Save summaries, flashcards, or quizzes after generating them to build your study library."
              icon="book"
              title="No saved study sessions yet"
            />
          )}
        </div>
      )}
    </section>
  );
}
