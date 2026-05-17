<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { getUVIndex, type UVIndexResponse } from "../../lib/weather/api";
    import { onMount } from "svelte";

    let uvData: UVIndexResponse | null = null;

    onMount(async () => {
        try {
            uvData = await getUVIndex();
        } catch (error) {
            console.error("Error loading UV index:", error);
        }
    });
</script>

<DashboardCard class="justify-end shrink-0">
    {#if uvData}
        <div class="flex flex-row gap-1 justify-between items-end mt-2">
            <div class="flex flex-col">
                <h2 class="text-xl font-mono text-text-primary tracking-widest drop-shadow font-medium">
                    uv index
                </h2>
                <span class="text-xs font-mono text-text-primary/60">Max at {uvData.max_uv_time}</span>
            </div>
            <span
                class="text-4xl md:text-6xl font-mono {uvData.max_uv_index > 7
                    ? 'text-danger'
                    : uvData.max_uv_index > 5
                        ? 'text-warning'
                        : 'text-success'}"
            >
                {uvData.max_uv_index.toFixed(1)}
            </span>
        </div>
    {:else}
        <div class="text-text-primary/60 text-sm font-mono mt-auto">
            --
        </div>
    {/if}
</DashboardCard>
