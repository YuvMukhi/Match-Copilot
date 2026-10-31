# Match Copilot 🏏🤖

> **Explainable AI assistant for live fantasy cricket fans**
> 
> *Disclaimer: Sample data. Not official Dream11 scoring.*

Match Copilot helps fantasy cricket fans understand and act on their team's performance during a live match.

## Core Design Principle (Non-Negotiable)
**The LLM must NEVER calculate points or numbers itself.**
All numbers originate from a deterministic scoring/projection engine in code. The LLM receives structured results via tool calling and only explains, recommends, and converses. Every answer is traceable to computed numbers.

## Features
1. **EXPLAIN**: "Why did I lose/gain points?" Compare team points between match moments and inspect ball-by-ball breakdown.
2. **ADVISE**: "Should I change my captain?" Rest-of-match projected points with risk flags and tactical fixes.
3. **WHAT-IF / ESTIMATE**: "What if rain cuts the match to 15 overs?" Approximate DLS target projection and player point ranges (low / expected / high).

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 + SQLite, Alembic migrations, pytest.
- **LLM**: Anthropic Claude API with tool use + Mock LLM mode (offline ready).
- **Frontend**: React + TypeScript (strict) + Vite + Tailwind CSS.
- **Deployment**: Single Dockerfile + `render.yaml`.
