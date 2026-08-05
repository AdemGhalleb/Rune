import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { chatMessages } from "@/lib/data/demoData";

export function ChatPage() {
  return (
    <section className="page page-reading chat-page">
      <header className="page-header">
        <p className="eyebrow">Chat</p>
        <h1>Ask against your course material.</h1>
        <p className="muted">Temporary conversation data until the chat service is connected.</p>
      </header>

      <div className="chat-thread" aria-label="Conversation">
        {chatMessages.map((message) => (
          <article className={`message message-${message.role}`} key={message.id}>
            <p>{message.body}</p>
            {"sources" in message && message.sources && (
              <div className="citation-row">
                {message.sources.map((source) => (
                  <button className="citation-chip" key={source} type="button">
                    <Icon name="fileText" size={16} />
                    {source}
                  </button>
                ))}
              </div>
            )}
          </article>
        ))}
        <div className="thinking-row">
          <span className="thinking-dots" aria-hidden="true" />
          <span>Searching Operating Systems notes...</span>
          <button type="button">Show details</button>
        </div>
        <Card className="inline-artifact">
          <div>
            <Badge tone="info">Generated practice</Badge>
            <h2>5 quick questions on scheduling tradeoffs</h2>
            <p className="muted">A short review set based on the sources used in this answer.</p>
          </div>
          <Button variant="secondary">Start</Button>
        </Card>
      </div>

      <form className="composer">
        <label className="sr-only" htmlFor="chat-input">
          Message Rune
        </label>
        <textarea id="chat-input" placeholder="Ask about a lecture, assignment, or weak concept..." rows={3} />
        <div className="composer-footer">
          <span>Grounded in selected course · citations appear after responses</span>
          <Button variant="primary" type="submit">
            Send
          </Button>
        </div>
      </form>
    </section>
  );
}
