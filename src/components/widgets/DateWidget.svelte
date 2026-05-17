<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { getYearProgress } from "../../lib/utils/date";

    const { dayOfYear, percentage, bar } = getYearProgress();
    const currentDateStr = new Date().toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
    });
</script>

<DashboardCard class="gap-2 justify-end">
    <div class="flex-row justify-between">
        <p class="text-md font-mono text-text-primary/60">
            Day {dayOfYear}/365
        </p>
    </div>
    <p class="text-md font-mono text-text-primary/60">
        [{bar}] {percentage}%
    </p>
    <p class="text-xl font-mono text-text-primary font-medium">
        {currentDateStr}
    </p>
</DashboardCard>
