<script lang="ts">
	import '../app.css';
	let { children } = $props();
</script>

<svelte:head>
	<title>I Dropped the LLM — Evidence Dashboard</title>
</svelte:head>

{@render children()}
