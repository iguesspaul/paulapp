<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { loadCountdowns, type Countdown } from "../../lib/countdowns/api";
    import { getCountdownDisplay } from "../../lib/utils/date";
    import { onMount } from "svelte";

    let countdowns: Countdown[] = [];
    let isLoading = true;

    onMount(async () => {
        try {
            const cRes = await loadCountdowns();
            countdowns = cRes.countdowns;
        } catch (error) {
            console.error("Error loading countdowns:", error);
        } finally {
            isLoading = false;
        }
    });
</script>

<DashboardCard href="/countdowns" title="countdowns">
    <div class="flex flex-col gap-2 font-mono">
        {#if isLoading}
            <div class="text-text-primary/80 text-sm">Loading countdowns...</div>
        {:else if countdowns.length > 0}
            {#each countdowns as countdown}
                {@const { daysRemaining, isToday } = getCountdownDisplay(countdown.target_timestamp)}
                <div class="flex flex-row justify-between items-center text-sm border-b border-divider pb-2 last:border-0 last:pb-0">
                    <span class="text-text-primary max-w-[60%] truncate">{countdown.name}</span>
                    <div class="flex flex-row items-baseline gap-1">
                        {#if isToday}
                            <span class="text-amber font-bold text-lg">TODAY!</span>
                        {:else}
                            <span class="text-amber font-bold text-lg">{daysRemaining}</span>
                            <span class="text-xs text-text-primary/40 uppercase">days</span>
                        {/if}
                    </div>
                </div>
            {/each}
        {:else}
            <div class="text-text-primary/80 text-sm">
                No countdowns found.
            </div>
        {/if}
    </div>
</DashboardCard>
