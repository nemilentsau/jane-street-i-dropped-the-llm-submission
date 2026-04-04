<script lang="ts">
	import Placeholder from './Placeholder.svelte';
	import InterpretStructure from './InterpretStructure.svelte';
	import InterpretShock from './InterpretShock.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="interpretability" icon="◆" title="Jacobian Analysis" subtitle="All contractive, mean-reverting" />
		<Placeholder phase="interpretability" icon="▦" title="Phase Structure" subtitle="Early stabilize, mid compress, late correct" delay={0.05} />
		<Placeholder phase="interpretability" icon="▲" title="Shock Response" subtitle="22x prediction gap: top vs bottom PCs" delay={0.1} />
		<Placeholder phase="interpretability" icon="▬" title="Trajectory PCA" subtitle="48-step trajectory is effectively 3-dimensional" colspan={2} delay={0.15} />
	</div>
{:else if subtab === '01-structure'}
	<InterpretStructure />
{:else if subtab === '02-shock'}
	<InterpretShock />
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="interpretability" icon="▶" title="Script Output" subtitle="Results for {subtab}" colspan={2} />
		<Placeholder phase="interpretability" icon="▲" title="Model Comparison" subtitle="Autonomous vs observer surrogate" delay={0.05} />
	</div>
{/if}
