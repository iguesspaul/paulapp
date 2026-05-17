<script lang="ts">
    import { onMount } from "svelte";
    import {
        loadTodos,
        addTodo,
        removeTodo,
        updateStatus,
        type Todo,
    } from "../../lib/todos/api";

    let todos = $state<Todo[]>([]);
    let todoName = $state("");
    let selectedUrgency = $state<1 | 2 | 3>(2);
    let selectedStatus = $state<1 | 2 | 3>(1);
    let loading = $state(true);

    const statusLabels: Record<1 | 2 | 3, string> = {
        1: "Not Started",
        2: "In Progress",
        3: "Completed",
    };

    const statusColors: Record<1 | 2 | 3, string> = {
        1: "border-b border-border",
        2: "border-b border-cobalt",
        3: "border-b border-success",
    };

    const urgencyLabels: Record<1 | 2 | 3, string> = {
        1: "Low",
        2: "Medium",
        3: "High",
    };

    const urgencyColors: Record<1 | 2 | 3, string> = {
        1: "border-b border-border",
        2: "border-b border-warning",
        3: "border-b border-danger",
    };

    async function handleAddTodo() {
        if (todoName.trim()) {
            try {
                const response = await addTodo(
                    todoName,
                    selectedUrgency,
                    selectedStatus,
                );
                todos = response.todos;
                todoName = "";
                selectedUrgency = 2;
                selectedStatus = 1;
            } catch (error) {
                console.error("Error adding todo:", error);
            }
        }
    }

    async function handleRemoveTodo(id: string) {
        try {
            const response = await removeTodo(id);
            todos = response.todos;
        } catch (error) {
            console.error("Error removing todo:", error);
        }
    }

    async function handleUpdateStatus(id: string, newStatus: 1 | 2 | 3) {
        try {
            const response = await updateStatus(id, newStatus);
            todos = response.todos;
        } catch (error) {
            console.error("Error updating status:", error);
        }
    }

    onMount(async () => {
        try {
            const response = await loadTodos();
            todos = response.todos;
        } catch (error) {
            console.error("Error loading todos:", error);
        } finally {
            loading = false;
        }
    });
</script>

<div class="w-full h-full grid grid-cols-2 gap-4 bg-ground overflow-hidden">
    <!-- Todo Adder -->
    <div
        class="border border-border m-4 bg-surface p-6 flex flex-col gap-6 min-h-0 overflow-auto"
    >
        <div
            class="text-lg font-mono font-medium text-text-primary border-b border-border pb-4"
        >
            todo adder
        </div>

        <div class="flex flex-col gap-3">
            <p class="text-sm font-mono text-text-secondary">name</p>
            <input
                type="text"
                bind:value={todoName}
                placeholder="Enter todo..."
                class="bg-base border border-border text-text-primary placeholder-text-tertiary px-3 py-2 font-mono focus:outline-none focus:border-cobalt"
                onkeydown={(e) => e.key === "Enter" && handleAddTodo()}
            />
        </div>

        <div class="flex flex-col gap-3">
            <p class="text-sm font-mono text-text-secondary">urgency</p>
            <div class="flex gap-2">
                {#each [1, 2, 3] as level (level)}
                    {@const typedLevel = level as 1 | 2 | 3}
                    {@const colorClasses: Record<1 | 2 | 3, { selected: string; unselected: string }> = {
                        1: {
                            selected: 'border-success bg-success/20',
                            unselected: 'border-border bg-surface',
                        },
                        2: {
                            selected: 'border-warning bg-warning/20',
                            unselected: 'border-border bg-surface',
                        },
                        3: {
                            selected: 'border-danger bg-danger/20',
                            unselected: 'border-border bg-surface',
                        },
                    }}
                    {@const colors = colorClasses[typedLevel]}
                    <button
                        onclick={() => (selectedUrgency = typedLevel)}
                        class={[
                            "w-8 h-8 border transition-colors",
                            selectedUrgency === typedLevel
                                ? colors.selected
                                : colors.unselected,
                        ]}
                        title={`Urgency: ${urgencyLabels[typedLevel]}`}
                    ></button>
                {/each}
            </div>
            <p class="text-sm font-mono text-text-secondary">status</p>
            <div class="flex gap-2">
                {#each [1, 2, 3] as level (level)}
                    {@const typedLevel = level as 1 | 2 | 3}
                    {@const colorClasses: Record<1 | 2 | 3, { selected: string; unselected: string }> = {
                        1: {
                            selected: 'border-success bg-success/20',
                            unselected: 'border-border bg-surface',
                        },
                        2: {
                            selected: 'border-warning bg-warning/20',
                            unselected: 'border-border bg-surface',
                        },
                        3: {
                            selected: 'border-danger bg-danger/20',
                            unselected: 'border-border bg-surface',
                        },
                    }}
                    {@const colors = colorClasses[typedLevel]}
                    <button
                        onclick={() => (selectedStatus = typedLevel)}
                        class={[
                            "px-3 py-1 font-mono text-sm transition-colors border",
                            selectedStatus === typedLevel
                                ? ["text-text-primary", colors.selected]
                                : ["text-text-secondary", colors.unselected],
                        ]}
                        title={`Status: ${statusLabels[typedLevel]}`}
                        >{statusLabels[typedLevel]}</button
                    >
                {/each}
            </div>
        </div>

        <button
            onclick={handleAddTodo}
            disabled={!todoName.trim()}
            class="mt-auto bg-amber border border-amber-bright text-text-inverse px-4 py-2 font-mono transition-colors hover:bg-amber-bright disabled:opacity-50 disabled:cursor-not-allowed"
        >
            add todo
        </button>
    </div>

    <!-- Todos List -->
    <div
        class="border border-border m-4 bg-surface p-6 flex flex-col gap-4 min-h-0 overflow-auto"
    >
        <div
            class="text-lg font-mono font-medium border-b text-text-primary border-border pb-4"
        >
            todos
        </div>

        <div class="flex flex-col gap-3 flex-1 overflow-y-auto p-2 -m-2">
            {#if todos.length === 0}
                <div class="font-mono text-text-tertiary">no todos yet</div>
            {:else}
                {#each todos as todo (todo.id)}
                    <div
                        class="bg-base border border-border p-3 flex justify-between items-start gap-3 transition-transform duration-200 hover:-translate-y-1 hover:scale-[1.02]"
                    >
                        <div class="flex-1 min-w-0">
                            <div class="font-mono truncate text-text-primary">
                                {todo.name}
                            </div>
                            <div class="flex flex-col gap-1.5">
                                <div
                                    class={[
                                        "text-xs font-mono pt-1 text-text-secondary",
                                        urgencyColors[todo.urgency],
                                    ]}
                                >
                                    {urgencyLabels[todo.urgency]}
                                </div>
                                <div
                                    class="text-xs font-mono text-text-primary pt-1"
                                >
                                    <button
                                        class={[
                                            "font-mono text-sm",
                                            todo.status !== 1 &&
                                                "text-text-secondary hover:text-text-primary/75",
                                        ]}
                                        disabled={todo.status === 1}
                                        onclick={() =>
                                            handleUpdateStatus(todo.id, 1)}
                                    >
                                        {statusLabels[1]}
                                    </button>
                                    <button
                                        class={[
                                            "font-mono text-sm mx-2",
                                            todo.status !== 2 &&
                                                "text-text-secondary hover:text-text-primary/75",
                                        ]}
                                        disabled={todo.status === 2}
                                        onclick={() =>
                                            handleUpdateStatus(todo.id, 2)}
                                    >
                                        {statusLabels[2]}
                                    </button>
                                    <button
                                        class={[
                                            "font-mono text-sm",
                                            todo.status !== 3 &&
                                                "text-text-secondary hover:text-text-primary/75",
                                        ]}
                                        disabled={todo.status === 3}
                                        onclick={() =>
                                            handleRemoveTodo(todo.id)}
                                    >
                                        {statusLabels[3]}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                {/each}
            {/if}
        </div>
    </div>
</div>
