<script lang="ts">
    import DashboardCard from "../DashboardCard.svelte";
    import { loadTodos, type Todo } from "../../lib/todos/api";
    import { onMount } from "svelte";

    let todos: Todo[] = [];
    let isLoading = true;

    onMount(async () => {
        try {
            const response = await loadTodos();
            todos = response.todos;
        } catch (error) {
            console.error("Error loading todos:", error);
        } finally {
            isLoading = false;
        }
    });
</script>

<DashboardCard href="/todos" title="todos">
    <div class="text-text-primary/80 font-mono text-sm leading-relaxed whitespace-pre-wrap">
        {#if isLoading}
            Loading...
        {:else if todos.length > 0}
            {#each todos as todo}
                <p>{todo.name}</p>
            {/each}
        {:else}
            No todos found.
        {/if}
    </div>
</DashboardCard>
