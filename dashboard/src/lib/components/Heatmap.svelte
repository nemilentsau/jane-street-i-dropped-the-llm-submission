<script lang="ts">
	let {
		data,
		title = '',
		width = 400,
		height = 400,
		xlabel = '',
		ylabel = '',
	}: {
		data: number[][];
		title?: string;
		width?: number;
		height?: number;
		xlabel?: string;
		ylabel?: string;
	} = $props();

	const pad = { top: 8, right: 8, bottom: 28, left: 28 };
	let rows = $derived(data.length);
	let cols = $derived(data[0]?.length ?? 0);
	let pw = $derived(width - pad.left - pad.right);
	let ph = $derived(height - pad.top - pad.bottom);
	let cellW = $derived(pw / cols);
	let cellH = $derived(ph / rows);

	let range = $derived.by(() => {
		let vmin = Infinity, vmax = -Infinity;
		for (const row of data) {
			for (const v of row) {
				if (v < vmin) vmin = v;
				if (v > vmax) vmax = v;
			}
		}
		return { vmin, vmax };
	});

	function color(val: number): string {
		const t = range.vmax > range.vmin ? (val - range.vmin) / (range.vmax - range.vmin) : 0.5;
		if (t < 0.33) {
			const s = t / 0.33;
			return `rgb(${lerp(13, 26, s)}, ${lerp(17, 82, s)}, ${lerp(23, 118, s)})`;
		} else if (t < 0.66) {
			const s = (t - 0.33) / 0.33;
			return `rgb(${lerp(26, 45, s)}, ${lerp(82, 212, s)}, ${lerp(118, 191, s)})`;
		} else {
			const s = (t - 0.66) / 0.34;
			return `rgb(${lerp(45, 251, s)}, ${lerp(212, 191, s)}, ${lerp(191, 36, s)})`;
		}
	}

	function lerp(a: number, b: number, t: number): number {
		return Math.round(a + (b - a) * t);
	}
</script>

<div class="inline-block">
	{#if title}<h4 class="mb-1 text-xs font-semibold text-text-secondary">{title}</h4>{/if}
	<svg {width} {height}>
		{#each data as row, i}
			{#each row as val, j}
				<rect
					x={pad.left + j * cellW}
					y={pad.top + i * cellH}
					width={cellW}
					height={cellH}
					fill={color(val)}
					stroke="none"
				>
					<title>({i},{j}): {val.toFixed(3)}</title>
				</rect>
			{/each}
		{/each}
		{#if xlabel}
			<text x={pad.left + pw / 2} y={height - 4} text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10">{xlabel}</text>
		{/if}
		{#if ylabel}
			<text x={10} y={pad.top + ph / 2} text-anchor="middle" fill="var(--color-text-tertiary)" font-size="10" transform="rotate(-90,10,{pad.top + ph / 2})">{ylabel}</text>
		{/if}
	</svg>
</div>
