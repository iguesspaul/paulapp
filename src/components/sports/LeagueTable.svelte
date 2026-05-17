<script lang="ts">
    let props = $props();

    function formatDate(timestamp: number): string {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString('en-US', { 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
</script>

<div class="flex-col flex h-full overflow-x-auto">
    {#if props.standings}
        <div class="flex flex-row gap-3 font-mono text-text-secondary border-b-2 border-border px-2 py-1 items-center text-sm font-bold min-w-min">
            <span class="w-8">#</span>
            <span class="w-40">Team</span>
            <span class="w-12">M</span>
            <span class="w-12">W</span>
            <span class="w-12">D</span>
            <span class="w-12">L</span>
            <span class="w-12">F</span>
            <span class="w-12">A</span>
            <span class="w-12">Pts</span>
        </div>
        {#each props.standings.standings as team}
            <div class="flex flex-row gap-3 font-mono text-text-primary border-b-2 border-border px-2 py-1 items-center text-sm min-w-min">
                <span class="w-8">{team.position}</span>
                <span class="w-40">{team.team_name}</span>
                <span class="w-12">{team.played}</span>
                <span class="w-12">{team.won}</span>
                <span class="w-12">{team.drawn}</span>
                <span class="w-12">{team.lost}</span>
                <span class="w-12">{team.goals_for}</span>
                <span class="w-12">{team.goals_against}</span>
                <span class="w-12 font-bold text-text-primary">{team.points}</span>
            </div>
        {/each}
    {:else}
        <div class="text-text-secondary">Loading...</div>
    {/if}
    
    {#if props.matches && props.matches.matches && props.matches.matches.length > 0}
        <div class="mt-8 pt-4">
            <div class="font-mono text-text-secondary font-bold px-2 py-2 text-sm">Upcoming Matches</div>
            {#each props.matches.matches as match}
                <div class="flex flex-col gap-1 font-mono text-text-primary border-b-2 border-border px-2 py-2 text-sm min-w-min">
                    <div class="flex flex-row gap-2 items-center justify-between">
                        <span class="text-text-secondary text-xs">Round {match.round}</span>
                        <span class="text-text-secondary text-xs">{formatDate(match.start_timestamp)}</span>
                    </div>
                    <div class="flex flex-row gap-4 items-center">
                        <span class="flex-1 text-right">{match.home_team_name}</span>
                        <span class="text-text-secondary">vs</span>
                        <span class="flex-1">{match.away_team_name}</span>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>