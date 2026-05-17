<script>
  import "../app.css";
  import SideBar from "../components/SideBar.svelte";
  import 'geist-svelte/font/sans';
  import 'geist-svelte/font/mono';
  let { children } = $props();
</script>

<main class="h-screen w-screen flex flex-col bg-ground">
    <div class="h-fit">
        <SideBar />
    </div>
    <div class="flex-1 overflow-hidden min-h-0 bg-base">
        {@render children()}
    </div>
</main>
