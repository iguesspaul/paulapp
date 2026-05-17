<script lang="ts">
    import DateWidget from "../components/widgets/DateWidget.svelte";
    import TodosWidget from "../components/widgets/TodosWidget.svelte";
    import UVWidget from "../components/widgets/UVWidget.svelte";
    import SleepWidget from "../components/widgets/SleepWidget.svelte";
    import NewsWidget from "../components/widgets/NewsWidget.svelte";
    import CountdownsWidget from "../components/widgets/CountdownsWidget.svelte";
</script>

<div class="h-full w-full grid grid-cols-3 grid-rows-2 p-4 overflow-hidden gap-4">
    <!-- Left Column -->
    <div class="col-span-1 row-span-2 flex flex-col gap-4 h-full min-h-0">
        <DateWidget />
        <TodosWidget />
        <UVWidget />
        <SleepWidget />
    </div>

    <!-- Right Column -->
    <div class="col-span-2 row-span-2 flex flex-col gap-4 h-full min-h-0">
        <NewsWidget />
        <CountdownsWidget />
    </div>
</div>
