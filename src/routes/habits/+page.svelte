<script lang="ts">
    import { onMount } from "svelte";
    import {
        loadHabits,
        addHabit,
        removeHabit,
        toggleHabitEntry,
        createHabitBackup,
        getMonthlySummary,
        getHabitHistory,
        type Habit,
        type HabitEntry,
        type MonthlySummary,
        type HabitHistoryResponse,
    } from "../../lib/habits/api";

    let habits = $state<Habit[]>([]);
    let entries = $state<HabitEntry[]>([]);
    let newHabitName = $state("");
    let loading = $state(true);

    let currentDate = $state(new Date());
    let year = $derived(currentDate.getFullYear());
    let month = $derived(currentDate.getMonth()); // 0-11
    let daysInMonth = $derived(getDaysInMonth(currentDate));
    let days = $derived(Array.from({ length: daysInMonth }, (_, i) => i + 1));

    let summary = $state<MonthlySummary | null>(null);
    let selectedHabitHistory = $state<HabitHistoryResponse | null>(null);
    let showingHistoryModal = $state(false);

    const dayLetters = ["M", "T", "W", "Th", "F", "Sa", "Sn"];

    function getDaysInMonth(date: Date): number {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    }

    function getDayLetter(date: Date): string {
        const day = date.getDay();
        return dayLetters[(day + 6) % 7];
    }

    function formatDate(year: number, month: number, day: number): string {
        return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    }

    function isEntryCompleted(habit_id: string, date: string): boolean {
        return entries.some(
            (e) => e.habit_id === habit_id && e.date === date && e.completed,
        );
    }

    async function loadSummary(y: number, m: number) {
        try {
            await createHabitBackup(y, m);
            summary = await getMonthlySummary(y, m);
        } catch (e) {
            console.error("Failed to load summary", e);
        }
    }

    $effect(() => {
        // Run whenever year or month changes
        loadSummary(year, month + 1);
    });

    async function handleToggle(habit_id: string, date: string) {
        try {
            const response = await toggleHabitEntry(habit_id, date);
            entries = response.entries;
            await loadSummary(year, month + 1);
        } catch (error) {
            console.error("Error toggling entry:", error);
        }
    }

    async function handleAddHabit() {
        if (newHabitName.trim()) {
            try {
                const response = await addHabit(newHabitName);
                habits = response.habits;
                entries = response.entries;
                newHabitName = "";
                await loadSummary(year, month + 1);
            } catch (error) {
                console.error("Error adding habit:", error);
            }
        }
    }

    async function handleRemoveHabit(habit_id: string) {
        try {
            const response = await removeHabit(habit_id);
            habits = response.habits;
            entries = response.entries;
            await loadSummary(year, month + 1);
        } catch (error) {
            console.error("Error removing habit:", error);
        }
    }

    async function showHistory(habitId: string) {
        try {
            selectedHabitHistory = await getHabitHistory(habitId);
            showingHistoryModal = true;
        } catch (error) {
            console.error("Failed to load habit history:", error);
        }
    }

    function closeHistory() {
        showingHistoryModal = false;
        selectedHabitHistory = null;
    }

    function prevMonth() {
        currentDate = new Date(year, month - 1, 1);
    }

    function nextMonth() {
        currentDate = new Date(year, month + 1, 1);
    }

    onMount(async () => {
        try {
            const response = await loadHabits();
            habits = response.habits;
            entries = response.entries;

            if (habits.length === 0) {
                const h1 = await addHabit("Read books");
                habits = h1.habits;
                entries = h1.entries;

                const h2 = await addHabit("Create code projects");
                habits = h2.habits;
                entries = h2.entries;
            }

            await loadSummary(year, month + 1);
        } catch (error) {
            console.error("Error loading habits:", error);
        } finally {
            loading = false;
        }
    });
</script>

<div class="flex flex-col h-full bg-ground relative">
    <!-- Header -->
    <div
        class="border-b border-border p-4 h-fit flex items-center justify-between"
    >
        <div class="text-lg font-mono font-medium text-text-primary">
            habits
        </div>

        <div class="flex items-center space-x-4">
            <button
                onclick={prevMonth}
                class="text-text-secondary hover:text-text-primary font-mono text-sm px-2 py-1 bg-surface border border-border"
                >&lt; prev</button
            >
            <div class="text-sm font-mono text-text-primary w-24 text-center">
                {currentDate.toLocaleString("default", {
                    month: "short",
                    year: "numeric",
                })}
            </div>
            <button
                onclick={nextMonth}
                class="text-text-secondary hover:text-text-primary font-mono text-sm px-2 py-1 bg-surface border border-border"
                >next &gt;</button
            >
        </div>
    </div>

    <!-- Content Container -->
    <div class="flex-1 flex overflow-hidden bg-surface">
        <!-- Fixed Left Column (Habit Names) -->
        <div
            class="w-32 shrink-0 border-r border-border flex flex-col overflow-y-auto"
        >
            <!-- Header Spacer -->
            <div class="h-8 border-b border-border"></div>

            <!-- Habit Rows -->
            {#each habits as habit}
                <div
                    class="h-16 border-b border-border p-2 flex flex-col justify-center bg-base relative group"
                >
                    <button
                        onclick={() => showHistory(habit.id)}
                        class="text-sm font-mono truncate text-text-primary text-left hover:text-accent-blue transition-colors"
                        title="View history"
                    >
                        {habit.name}
                    </button>
                    <button
                        onclick={() => handleRemoveHabit(habit.id)}
                        class="text-xs font-mono mt-1 hover:text-accent-amber text-text-tertiary text-left w-max"
                    >
                        remove
                    </button>
                </div>
            {/each}

            <!-- Add Habit Row -->
            <div class="h-8 border-t border-border p-2 flex items-center">
                <input
                    type="text"
                    bind:value={newHabitName}
                    placeholder="New..."
                    class="w-full px-1 py-1 bg-base border border-border text-xs font-mono text-text-primary h-6"
                    onkeydown={(e) => e.key === "Enter" && handleAddHabit()}
                />
            </div>
        </div>

        <!-- Scrollable Right Section (Day Grid) -->
        <div class="flex-1 overflow-auto">
            <div class="inline-block min-w-full">
                <!-- Header Row with Days -->
                <div class="flex border-b border-border">
                    {#each days as day}
                        {@const dayDate = new Date(year, month, day)}
                        {@const letter = getDayLetter(dayDate)}
                        <div
                            class="w-8 h-8 flex flex-col items-center justify-center border-r border-border text-xs font-mono shrink-0 text-text-secondary bg-base"
                        >
                            <div class="leading-none">{letter}</div>
                            <div class="text-[10px] leading-none mt-1">
                                {day}
                            </div>
                        </div>
                    {/each}
                    <div
                        class="w-16 h-8 flex items-center justify-center border-r border-border text-xs font-mono shrink-0 text-text-secondary bg-surface"
                    >
                        Score
                    </div>
                    <div
                        class="w-16 h-8 flex items-center justify-center border-r border-border text-xs font-mono shrink-0 text-text-secondary bg-surface"
                    >
                        Rate
                    </div>
                </div>

                <!-- Habit Rows with Entry Cells -->
                {#each habits as habit}
                    {@const habitSummary = summary?.habits.find(
                        (h) => h.habit_name === habit.name,
                    )}
                    <div class="flex border-b border-border h-16">
                        {#each days as day}
                            {@const dateStr = formatDate(year, month, day)}
                            {@const completed = isEntryCompleted(
                                habit.id,
                                dateStr,
                            )}
                            <button
                                onclick={() => handleToggle(habit.id, dateStr)}
                                class="w-8 border-r border-border flex items-center justify-center font-mono text-xs shrink-0 bg-base text-text-primary hover:bg-surface transition-colors"
                            >
                                {#if completed}
                                    <span class="w-2 h-2 bg-text-primary"
                                    ></span>
                                {/if}
                            </button>
                        {/each}
                        <div
                            class="w-16 border-r border-border flex items-center justify-center font-mono text-xs shrink-0 bg-surface text-text-primary"
                        >
                            {habitSummary ? habitSummary.days_completed : "-"}
                        </div>
                        <div
                            class="w-16 border-r border-border flex items-center justify-center font-mono text-xs shrink-0 bg-surface text-text-primary"
                        >
                            {habitSummary
                                ? Math.round(
                                      habitSummary.completion_rate * 100,
                                  ) + "%"
                                : "-"}
                        </div>
                    </div>
                {/each}

                <!-- Add Habit Row (Day Cells) -->
                <div class="flex border-t border-border h-8"></div>
            </div>
        </div>
    </div>

    <!-- History Modal -->
    {#if showingHistoryModal && selectedHabitHistory}
        <div
            class="absolute inset-0 bg-ground/80 backdrop-blur-sm flex items-center justify-center z-50 p-8"
        >
            <div
                class="bg-base border border-border w-full max-w-2xl flex flex-col max-h-full shadow-2xl"
            >
                <!-- Modal Header -->
                <div
                    class="flex items-center justify-between p-4 border-b border-border bg-surface"
                >
                    <h2 class="font-mono text-text-primary text-lg">
                        {selectedHabitHistory.habit_name} - History
                    </h2>
                    <button
                        onclick={closeHistory}
                        class="text-text-secondary hover:text-accent-amber font-mono text-sm px-2 py-1 border border-border bg-base"
                    >
                        close
                    </button>
                </div>

                <!-- Modal Content -->
                <div class="p-6 overflow-y-auto">
                    {#if selectedHabitHistory.snapshots.length === 0}
                        <div
                            class="text-text-secondary font-mono text-sm text-center py-8"
                        >
                            No historical data available.
                        </div>
                    {:else}
                        <div
                            class="grid grid-cols-5 gap-4 mb-4 border-b border-border pb-2 text-text-secondary font-mono text-xs"
                        >
                            <div>Month</div>
                            <div>Year</div>
                            <div>Completed</div>
                            <div>Total Days</div>
                            <div>Rate</div>
                        </div>
                        <div class="flex flex-col space-y-2">
                            {#each selectedHabitHistory.snapshots as snapshot}
                                <div
                                    class="grid grid-cols-5 gap-4 font-mono text-sm text-text-primary items-center border border-border p-2 bg-surface"
                                >
                                    <div>
                                        {new Date(
                                            snapshot.year,
                                            snapshot.month - 1,
                                        ).toLocaleString("default", {
                                            month: "short",
                                        })}
                                    </div>
                                    <div>{snapshot.year}</div>
                                    <div class="text-accent-blue">
                                        {snapshot.days_completed}
                                    </div>
                                    <div>{snapshot.days_in_month}</div>
                                    <div>
                                        <div
                                            class="flex items-center space-x-2 w-full"
                                        >
                                            <span class="w-10"
                                                >{Math.round(
                                                    snapshot.completion_rate *
                                                        100,
                                                )}%</span
                                            >
                                            <div
                                                class="h-1 flex-1 bg-ground border border-border"
                                            >
                                                <div
                                                    class="h-full bg-text-primary"
                                                    style="width: {snapshot.completion_rate *
                                                        100}%"
                                                ></div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
</div>
