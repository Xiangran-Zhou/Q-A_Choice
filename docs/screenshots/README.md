# Screenshots

Place screenshots here using the filenames below. The Chinese
README (`README.zh-CN.md`) embeds these images by relative path, so
once you drop the PNGs in, the report renders end-to-end.

## Required files

| Filename | What to capture | Suggested viewport |
|---|---|---|
| `matrix.png` | The `/matrix` page showing the full 3-paradigm score grid with the M3 banner hidden | 1440 × ~1800 (full page) |
| `compare.png` | The `/compare` page **after submitting a question** — ideally a multi-hop one like Q 2.2 so GraphRAG / Agentic both shine. Capture once all three columns finish rendering. | 1440 × ~1200 |
| `rag.png` | The `/rag` page after asking Q 1.3 ("LangSmith free plan traces") — captures a 3-point answer + the chunks panel expanded | 1440 × ~1400 |
| `agentic.png` | The `/agentic` page after asking Q 2.3 ("ConversationBufferMemory deprecation") — captures a multi-tool answer + the tool-call timeline expanded | 1440 × ~1400 |
| `graphrag.png` | The `/graphrag` page after asking Q 2.3 (same question — comparison is implicit) | 1440 × ~1400 |

## How to capture (macOS)

1. Start the backend + frontend (see top-level README §6 + §7)
2. Open the page in Chrome / Safari
3. **Cmd + Shift + 4**, then **Space**, then click the browser window
4. Save the resulting PNG into this directory with the exact filename above

For full-page captures (the matrix page is longer than one viewport),
use Chrome DevTools:
- Cmd+Option+I → open DevTools
- Cmd+Shift+P → "Capture full size screenshot"
- Saves to your Downloads folder; move + rename here

## Optional / nice-to-have

| Filename | What to capture |
|---|---|
| `home.png` | The `/` landing page with the 5-tab nav and the project intro |
| `architecture.png` | A rendered version of the architecture diagram (if you'd rather show it as an image than ASCII art) |

## Gitignore

These PNGs are NOT gitignored — drop them in and commit them so they
ship with the repo. The directory itself is tracked via this README.
