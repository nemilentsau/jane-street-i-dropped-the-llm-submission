<script lang="ts">
	let {
		seriesA,
		seriesB,
		labelA = 'A',
		labelB = 'B',
		colorA = 'var(--color-accent-green)',
		colorB = 'var(--color-accent-red)',
		title = '',
		xlabel = '',
		bins = 40,
		width = 480,
		height = 220,
	}: {
		seriesA: number[];
		seriesB: number[];
		labelA?: string;
		labelB?: string;
		colorA?: string;
		colorB?: string;
		title?: string;
		xlabel?: string;
		bins?: number;
		width?: number;
		height?: number;
	} = $props();

	const pad = { top: 20, right: 16, bottom: 36, left: 44 };
	let pw = $derived(width - pad.left - pad.right);
	let ph = $derived(height - pad.top - pad.bottom);

	let histData = $derived.by(() => {
		const all = [...seriesA, ...seriesB];
		const lo = Math.min(...all);
		const hi = Math.max(...all);
		const range = hi - lo || 1;
		const binW = range / bins;

		function binify(values: number[]): number[] {
			const counts = new Array(bins).fill(0);
			for (const v of values) {
				const idx = Math.min(Math.floor((v - lo) / binW), bins - 1);
				counts[idx]++;
			}
			return counts;
		}

		const binsA = binify(seriesA);
		const binsB = binify(seriesB);
		const maxCount = Math.max(...binsA, ...binsB);

		return { binsA, binsB, lo, binW, maxCount };
	});

	function barX(i: number): number { return pad.left + (i / bins) * pw; }
	function barW(): number { return pw / bins; }
	function barH(count: number): number {
		return histData.maxCount > 0 ? (count / histData.maxCount) * ph : 0;
	}
</script>

<div class="inline-block">
	{#if title}<h4 class="mb-1 text-xs font-semibold text-text-secondary">{title}</h4>{/if}
	<svg {width} {height}>
		<line x1={pad.left} x2={pad.left + pw} y1={pad.top + ph} y2={pad.top + ph} stroke="var(--color-border-medium)" />
		<line x1={pad.left} x2={pad.left} y1={pad.top} y2={pad.top + ph} stroke="var(--color-border-medium)" />

		{#each histData.binsB as count, i}
			{#if count > 0}
				<rect x={barX(i)} y={pad.top + ph - barH(count)} width={barW()} height={barH(count)} fill={colorB} opacity="0.5">
					<title>{labelB}: {(histData.lo + i * histData.binW).toFixed(2)}–{(histData.lo + (i + 1) * histData.binW).toFixed(2)}, count={count}</title>
				</rect>
			{/if}
		{/each}

		{#each histData.binsA as count, i}
			{#if count > 0}
				<rect x={barX(i)} y={pad.top + ph - barH(count)} width={barW()} height={barH(count)} fill={colorA} opacity="0.7">
					<title>{labelA}: {(histData.lo + i * histData.binW).toFixed(2)}–{(histData.lo + (i + 1) * histData.binW).toFixed(2)}, count={count}</title>
				</rect>
			{/if}
		{/each}

		<!-- Legend -->
		<rect x={pad.left + pw - 130} y={pad.top + 2} width={10} height={10} fill={colorA} opacity="0.7" rx="1" />
		<text x={pad.left + pw - 116} y={pad.top + 11} fill="var(--color-text-secondary)" font-size="10">{labelA}</text>
		<rect x={pad.left + pw - 130} y={pad.top + 18} width={10} height={10} fill={colorB} opacity="0.5" rx="1" />
		<text x={pad.left + pw - 116} y={pad.top + 27} fill="var(--color-text-secondary)" font-size="10">{labelB}</text>

		{#if xlabel}
			<text x={pad.left + pw / 2} y={height - 4} text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">{xlabel}</text>
		{/if}
	</svg>
</div>
