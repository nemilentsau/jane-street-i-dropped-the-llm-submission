<script lang="ts">
	import Placeholder from './Placeholder.svelte';
	import OrderingOverview from './OrderingOverview.svelte';
	import OrderingDeltaGreedy from './OrderingDeltaGreedy.svelte';
	import OrderingPairwise from './OrderingPairwise.svelte';
	import OrderingSinkhorn from './OrderingSinkhorn.svelte';
	import OrderingBeamSearch from './OrderingBeamSearch.svelte';
	import OrderingSpectralFlow from './OrderingSpectralFlow.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<div class="fade-in-up">
		<OrderingOverview />
	</div>
{:else if subtab === '01-delta-greedy'}
	<div class="fade-in-up">
		<OrderingDeltaGreedy />
	</div>
{:else if subtab === '02-pairwise'}
	<div class="fade-in-up">
		<OrderingPairwise />
	</div>
{:else if subtab === '03-sinkhorn'}
	<div class="fade-in-up">
		<OrderingSinkhorn />
	</div>
{:else if subtab === '04-beam-search'}
	<div class="fade-in-up">
		<OrderingBeamSearch />
	</div>
{:else if subtab === '05-spectral-flow'}
	<div class="fade-in-up">
		<OrderingSpectralFlow />
	</div>
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="ordering" icon="▲" title="Ordering Quality" subtitle="Raw positions, MSE, convergence" />
		<Placeholder phase="ordering" icon="▬" title="Position Comparison" subtitle="Found ordering vs GT ordering" delay={0.05} />
		<Placeholder phase="ordering" icon="▶" title="Script Output" subtitle="Raw terminal output for {subtab}" colspan={2} delay={0.1} />
	</div>
{/if}
