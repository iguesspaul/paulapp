<script lang="ts">
    import { getStandings, type StandingsResponse, getUpcomingMatches, type UpcomingMatchesResponse } from "../../lib/sports/api";
    import { onMount } from "svelte";
    import LeagueTable from "../../components/sports/LeagueTable.svelte";

    let leaguedata = $state<StandingsResponse | null>(null);
    let matchesData = $state<UpcomingMatchesResponse | null>(null);
    let loading = $state(true);
    let displayedLeagueId = $state("17"); // Default to Premier League
    let testLeagueId = $state("");

    $inspect(leaguedata);

    async function fetchLeagueData(leagueId: string) {
        loading = true;
        leaguedata = null;
        matchesData = null;
        
        try {
            leaguedata = await getStandings(leagueId);
            matchesData = await getUpcomingMatches(leagueId);
        } catch (error) {
            console.error("Error fetching league data:", error);
        }
        loading = false;
    }

    onMount(async () => {
        await fetchLeagueData("17"); // EPL
    });
</script>

<div class="w-full h-full grid grid-cols-4 gap-4 bg-ground overflow-hidden">
    <div
        class="col-span-2 border border-border m-4 bg-surface p-4 flex flex-col min-h-0 overflow-auto"
    >
        <div class="border-b-2 border-border h-fit flex flex-row gap-4">
            <button
                class={['font-mono transition-colors', {
                    'text-text-primary': displayedLeagueId === '17',
                    'text-text-secondary': displayedLeagueId !== '17',
                    'hover:text-text-primary': displayedLeagueId !== '17'
                }]}
                onclick={() => {
                    displayedLeagueId = "17";
                    fetchLeagueData(displayedLeagueId);
                }}>Prem</button
            >
            <button
                class={['font-mono transition-colors', {
                    'text-text-primary': displayedLeagueId === '37',
                    'text-text-secondary': displayedLeagueId !== '37',
                    'hover:text-text-primary': displayedLeagueId !== '37'
                }]}
                onclick={() => {
                    displayedLeagueId = "37";
                    fetchLeagueData(displayedLeagueId);
                }}>Eredivise</button
            >
            <button
                class={['font-mono transition-colors', {
                    'text-text-primary': displayedLeagueId === '23',
                    'text-text-secondary': displayedLeagueId !== '23',
                    'hover:text-text-primary': displayedLeagueId !== '23'
                }]}
                onclick={() => {
                    displayedLeagueId = "23";
                    fetchLeagueData(displayedLeagueId);
                }}>Serie A</button
            >
            <button
                class={['font-mono transition-colors', {
                    'text-text-primary': displayedLeagueId === '8',
                    'text-text-secondary': displayedLeagueId !== '8',
                    'hover:text-text-primary': displayedLeagueId !== '8'
                }]}
                onclick={() => {
                    displayedLeagueId = "8";
                    fetchLeagueData(displayedLeagueId);
                }}>LaLiga</button
            >
        </div>
        <div class="flex-1 min-h-0 overflow-auto">
            <LeagueTable standings={leaguedata} matches={matchesData} />
        </div>
    </div>
    <div class="col-span-1 border border-border m-4 overflow-auto flex flex-col gap-2">
        Column 2 (25%)
    </div>
    <div class="col-span-1 border border-border m-4 overflow-auto">
        Column 3 (25%)
    </div>
</div>
