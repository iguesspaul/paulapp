# Frontend Debugging & Known Issues

This document serves as a repository for known UI/UX, styling, and rendering issues encountered in the frontend of this application. When encountering unusual frontend behavior, reference this document before attempting layout overhauls.

## 1. Hover Scale Clipping in Grid/Flex Layouts
**Symptom:**
When a container (like a link box or dashboard card) is set to scale on hover (e.g., `hover:scale-[1.02]`), the text inside the container scales up visually, but the background box appears to remain the same size or gets its edges sliced off.

**Root Cause:**
The parent column or container holding the scaling element has a clipping property applied, typically `overflow-hidden` or `overflow-y-auto`. When the child element scales up, its physical boundaries expand beyond the parent container's bounds. The parent container then clips those expanded boundaries, creating the optical illusion that only the text is scaling while the box is stuck at its original size.

**Solution:**
Remove the clipping context from the parent layout container. 
- Replace `overflow-hidden` or `overflow-y-auto` on the parent layout wrapper with `min-h-0`.
- Ensure the parent column does not restrict the visual expansion of its children.
- If specific internal blocks need scrolling, apply `overflow-y-auto` to those individual blocks rather than the whole column.

## 2. Invisible Button Text due to Tailwind Custom Color Variable Naming
**Symptom:**
A button or text element appears to be a solid block of color with no visible text, despite having a text color class applied (e.g., `text-inverse`). 

**Root Cause:**
The custom CSS variable defining the color is named `--color-text-inverse`. In Tailwind CSS v4, when referencing custom colors prefixed with `--color-`, the class name must match the suffix exactly. The class `text-inverse` does not resolve to `--color-text-inverse`; instead, it resolves to nothing, causing the text to inherit the color of its parent container. Since the button background was `bg-text-primary` and the text color defaulted to `text-text-primary`, the text was indistinguishable from the background.

**Solution:**
Ensure the Tailwind class name exactly matches the suffix of the `--color-` variable.
- Replace `text-inverse` with `text-text-inverse`.

## 3. `<svelte:element>` Type Errors with Conditional Attributes
**Symptom:**
When using `<svelte:element this={Tag}>` where `Tag` is reactive (e.g. `$derived(isLink ? 'a' : 'div')`), passing attributes that only belong to one of those elements (like `href={href}`) causes a TypeScript error in `pnpm run check`: `Object literal may only specify known properties, and 'href' does not exist in type 'HTMLAttributes<any>'`.

**Root Cause:**
Svelte's type checker for `<svelte:element>` does not dynamically intersect the attributes of all possible tags. It expects the props to be universally valid for `HTMLAttributes<any>`, so passing an `href` to something that *might* be a `<div>` causes a strict typing failure.

**Solution:**
Do not use `<svelte:element>` for conditional tags that require specific attributes. Instead, utilize Svelte 5 snippets (`{#snippet}`) to define the inner content once, and render it inside standard conditional HTML tags:

```svelte
{#snippet content()}
    <!-- Inner markup -->
{/snippet}

{#if isLink}
    <a href={href}>
        {@render content()}
    </a>
{:else}
    <div>
        {@render content()}
    </div>
{/if}
```
