<script lang="ts">
	import Placeholder from './Placeholder.svelte';

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
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="interpretability" icon="◆" title="Jacobian Traces" subtitle="Per-block trace values, all negative" />
		<Placeholder phase="interpretability" icon="▦" title="Phase Delta Chart" subtitle="Early (blue) / Mid (green) / Late (red)" delay={0.05} />
		<Placeholder phase="interpretability" icon="▬" title="Cumulative Operator SVs" subtitle="Scree plot: factor compression" delay={0.1} />
		<Placeholder phase="interpretability" icon="●" title="Trajectory PCA" subtitle="Mean state projected onto top PCs" delay={0.15} />
	</div>
{:else if subtab === '02-shock'}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="interpretability" icon="▲" title="Shock Response Curves" subtitle="Top-PC (amplified) vs bottom-PC (damped) through depth" colspan={2} />
		<Placeholder phase="interpretability" icon="◆" title="Damping Ratios" subtitle="Per-direction damping summary" delay={0.05} />
		<Placeholder phase="interpretability" icon="▦" title="Regime Stability" subtitle="Gap persists across data subsets" delay={0.1} />
	</div>
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="interpretability" icon="▶" title="Script Output" subtitle="Results for {subtab}" colspan={2} />
		<Placeholder phase="interpretability" icon="▲" title="Model Comparison" subtitle="Autonomous vs observer surrogate" delay={0.05} />
	</div>
{/if}
