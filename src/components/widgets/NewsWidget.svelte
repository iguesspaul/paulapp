<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { getNewsSummary } from "../../lib/ai/api";
    import { onMount } from "svelte";

    let newsSummary = "";

    onMount(async () => {
        try {
            newsSummary = await getNewsSummary();
        } catch (error) {
            console.error("Error loading news summary:", error);
            newsSummary = "Failed to load news summary. Is Ollama running locally?";
        }
    });
</script>

<DashboardCard class="flex-1 min-h-0 overflow-y-auto gap-4" title="news">
    <div class="text-text-primary/80 font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {#if newsSummary}
            {newsSummary}
        {:else}
            Loading daily AI summary...
        {/if}
    </div>
</DashboardCard>
