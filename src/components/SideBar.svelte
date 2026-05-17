<script>
    import soccerball from "iconoir/icons/soccer-ball.svg";
    import clipboardCheck from "iconoir/icons/clipboard-check.svg";
    import calendar from "iconoir/icons/calendar.svg";
    import home from "iconoir/icons/home-simple.svg";
    import bell from "iconoir/icons/bell-notification.svg";
    import SideBarIcon from "./SideBarIcon.svelte";
</script>

<div
    class="bg-surface border-b border-border p-4 flex flex-row gap-4 items-center"
>
    <SideBarIcon source={home} href="/" />
    <SideBarIcon source={soccerball} href="/sports" />
    <SideBarIcon source={clipboardCheck} href="/todos" />
    <SideBarIcon source={calendar} href="/habits" />
    <SideBarIcon source={bell} href="/countdowns" />
</div>
