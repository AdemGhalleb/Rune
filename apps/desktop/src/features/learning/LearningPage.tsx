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
  type FlashcardSetResponse,
  type QuizResponse,
  type SummaryResponse,
  type WorkspaceDocument,
  fetchLlmStatus,
  fetchWorkspaceDocuments,
  generateExplanation,
  generateFlashcards,
  generateQuiz,
  generateSummary,
} from "@/lib/api/client";
import { useWorkspace } from "@/lib/workspace/WorkspaceProvider";

const tabs = [
  { id: "summary", label: "Summarize" },
  { id: "flashcards", label: "Flashcards" },
  { id: "quiz", label: "Quiz Mode" },
  { id: "explain", label: "Explain Concept" },
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

  // Study Results State
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
    }
  }, [workspace]);

  // Handlers for Generation
  async function handleGenerateSummary() {
    setLoading(true);
    setErrorMessage(null);
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

  // Quiz Navigation
  function handleQuizSubmit() {
    if (selectedOption === null || !quizData) return;
    const currentQ = quizData.questions[quizIndex];
    if (selectedOption === currentQ.correct_index) {
      setQuizScore((prev) => prev + 1);
    }
    setQuizSubmitted(true);
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
  }

  return (
    <section className="page page-reading learning-page">
      <header className="page-header">
        <p className="eyebrow">Study Intelligence</p>
        <h1>Grounded study material from your workspace.</h1>
        <p className="muted">
          Generate summaries, flashcards, quizzes, and explanations verified against your academic documents.
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

      {/* Target Scope & Material Selector */}
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

        {errorMessage && (
          <p className="status-error" style={{ marginTop: "12px", color: "var(--error)" }}>
            {errorMessage}
          </p>
        )}
      </Card>

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
                <Badge tone="blue">
                  Card {cardIndex + 1} of {flashcardData.cards.length}
                </Badge>
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

              <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
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

                <Button onClick={() => setCardFlipped((v) => !v)} variant="secondary">
                  {cardFlipped ? "Show Question" : "Flip to Answer"}
                </Button>

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
                    onClick={handleQuizSubmit}
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
    </section>
  );
}
