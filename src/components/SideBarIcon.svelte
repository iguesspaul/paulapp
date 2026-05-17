<script>
    import { page } from "$app/state";
    let { source, href } = $props();

    let isActive = $derived(
        href === "/"
            ? page.url.pathname === href
            : page.url.pathname.startsWith(href),
    );
</script>

<a class="text-text-primary" {href}>
    <img
        src={source}
        alt={href}
        class={[
            "w-6 h-6 invert hover:scale-110 transition",
            {
                "opacity-100": isActive,
                "opacity-40 hover:opacity-100": !isActive,
            },
        ]}
    />
</a>
