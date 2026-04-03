<script lang="ts">
	import Placeholder from './Placeholder.svelte';
	import OrderingDeltaGreedy from './OrderingDeltaGreedy.svelte';
	import OrderingPairwise from './OrderingPairwise.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="ordering" icon="▦" title="Ordering Comparison Table" subtitle="Method | Raw positions | Polished | Raw MSE | Polished MSE" colspan={2} />
		<Placeholder phase="ordering" icon="▲" title="Raw vs Polished Positions" subtitle="Grouped bar chart: raw vs 97/97 polished" delay={0.05} />
		<Placeholder phase="ordering" icon="▬" title="Stiffness by Block Position" subtitle="Frobenius norm through GT ordering" delay={0.1} />
	</div>
{:else if subtab === '01-delta-greedy'}
	<div class="fade-in-up">
		<OrderingDeltaGreedy />
	</div>
{:else if subtab === '02-pairwise'}
	<div class="fade-in-up">
		<OrderingPairwise />
	</div>
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="ordering" icon="▲" title="Ordering Quality" subtitle="Raw positions, MSE, convergence" />
		<Placeholder phase="ordering" icon="▬" title="Position Comparison" subtitle="Found ordering vs GT ordering" delay={0.05} />
		<Placeholder phase="ordering" icon="▶" title="Script Output" subtitle="Raw terminal output for {subtab}" colspan={2} delay={0.1} />
	</div>
{/if}
