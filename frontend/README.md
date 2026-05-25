# Frontend — Q&A Paradigm Lab UI

Next.js 16 + App Router + Tailwind v4 + Turbopack. Five tabs reflecting
the five views of the project:

| Route          | Purpose                                                    |
|----------------|------------------------------------------------------------|
| `/rag`         | Single-paradigm chat for traditional RAG                   |
| `/agentic`     | Single-paradigm chat for Agentic Search                    |
| `/graphrag`    | Single-paradigm chat for GraphRAG                          |
| `/compare`     | Side-by-side three-column comparison (demo centerpiece)    |
| `/matrix`      | Static decision matrix populated from evaluation results   |

All five are currently **placeholder pages** rendering only their title
and a "Coming soon" line. Backend integration and the real UI land in
later commits.

## Layout

```
frontend/
├── app/
│   ├── layout.tsx              Root layout (nav bar + main container)
│   ├── page.tsx                Home / landing
│   ├── globals.css             Tailwind v4 theme tokens
│   ├── _components/
│   │   └── nav-bar.tsx         Top nav with active-tab highlight (Client)
│   ├── rag/page.tsx
│   ├── agentic/page.tsx
│   ├── graphrag/page.tsx
│   ├── compare/page.tsx
│   └── matrix/page.tsx
├── package.json
├── tsconfig.json
└── next.config.ts
```

## Prerequisites

- Node 20.19+ / 22.13+ / 24+ recommended (Node 23 works with a benign
  `EBADENGINE` warning during install)
- npm 10+

## Setup

```bash
cd frontend
npm install
```

## Running locally

```bash
npm run dev
```

The dev server runs on <http://localhost:3000>. Turbopack is enabled by
default.

## Build

```bash
npm run build   # production build
npm run start   # serve the production build
npm run lint    # ESLint (next-config based)
```

## Working with Next.js 16

This project uses Next.js 16, which has breaking changes from earlier
versions. The auto-generated [`AGENTS.md`](./AGENTS.md) at the project
root notes this — when writing new routes or layouts, consult
`node_modules/next/dist/docs/` for the canonical reference rather than
relying on training-data memory of earlier Next.js versions.
