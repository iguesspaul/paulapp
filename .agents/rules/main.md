---
trigger: always_on
---

# Paulapp AI Directives

**Context**: Personal desktop app. Ignore standard security (SQL injection, auth). Optimize for developer speed.
**Stack**: Svelte 5, Tailwind v4, pnpm, Tauri, Rust, SQLite.

## Architecture & Rules

**1. Rust Backend**
- **Models**: Define ALL structs/models in `src-tauri/src/models.rs`.
- **Logging**: Log to `stderr` with `[module_name]` prefix.
- **Docs**: Update `src-tauri/src/RUST_DEBUG.md` on every backend change (API, structs, errors). Reference it for debugging.

**2. Frontend API**
- **Facades**: Create TS facades at `src/lib/{feature}/api.ts`.
- **Casing**: Pass parameters in `camelCase` in TS. Tauri handles `snake_case` conversion automatically.

**3. Design (Warm Brutalism)**
- **References**: Follow `design/design-system.md` and `@theme` in `src/app.css`. Use theme color classes preferentially.
- **Rules**: No rounded corners. Deep charcoal (`#111111`) backgrounds. Cobalt blue & Amber accents. Monospace typography. High density layout.

**4. Documentation**
- **Frontend Issues**: Document UI/CSS bug fixes (symptom, root cause, solution) in `src/routes/FRONTEND.md`.

**5. Scaffolding**
- **Automation**: Run `npm run scaffold <feature-name>` via `run_command` (`SafeToAutoRun: true`) for new features. Do this before writing boilerplate.

## Output Protocol
- Zero conversational fluff, summaries, or checklists.
- Output only code or modifications.
- Begin response with exactly: "I'm completing the task."
- End response with exactly: "completed."