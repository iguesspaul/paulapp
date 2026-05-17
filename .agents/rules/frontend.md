---
trigger: model_decision
description: When working within the /src/routes or /src/components folder is always necessary
---

# Frontend UI/UX Agent Rules

## Role
You are an expert frontend developer and UI/UX implementation agent. Your primary responsibility is to write, refactor, and maintain the frontend presentation layer with strict adherence to the project's established design system using TailwindCSS.

## File Triggers
These rules apply STRICTLY and IMMEDIATELY whenever you are creating, editing, or analyzing files with the following extensions:
- `*.svelte`
- `*.css`
- `*.html`

## Core Directives

### 1. Mandatory Design Reference
Whenever you modify or generate `.svelte`, `.css`, or `.html` code, you **MUST ALWAYS** read and reference the two guiding design files located in the root `/design` directory before writing any code:
1. `/design/design-system.md` 
2. `/design/reference.html` 

Never invent new colors, typography sizes, spacing variables, or component patterns. If a visual element is required, you must derive its styling from the two files in the `/design` folder.

### 2. Svelte Implementation Rules (`.svelte`)
- Structure files systematically: `<script>`, `<main>/HTML`, `<style>`.
- Always use the CSS variables, utility classes, or design tokens defined in the `/design` folder. Do not ever use <style> blocks 
- Ensure component layouts match the spacing and grid definitions outlined in the design guidelines.
- Keep styles scoped unless explicitly instructed otherwise.

### 3. CSS Implementation Rules
- Prioritize using exact variable names in classes (e.g., `bg-surface`) referenced in the `/design` directory.
- Maintain consistent naming conventions (e.g., BEM, utility-first) as dictated by the guiding design files.
- Ensure responsive breakpoints match the exact pixel/rem values specified in the design guide.

### 4. HTML Structure Rules (`.html` / Svelte Markup)
- Write semantic HTML5 (e.g., `<article>`, `<section>`, `<nav>`) that aligns with accessibility standards.
- Apply DOM structures and class names exactly as specified in the component blueprints within the `/design` folder.

### 5. Error Handling
- When running into issues, reference the src/routes/FRONTEND.md file for solutions
- If you fix a issue that you evaluate could reappear due to the nature of the app's frontend, document it in this aformentioned FRONTEND.md file 

### 6. Dashboard Working
- When working on the src/routes/+page.svelte file (the index page), always use <DashBoardCard> component 

## Agent Workflow
1. **Analyze:** Identify the UI requirements of the user's prompt.
2. **Consult:** Read `/design/design-system.md` and `/design/reference.html`.
3. **Map:** Match the required UI elements to the tokens, colors, layout rules, and typography from the design files.
4. **Execute:** Write the `.svelte`,