<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { getWhoopAuthUrl, getWhoopSleepScore, type SleepScore } from "../../lib/whoop/api";
    import { onMount } from "svelte";

    let sleepScore: SleepScore | null = null;
    let sleepScoreError = "";

    onMount(async () => {
        try {
            sleepScore = await getWhoopSleepScore();
        } catch (error: any) {
            console.error("Error loading sleep score:", error);
            sleepScoreError = error.toString();
        }
    });
</script>

<DashboardCard class="justify-end shrink-0">
    {#if sleepScore}
        <div class="flex flex-row gap-1 justify-between items-end mt-2">
            <h2 class="text-xl font-mono text-text-primary tracking-widest drop-shadow font-medium">
                sleep
            </h2>
            <span
                class="text-4xl md:text-6xl font-mono {sleepScore.sleepPerformancePercentage > 85
                    ? 'text-success'
                    : sleepScore.sleepPerformancePercentage > 65
                        ? 'text-warning'
                        : 'text-danger'}"
            >
                {Math.round(sleepScore.sleepPerformancePercentage)}%
            </span>
        </div>
    {:else if sleepScoreError.includes("Not authenticated") || sleepScoreError.includes("WHOOP_API")}
        <button
            class="bg-warning/20 text-warning hover:bg-warning/40 p-2 font-mono text-sm uppercase mt-auto"
            on:click={async () => {
                const url = await getWhoopAuthUrl();
                window.location.href = url;
            }}
        >
            Connect
        </button>
    {:else}
        <div class="text-text-primary/60 text-sm font-mono mt-auto">
            --
        </div>
    {/if}
</DashboardCard>
