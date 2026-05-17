<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import {
        loadCountdowns,
        addCountdown,
        removeCountdown,
        type Countdown,
    } from "../../lib/countdowns/api";

    import arrowLeft from "iconoir/icons/arrow-left.svg";
    import trash from "iconoir/icons/trash.svg";

    let countdowns: Countdown[] = [];

    let newName = "";
    let newDate = "";
    let newTime = "";

    async function handleAdd() {
        if (!newName.trim() || !newDate.trim()) return;

        const dateCombined = newTime
            ? `${newDate}T${newTime}`
            : `${newDate}T00:00:00`;
        const targetDate = new Date(dateCombined);
        const targetTimestamp = Math.floor(targetDate.getTime() / 1000); // Unix timestamp in seconds

        try {
            const response = await addCountdown(
                newName.trim(),
                targetTimestamp,
            );
            countdowns = response.countdowns;
            newName = "";
            newDate = "";
            newTime = "";
        } catch (e) {
            console.error("Failed to add countdown:", e);
        }
    }

    async function handleRemove(id: string) {
        try {
            const response = await removeCountdown(id);
            countdowns = response.countdowns;
        } catch (e) {
            console.error("Failed to remove countdown:", e);
        }
    }

    onMount(async () => {
        try {
            const response = await loadCountdowns();
            countdowns = response.countdowns;
        } catch (e) {
            console.error("Failed to load countdowns:", e);
        }
    });
</script>

<div class="h-full w-full flex flex-col p-8 gap-8 overflow-hidden font-mono">
    <div class="flex flex-row items-center justify-between">
        <h1 class="text-3xl font-mono text-text-primary font-medium">
            countdowns
        </h1>
        <div class="w-12"></div>
    </div>

    <div class="flex-1 flex flex-row gap-8 overflow-hidden">
        <!-- Left side: List of active countdowns -->
        <div class="flex-1 flex flex-col gap-4 overflow-y-auto">
            {#if countdowns.length === 0}
                <div class="bg-surface p-6 text-text-primary/60">
                    No countdowns set. Add an event to begin.
                </div>
            {:else}
                {#each countdowns as countdown}
                    {@const target = new Date(
                        countdown.target_timestamp * 1000,
                    )}
                    {@const now = new Date()}
                    {@const diffTime = target.getTime() - now.getTime()}
                    {@const daysRemaining = Math.max(
                        0,
                        Math.ceil(diffTime / (1000 * 60 * 60 * 24)),
                    )}
                    {@const isToday =
                        target.getDate() === now.getDate() &&
                        target.getMonth() === now.getMonth() &&
                        target.getFullYear() === now.getFullYear()}

                    <div
                        class="bg-surface p-4 flex flex-row items-center justify-between group hover:scale-[1.01] transition relative"
                    >
                        <div class="flex flex-col gap-1">
                            <span class="text-lg text-text-primary truncate"
                                >{countdown.name}</span
                            >
                            <span class="text-sm text-text-primary/40">
                                {target.toLocaleDateString("en-US", {
                                    year: "numeric",
                                    month: "long",
                                    day: "numeric",
                                })}
                            </span>
                        </div>

                        <div class="flex flex-col items-end gap-1 px-4 pr-14">
                            {#if isToday}
                                <span class="text-3xl text-amber font-bold"
                                    >TODAY!</span
                                >
                            {:else}
                                <span
                                    class="text-3xl text-text-primary font-bold"
                                    >{daysRemaining}</span
                                >
                                <span
                                    class="text-xs text-text-primary/60 uppercase"
                                    >Days Left</span
                                >
                            {/if}
                        </div>

                        <button
                            on:click={() => handleRemove(countdown.id)}
                            class="absolute right-4 bg-transparent p-2 opacity-0 group-hover:opacity-100 transition flex items-center justify-center"
                            title="Delete Countdown"
                        >
                            <img
                                src={trash}
                                alt="Delete"
                                class="w-5 h-5 invert opacity-60 hover:opacity-100 hover:scale-110 transition"
                            />
                        </button>
                    </div>
                {/each}
            {/if}
        </div>

        <!-- Right side: Add new form -->
        <div class="w-1/3 flex flex-col gap-4 bg-surface p-6 h-fit shrink-0">
            <h2 class="text-xl text-text-primary tracking-widest mb-4">
                add event
            </h2>

            <div class="flex flex-col gap-2">
                <p class="text-xs text-text-primary/60">event name</p>
                <input
                    type="text"
                    bind:value={newName}
                    placeholder="Graduation..."
                    class="bg-raised border-none text-text-primary p-3 font-mono focus:outline-none"
                />
            </div>

            <div class="flex flex-col gap-2">
                <p class="text-xs text-text-primary/60">target date</p>
                <input
                    type="date"
                    bind:value={newDate}
                    class="bg-raised border-none text-text-primary p-3 font-mono focus:outline-none"
                />
            </div>

            <div class="flex flex-col gap-2">
                <p class="text-xs text-text-primary/60">
                    target time (optional)
                </p>
                <input
                    type="time"
                    bind:value={newTime}
                    class="bg-raised border-none text-text-primary p-3 font-mono focus:outline-none"
                />
            </div>

            <button
                on:click={handleAdd}
                class="mt-4 bg-text-primary text-text-inverse p-3 font-mono text-sm tracking-widest font-bold transition-all duration-300 transform-gpu hover:scale-[1.02] hover:opacity-90 {!newName.trim() ||
                !newDate.trim()
                    ? 'opacity-50 cursor-not-allowed'
                    : 'cursor-pointer'}"
            >
                add countdown
            </button>

            {#if !newName.trim() || !newDate.trim()}
                <div
                    class="mt-2 bg-danger/10 text-danger p-3 font-mono text-xs flex flex-col gap-1"
                >
                    <span
                        >Please provide an event name and target date to
                        continue.</span
                    >
                </div>
            {/if}
        </div>
    </div>
</div>
