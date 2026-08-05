import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { graphEdges, graphNodes } from "@/lib/data/demoData";

export function GraphPage() {
  const [selectedNodeId, setSelectedNodeId] = useState("deadlock");
  const selectedNode = graphNodes.find((node) => node.id === selectedNodeId);

  return (
    <section className="page page-wide graph-page">
      <header className="page-header dashboard-header">
        <div>
          <p className="eyebrow">Knowledge Graph</p>
          <h1>Concept mastery, not file spaghetti.</h1>
          <p className="muted">Nodes represent course concepts; color and size express mastery and centrality.</p>
        </div>
        <Badge tone="blue">Operating Systems</Badge>
      </header>

      <div className="graph-layout">
        <Card className="graph-canvas">
          {graphNodes.length === 0 ? (
            <EmptyState
              description="Mastery tracking appears after Rune has enough study, chat, and practice signals."
              icon="graph"
              title="No mastery map yet"
            />
          ) : (
            <svg aria-label="Operating Systems concept mastery graph" role="img" viewBox="0 0 680 440">
              {graphEdges.map(([from, to, strength]) => {
                const source = graphNodes.find((node) => node.id === from);
                const target = graphNodes.find((node) => node.id === to);
                if (!source || !target) {
                  return null;
                }
                const connected = from === selectedNodeId || to === selectedNodeId;
                return (
                  <line
                    className={connected ? "graph-edge active" : "graph-edge dimmed"}
                    key={`${from}-${to}`}
                    strokeWidth={strength}
                    x1={source.x}
                    x2={target.x}
                    y1={source.y}
                    y2={target.y}
                  />
                );
              })}
              {graphNodes.map((node) => {
                const selected = node.id === selectedNodeId;
                const connected = graphEdges.some(
                  ([from, to]) =>
                    (from === selectedNodeId && to === node.id) || (to === selectedNodeId && from === node.id),
                );
                return (
                  <g
                    className={`${selected ? "graph-node selected" : connected ? "graph-node connected" : "graph-node dimmed"} ${getMasteryClass(node.mastery)}`}
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        setSelectedNodeId(node.id);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                  >
                    <circle cx={node.x} cy={node.y} r={node.weight / 2} />
                    <text x={node.x} y={node.y + node.weight / 2 + 20}>
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          )}
        </Card>

        {selectedNode && (
          <Card className="graph-panel">
            <p className="eyebrow">Selected concept</p>
            <h2>{selectedNode.label}</h2>
            <p className="muted">Last practiced 9 days ago. Strongly connected to synchronization and threads.</p>
            <div className="mastery-meter">
              <span>{selectedNode.mastery}% mastery</span>
              <div>
                <span style={{ width: `${selectedNode.mastery}%` }} />
              </div>
            </div>
            <Button variant="primary">Practice this</Button>
            <Button variant="secondary">Ask about this</Button>
          </Card>
        )}
      </div>
    </section>
  );
}

function getMasteryClass(mastery: number) {
  if (mastery < 50) {
    return "mastery-low";
  }
  if (mastery < 70) {
    return "mastery-mid";
  }
  return "mastery-high";
}
