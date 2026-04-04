<script lang="ts">
	import InterpretOverview from './InterpretOverview.svelte';
	import InterpretStructure from './InterpretStructure.svelte';
	import InterpretShock from './InterpretShock.svelte';
	import InterpretObserver from './InterpretObserver.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<InterpretOverview />
{:else if subtab === '01-structure'}
	<InterpretStructure />
{:else if subtab === '02-shock'}
	<InterpretShock />
{:else if subtab === '03-observer'}
	<InterpretObserver />
{/if}
