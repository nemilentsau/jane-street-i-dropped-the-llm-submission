<script lang="ts">
	let {
		margins,
		title = '',
		width = 480,
		height = 200,
	}: {
		margins: number[];
		title?: string;
		width?: number;
		height?: number;
	} = $props();

	const pad = { top: 16, right: 12, bottom: 28, left: 44 };
	let pw = $derived(width - pad.left - pad.right);
	let ph = $derived(height - pad.top - pad.bottom);
	let n = $derived(margins.length);
	let yMax = $derived(Math.max(...margins) * 1.1);
	let yMin = $derived(Math.min(0, Math.min(...margins) * 1.1));
	let yRange = $derived(yMax - yMin || 1);
	let zeroY = $derived(pad.top + ph - ((0 - yMin) / yRange) * ph);
	let minMargin = $derived(Math.min(...margins));
	let minMarginY = $derived(pad.top + ph - ((minMargin - yMin) / yRange) * ph);

	function barX(i: number): number { return pad.left + (i / n) * pw; }
	function barW(): number { return Math.max(pw / n - 1, 1); }
</script>

<div class="inline-block">
	{#if title}<h4 class="mb-1 text-xs font-semibold text-text-secondary">{title}</h4>{/if}
	<svg {width} {height}>
		<line x1={pad.left} x2={pad.left + pw} y1={zeroY} y2={zeroY} stroke="var(--color-border-accent)" stroke-dasharray="4,3" />
		<line x1={pad.left} x2={pad.left} y1={pad.top} y2={pad.top + ph} stroke="var(--color-border-medium)" />

		{#each margins as m, i}
			{@const barTop = pad.top + ph - ((Math.max(m, 0) - yMin) / yRange) * ph}
			{@const barBot = pad.top + ph - ((Math.min(m, 0) - yMin) / yRange) * ph}
			<rect
				x={barX(i)}
				y={barTop}
				width={barW()}
				height={barBot - barTop}
				fill={m >= 0 ? 'var(--color-accent-green)' : 'var(--color-accent-red)'}
				opacity="0.7"
				rx="1"
			>
				<title>pair {i}: margin={m.toFixed(3)}</title>
			</rect>
		{/each}

		<line x1={pad.left} x2={pad.left + pw} y1={minMarginY} y2={minMarginY} stroke="var(--color-accent-amber)" stroke-width="1" stroke-dasharray="2,2" opacity="0.6" />
		<text x={pad.left + pw - 4} y={minMarginY - 4} text-anchor="end" fill="var(--color-accent-amber)" font-size="10" font-family="var(--font-mono)">min = {minMargin.toFixed(2)}</text>

		<text x={pad.left + pw / 2} y={height - 4} text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">Pairs (sorted by margin)</text>
	</svg>
</div>
