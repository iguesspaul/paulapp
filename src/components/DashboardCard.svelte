<script lang="ts">
    import type { Snippet } from "svelte";
    import arrow from "iconoir/icons/arrow-up-right.svg";

    let {
        title,
        href,
        children,
        class: className = "",
    }: {
        title?: string;
        href?: string;
        children?: Snippet;
        class?: string;
    } = $props();

    let isLink = $derived(!!href);
    let classes = $derived(`bg-surface p-4 flex flex-col overflow-hidden ${isLink ? 'group hover:scale-[1.02] hover:bg-raised hover:shadow-xl hover:z-10 transition-all duration-300 relative transform-gpu cursor-pointer shrink-0 gap-4' : ''} ${className}`);
</script>

{#snippet content()}
    {#if title}
        <h2
            class="text-xl font-mono text-text-primary tracking-widest drop-shadow font-medium shrink-0 {isLink ? '' : 'mb-4'}"
        >
            {title}
        </h2>
    {/if}

    {@render children?.()}

    {#if isLink}
        <div class="absolute top-2 right-2">
            <img
                src={arrow}
                alt={title ? `Go to ${title}` : "Link arrow"}
                class="w-4 h-4 invert invisible group-hover:visible"
            />
        </div>
    {/if}
{/snippet}

{#if isLink}
    <a {href} class={classes}>
        {@render content()}
    </a>
{:else}
    <div class={classes}>
        {@render content()}
    </div>
{/if}
