<script lang="ts">
	import Placeholder from './Placeholder.svelte';
	import PairingOverview from './PairingOverview.svelte';
	import PairingWeightCorr from './PairingWeightCorr.svelte';
	import PairingOperatorMoments from './PairingOperatorMoments.svelte';
	import PairingSvdAlignment from './PairingSvdAlignment.svelte';
	import PairingAffineLinear from './PairingAffineLinear.svelte';
	import PairingMultiview from './PairingMultiview.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<div class="fade-in-up">
		<PairingOverview />
	</div>
{:else if subtab === '01-weight-corr'}
	<div class="fade-in-up">
		<PairingWeightCorr />
	</div>
{:else if subtab === '02-operator-moments'}
	<div class="fade-in-up">
		<PairingOperatorMoments />
	</div>
{:else if subtab === '03-svd-alignment'}
	<div class="fade-in-up">
		<PairingSvdAlignment />
	</div>
{:else if subtab === '04-affine-linear'}
	<div class="fade-in-up">
		<PairingAffineLinear />
	</div>
{:else if subtab === '05-multiview'}
	<div class="fade-in-up">
		<PairingMultiview />
	</div>
{:else}
	<div class="grid grid-cols-2 gap-4">
		<Placeholder phase="pairing" icon="■" title="Cost Matrix (48×48)" subtitle="Script output for {subtab}" colspan={2} />
		<Placeholder phase="pairing" icon="▲" title="Separation Stats" subtitle="Correct vs incorrect pair scores" delay={0.05} />
		<Placeholder phase="pairing" icon="▶" title="Script Output" subtitle="Raw terminal output" delay={0.1} />
	</div>
{/if}
