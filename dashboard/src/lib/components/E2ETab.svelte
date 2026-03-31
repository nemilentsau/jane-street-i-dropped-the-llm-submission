<script lang="ts">
	import Placeholder from './Placeholder.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="e2e" icon="★" title="Fastest Path" subtitle="Weight correlation + delta greedy + polish" colspan={2} />
		<Placeholder phase="e2e" icon="■" title="Pairing × Ordering Grid" subtitle="Which combos reach perfect MSE" delay={0.05} />
		<Placeholder phase="e2e" icon="▲" title="Timing Breakdown" subtitle="Time per stage across methods" delay={0.1} />
	</div>
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="e2e" icon="▶" title="Script Output" subtitle="Full results for {subtab}" colspan={2} />
		<Placeholder phase="e2e" icon="▲" title="Results Summary" subtitle="Key metrics from this run" delay={0.05} />
	</div>
{/if}
