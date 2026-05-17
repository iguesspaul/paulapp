<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import { exchangeWhoopToken } from '$lib/whoop/api';

  let status = "Authenticating with WHOOP...";

  onMount(async () => {
    const code = $page.url.searchParams.get('code');
    if (code) {
      try {
        await exchangeWhoopToken(code);
        status = "Success! Redirecting back to dashboard...";
        setTimeout(() => {
          goto('/');
        }, 1000);
      } catch (err) {
        status = `Failed to exchange token: ${err}`;
      }
    } else {
      status = "Error: No code provided in URL.";
    }
  });
</script>

<div class="h-full w-full flex items-center justify-center p-8 text-center text-text-primary font-mono text-xl">
  {status}
</div>
