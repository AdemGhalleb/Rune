# Rune — User Guide

This guide is for students using Rune day-to-day. No technical background required. If you're a developer looking for architecture details instead, see [`README.md`](./README.md).

---

## Table of Contents

1. [First-Time Setup](#first-time-setup)
2. [Workspace Management](#workspace-management)
3. [Using the AI Assistant](#using-the-ai-assistant)
4. [The Memory System](#the-memory-system)
5. [Privacy](#privacy)

---

## First-Time Setup

### 1. Install Rune

Download the installer for your operating system from the Releases page and run it, the same as any other desktop application. No account is required to use Rune.

### 2. Choose your workspace

On first launch, Rune will ask you to select one or more folders where you keep your academic material — lecture PDFs, notes, assignments, past exams, whatever you already have. Rune **does not move, copy, or reorganize your files.** It reads them where they already are.

A little organization helps but isn't required to get started:

```
My University Files/
├── Operating Systems/
│   ├── lectures/
│   ├── notes/
│   └── past exams/
├── Algorithms/
│   ├── lectures/
│   └── assignments/
```

If your files are folder-per-course, Rune will automatically associate documents with the right course. If your files are less organized, that's fine too — you can tag documents by course afterward from within the app.

### 3. Let it index

After you select a workspace, Rune reads through your files and builds its internal knowledge base — this is the one-time step that lets it later answer questions grounded in your actual material. Indexing runs in the background; you don't have to wait for it to finish before starting to explore the app, but answers will get better as more of your workspace finishes processing. A large workspace (hundreds of files) may take a while the first time; after that, only new or changed files need to be processed.

---

## Workspace Management

### Adding a course

Create a folder for the course inside your workspace (or tag existing documents with a course from within the app) — Rune picks it up automatically.

### Adding new files

Drop a new file into your workspace folder as normal. Rune's file watcher notices it and queues it for indexing — no manual "re-scan" step needed.

### Modifying files

If you edit a file (say, you update your notes), Rune detects the change and re-indexes just that file, not your entire workspace. This keeps things fast even as your workspace grows over a semester.

### Deleting files

If you delete a file from your workspace, Rune removes it from its knowledge base too, so old or removed material won't show up in answers.

### How synchronization behaves

Rune watches your workspace continuously while the app is running. If you make changes while Rune isn't open, it catches up and reconciles everything the next time you launch it — nothing gets permanently missed.

---

## Using the AI Assistant

Once your workspace is indexed, you can ask Rune questions grounded in your own material. Some examples of what works well:

- *"Explain chapter 3 of Operating Systems."*
- *"Create a revision plan for my algorithms exam."*
- *"Find similarities between these two lectures."*
- *"What did my professor say about the project deadline in last week's lecture?"*
- *"Quiz me on the topics I've been struggling with in this course."*

Rune answers using your actual lecture material, notes, and past exams rather than generic knowledge — and it will tell you when something isn't covered in your workspace rather than guessing.

You can also point Rune at specific gaps: asking it to focus on a topic you're unsure about, or to generate practice questions targeting the areas you've struggled with historically, tends to be more useful than general "explain everything" requests.

---

## The Memory System

### What Rune remembers

Rune keeps track of durable, useful information about how you study and where you're strong or weak — for example, that you tend to struggle with a particular topic, that you prefer concise explanations over long ones, or that you have an upcoming exam. It does **not** keep a running transcript of every conversation as "memory" — small talk and one-off questions aren't stored.

### Why it remembers

The goal is for Rune to get more useful the longer you use it, rather than starting from zero in every conversation — the same way a human tutor would remember that you already understand recursion but keep tripping up on dynamic programming.

### Viewing and deleting memories

You can see everything Rune has stored about you from the Memory section of the app, and delete anything you don't want it to keep. Nothing is permanent or hidden from you.

---

## Privacy

### Where your data is stored

Everything — your indexed documents, your knowledge base, your memory, your conversation history — is stored locally on your own machine. Rune does not require a server account, and by default nothing about your academic material leaves your computer.

### What leaves the machine

Nothing, by default. If you choose to enable a cloud AI provider (optional, and off unless you turn it on), only the specific text needed for that request — for example, your question and the retrieved passages relevant to it — is sent to that provider, under their own privacy terms. Your files themselves are never uploaded anywhere.

If you connect email or calendar integrations (a future feature), those connections use your own account credentials and narrow, read-focused permissions — Rune will never take an action on your behalf (like sending an email) without asking you first.

### Local models vs. cloud models

By default, Rune uses a local model running on your own machine via Ollama — nothing about your documents or questions leaves your computer, and there's no cost per use. You can optionally configure a cloud model (like an OpenAI model) if you want stronger reasoning and are comfortable with that provider's terms — this is always an explicit, per-feature choice, never a default.

---

Questions, issues, or feedback? Open an issue on the project's GitHub repository.
