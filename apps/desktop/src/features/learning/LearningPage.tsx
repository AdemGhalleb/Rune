import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { ProgressBar } from "@/components/ui/ProgressBar";
import { Tabs } from "@/components/ui/Tabs";

const tabs = [
  { id: "review", label: "Review Session" },
  { id: "flashcards", label: "Flashcards" },
  { id: "quiz", label: "Quiz Mode" },
];

export function LearningPage() {
  const [activeTab, setActiveTab] = useState("review");
  const [flipped, setFlipped] = useState(false);
  const [selectedOption, setSelectedOption] = useState("Higher responsiveness with context-switch overhead");

  return (
    <section className="page page-reading learning-page">
      <header className="page-header">
        <p className="eyebrow">Learning</p>
        <h1>Practice what actually needs practice.</h1>
        <p className="muted">Queues are assembled from weak concepts and review decay. Data shown here is temporary.</p>
      </header>

      <Tabs activeId={activeTab} items={tabs} onChange={setActiveTab} />

      <Card className="recommendation-card">
        <Badge tone="warning">Recommended</Badge>
        <h2>Process Scheduling · 12 minute review</h2>
        <p className="muted">Weak spot, last touched 9 days ago, connected to two upcoming lab tasks.</p>
        <ProgressBar value={62} label="Current mastery" />
      </Card>

      {activeTab === "review" && (
        <Card className="session-card">
          <Icon name="target" size={24} />
          <h2>Ready for a focused review?</h2>
          <p className="muted">One card at a time. No deck management, no busy dashboard gymnastics.</p>
          <Button variant="primary">Begin session</Button>
        </Card>
      )}

      {activeTab === "flashcards" && (
        <button
          aria-pressed={flipped}
          className={`flashcard ${flipped ? "flipped" : ""}`}
          onClick={() => setFlipped((currentValue) => !currentValue)}
          type="button"
        >
          <span className="flashcard-face flashcard-front">
            <small>Question</small>
            <strong>What makes a time quantum too small in round-robin scheduling?</strong>
          </span>
          <span className="flashcard-face flashcard-back">
            <small>Answer</small>
            <strong>Context-switch overhead begins to dominate useful CPU work.</strong>
          </span>
        </button>
      )}

      {activeTab === "quiz" && (
        <Card className="quiz-card">
          <p className="eyebrow">Question 1 of 5</p>
          <h2>Which tradeoff best describes round-robin scheduling?</h2>
          {["Lowest memory usage", "Higher responsiveness with context-switch overhead", "No starvation ever", "Strict priority ordering"].map(
            (option) => (
              <button
                className={`option-row ${selectedOption === option ? "selected" : ""}`}
                key={option}
                onClick={() => setSelectedOption(option)}
                type="button"
              >
                {option}
              </button>
            ),
          )}
          <Button variant="primary">Submit answer</Button>
        </Card>
      )}
    </section>
  );
}
