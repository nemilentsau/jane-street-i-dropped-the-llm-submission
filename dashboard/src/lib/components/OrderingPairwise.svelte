<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart, HeatmapChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, VisualMapComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, LineChart, HeatmapChart, TooltipComponent, GridComponent, MarkLineComponent, VisualMapComponent, CanvasRenderer]);

	type MethodResult = {
		correct_positions: number;
		total_positions: number;
		mse: number;
		pairwise_score?: number;
	};

	type PTData = {
		pairwise_accuracy: number;
		margin_matrix_gt_order: number[][];
		margin_distribution: number[];
		margin_stats: {
			mean_abs: number;
			median_abs: number;
			max_abs: number;
			n_concordant: number;
			n_discordant: number;
			total_pairs: number;
		};
		nontransitive: {
			n_cycles: number;
			n_triples: number;
			cycle_rate: number;
		};
		methods: {
			win_count: MethodResult;
			insertion: MethodResult;
			refined: MethodResult;
			polished: MethodResult;
		};
		polish_trace: { iteration: number; mse: number }[];
		elapsed_s: number;
	};

	let data: PTData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/ordering_02_pairwise_tournament.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	/* ── Heatmap: margin matrix in GT order ─────────────────── */
	let heatmapOptions = $derived.by(() => {
		if (!data) return null;
		const matrix = data.margin_matrix_gt_order;
		const n = matrix.length;
		const heatData: [number, number, number][] = [];
		let maxAbs = 0;
		for (let i = 0; i < n; i++) {
			for (let j = 0; j < n; j++) {
				if (i === j) continue;
				const v = matrix[i][j];
				heatData.push([j, n - 1 - i, v]);
				if (Math.abs(v) > maxAbs) maxAbs = Math.abs(v);
			}
		}
		return {
			tooltip: {
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = params as { value: [number, number, number] };
					const col = p.value[0];
					const row = n - 1 - p.value[1];
					const v = p.value[2];
					const concordant = (row < col && v > 0) || (row > col && v < 0);
					return `<strong style="color:#eceff4">GT pos ${row + 1} vs ${col + 1}</strong>`
						+ `<br/>Margin: <span style="color:${v > 0 ? '#6cb6ff' : '#ee7a7a'}">${v.toFixed(5)}</span>`
						+ `<br/>${concordant ? '<span style="color:#3dd68c">Concordant</span>' : '<span style="color:#f0883e">Discordant</span>'}`;
				},
			},
			grid: { top: 8, right: 16, bottom: 44, left: 52 },
			xAxis: {
				type: 'category' as const,
				data: Array.from({ length: n }, (_, i) => i + 1),
				axisLabel: { color: '#8690a2', fontSize: 9, interval: 7 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { show: false },
				name: 'GT position (column)',
				nameLocation: 'middle' as const,
				nameGap: 28,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: {
				type: 'category' as const,
				data: Array.from({ length: n }, (_, i) => n - i),
				axisLabel: { color: '#8690a2', fontSize: 9, interval: 7 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { show: false },
				name: 'GT position (row)',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			visualMap: {
				min: -maxAbs,
				max: maxAbs,
				calculable: false,
				orient: 'horizontal' as const,
				left: 'center',
				bottom: 0,
				itemWidth: 12,
				itemHeight: 100,
				textStyle: { color: '#8690a2', fontSize: 10 },
				inRange: {
					color: ['#ee7a7a', '#2a1f1f', '#0d1117', '#1a2433', '#6cb6ff'],
				},
			},
			series: [{
				type: 'heatmap' as const,
				data: heatData,
				itemStyle: { borderWidth: 0 },
			}],
			backgroundColor: 'transparent',
		};
	});

	/* ── Histogram: margin distribution ─────────────────────── */
	let histogramOptions = $derived.by(() => {
		if (!data) return null;
		const vals = data.margin_distribution;
		const nBins = 40;
		const maxAbs = data.margin_stats.max_abs;
		const binWidth = (2 * maxAbs) / nBins;
		const bins = Array.from({ length: nBins }, (_, i) => ({
			left: -maxAbs + i * binWidth,
			right: -maxAbs + (i + 1) * binWidth,
			count: 0,
		}));
		for (const v of vals) {
			const idx = Math.min(Math.floor((v + maxAbs) / binWidth), nBins - 1);
			if (idx >= 0 && idx < nBins) bins[idx].count++;
		}
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const b = bins[p.dataIndex];
					const label = b.right <= 0 ? 'Discordant' : b.left >= 0 ? 'Concordant' : 'Mixed';
					return `<strong style="color:#eceff4">[${b.left.toFixed(4)}, ${b.right.toFixed(4)})</strong>`
						+ `<br/>Count: ${b.count}`
						+ `<br/>${label}`;
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 48 },
			xAxis: {
				type: 'category' as const,
				data: bins.map(b => ((b.left + b.right) / 2).toFixed(3)),
				axisLabel: {
					color: '#b0b8c8', fontSize: 10,
					interval: (_: number, value: string) => {
						const v = parseFloat(value);
						return Math.abs(v) < 0.001 || Math.abs(v - 0.03) < 0.002 || Math.abs(v + 0.03) < 0.002;
					},
				},
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Margin value',
				nameLocation: 'middle' as const,
				nameGap: 22,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: 'Count',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'bar' as const,
				data: bins.map(b => ({
					value: b.count,
					itemStyle: {
						color: b.right <= 0 ? '#ee7a7a' : b.left >= 0 ? '#6cb6ff' : '#8690a2',
						opacity: 0.85,
					},
				})),
				barMaxWidth: 16,
				barMinWidth: 4,
			}],
			backgroundColor: 'transparent',
		};
	});

	/* ── Bar: method comparison (MSE, log scale) ────────────── */
	let methodChartOptions = $derived.by(() => {
		if (!data) return null;
		const m = data.methods;
		const entries = [
			{ label: 'Win count', ...m.win_count },
			{ label: 'Insertion', ...m.insertion },
			{ label: 'Refined', ...m.refined },
			{ label: 'Polished', ...m.polished },
		];
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const e = entries[p.dataIndex];
					return `<strong style="color:#eceff4">${e.label}</strong>`
						+ `<br/>MSE: <span style="color:#6cb6ff">${e.mse.toExponential(2)}</span>`
						+ `<br/>Positions: ${e.correct_positions}/${e.total_positions}`;
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 64 },
			xAxis: {
				type: 'category' as const,
				data: entries.map(e => e.label),
				axisLabel: { color: '#b0b8c8', fontSize: 12 },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: 'log' as const,
				min: 1e-15,
				axisLabel: {
					color: '#b0b8c8', fontSize: 11,
					formatter: (v: number) => v.toExponential(0),
				},
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: 'MSE (log)',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'bar' as const,
				data: entries.map((e, i) => ({
					value: Math.max(e.mse, 1e-15),
					itemStyle: {
						color: i === 0 ? '#ee7a7a' : i === 3 ? '#3dd68c' : '#6cb6ff',
						opacity: i === 0 ? 0.9 : i === 3 ? 1.0 : 0.75,
					},
				})),
				barMaxWidth: 40,
			}],
			backgroundColor: 'transparent',
		};
	});

	const stages: { key: 'win_count' | 'insertion' | 'refined' | 'polished'; label: string; desc: string; fail: boolean }[] = [
		{ key: 'win_count', label: 'Win count', desc: 'Sort by wins', fail: true },
		{ key: 'insertion', label: 'Insertion', desc: 'Greedy insert', fail: false },
		{ key: 'refined', label: 'Refined', desc: 'Pairwise swaps', fail: false },
		{ key: 'polished', label: 'Polished', desc: 'MSE polish', fail: false },
	];

	/* ── Line: polish convergence ───────────────────────────── */
	let polishOptions = $derived.by(() => {
		if (!data) return null;
		const trace = data.polish_trace;
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const t = trace[p.dataIndex];
					return `<strong style="color:#eceff4">Iteration ${t.iteration}</strong>`
						+ `<br/>MSE: <span style="color:#6cb6ff">${t.mse.toExponential(3)}</span>`;
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 64 },
			xAxis: {
				type: 'category' as const,
				data: trace.map(t => t.iteration),
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Polish iteration',
				nameLocation: 'middle' as const,
				nameGap: 24,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: {
				type: 'log' as const,
				min: 1e-15,
				axisLabel: {
					color: '#b0b8c8', fontSize: 11,
					formatter: (v: number) => v.toExponential(0),
				},
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: 'MSE (log)',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'line' as const,
				data: trace.map(t => Math.max(t.mse, 1e-15)),
				lineStyle: { color: '#6cb6ff', width: 2 },
				symbol: 'circle',
				symbolSize: 8,
				itemStyle: { color: '#6cb6ff' },
				markLine: {
					silent: true,
					lineStyle: { color: '#3dd68c33', type: 'dashed' as const, width: 1 },
					data: [{ yAxis: 3.16e-14, label: { formatter: 'exact', color: '#3dd68c', fontSize: 10 } }],
				},
			}],
			backgroundColor: 'transparent',
		};
	});
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python ordering/02_pairwise_tournament.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Nontransitive pairwise preferences hide a solvable ordering</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				For every pair of blocks A and B, run both orderings (A then B vs B then A)
				on the data and compare downstream MSE. This produces a signed margin matrix:
			</p>
			<code class="my-3 block rounded bg-bg-inset px-4 py-2 font-mono text-sm text-accent-cyan">
				margin[i,j] = MSE(j before i) &minus; MSE(i before j)
			</code>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Positive margin means block i should precede block j. The pairwise accuracy
				is <strong class="text-text-primary">{(data.pairwise_accuracy * 100).toFixed(1)}%</strong>
				&mdash; better than chance, but the preferences are nontransitive:
				<strong class="text-text-primary">{(data.nontransitive.cycle_rate * 100).toFixed(1)}%</strong>
				of all triples form cycles (A &gt; B, B &gt; C, C &gt; A).
				Naive sorting by win count collapses this structure and fails.
				Smart extraction via insertion + pairwise refinement preserves enough
				directional signal for MSE polish to finish the job.
			</p>
		</div>

		<!-- ── 2. STATS ────────────────────────────────────────── -->
		<div class="grid grid-cols-4 gap-3">
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Pairwise accuracy</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{(data.pairwise_accuracy * 100).toFixed(1)}%</div>
				<div class="mt-1 text-xs text-text-tertiary">{data.margin_stats.n_concordant}/{data.margin_stats.total_pairs} concordant</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Intransitive triples</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{(data.nontransitive.cycle_rate * 100).toFixed(1)}%</div>
				<div class="mt-1 text-xs text-text-tertiary">{data.nontransitive.n_cycles.toLocaleString()}/{data.nontransitive.n_triples.toLocaleString()} triples</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Median |margin|</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{data.margin_stats.median_abs.toFixed(4)}</div>
				<div class="mt-1 text-xs text-text-tertiary">max {data.margin_stats.max_abs.toFixed(4)}</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polish iterations</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{data.polish_trace.length - 1}</div>
				<div class="mt-1 text-xs text-text-tertiary">to exact solution</div>
			</div>
		</div>

		<!-- ── 3. MARGIN MATRIX HEATMAP ────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Pairwise margin matrix (GT order)</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Rows and columns are sorted by ground-truth position.
				Blue (positive) in the upper triangle means the margin correctly identifies
				that the earlier block should come first.
				Red patches are discordant pairs &mdash; the {data.margin_stats.n_discordant} pairwise
				errors that make the preferences nontransitive and
				defeat naive sorting.
			</p>

			{#if heatmapOptions}
				<div style="width: 100%; height: 420px;">
					<Chart {init} options={heatmapOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#6cb6ff"></span> Positive (i before j)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#ee7a7a"></span> Negative (j before i)</span>
			</div>
		</div>

		<!-- ── 4. MARGIN DISTRIBUTION ──────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Margin strength distribution</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Distribution of all {data.margin_stats.total_pairs.toLocaleString()} upper-triangle margins (GT order).
				Blue bars are concordant (positive: correctly predicts earlier block should come first),
				red bars are discordant.
				Most margins are weak (median {data.margin_stats.median_abs.toFixed(4)}),
				explaining why naive sorting cannot disentangle the noisy pairwise preferences
				into a coherent global order.
			</p>

			{#if histogramOptions}
				<div style="width: 100%; height: 240px;">
					<Chart {init} options={histogramOptions} theme="dark" />
				</div>
			{/if}
		</div>

		<!-- ── 5. METHOD COMPARISON ────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Naive sorting fails; smart extraction works</h3>
			<div class="mb-4 grid grid-cols-4 gap-3">
				{#each stages as stage}
					{@const m = data.methods[stage.key]}
					<div class="rounded-lg px-4 py-3 {stage.fail
						? 'border border-red-500/30 bg-red-500/5'
						: m.correct_positions === m.total_positions
							? 'border border-accent-green/20 bg-accent-green/8'
							: 'border border-border-subtle'}">
						<div class="mb-1 text-xs font-semibold uppercase tracking-wider {stage.fail ? 'text-red-400' : m.correct_positions === m.total_positions ? 'text-accent-green' : 'text-text-tertiary'}">{stage.label}</div>
						<div class="flex items-baseline gap-2">
							<span class="font-mono text-2xl font-bold {stage.fail ? 'text-red-400' : m.correct_positions === m.total_positions ? 'text-accent-green' : 'text-accent-blue'}">
								{m.correct_positions}/{m.total_positions}
							</span>
						</div>
						<div class="mt-1 font-mono text-xs text-text-secondary">MSE {m.mse.toExponential(2)}</div>
						<div class="mt-0.5 text-xs text-text-tertiary">{stage.desc}</div>
					</div>
				{/each}
			</div>

			{#if methodChartOptions}
				<div style="width: 100%; height: 220px;">
					<Chart {init} options={methodChartOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#ee7a7a"></span> Fails (win count)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#6cb6ff"></span> Raw extraction</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#3dd68c"></span> Exact (after polish)</span>
			</div>
		</div>

		<!-- ── 6. POLISH CONVERGENCE ───────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Polish convergence</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Starting from refined MSE {data.methods.refined.mse.toExponential(2)},
				greedy pairwise swap polish converges to the exact solution
				({data.methods.polished.mse.toExponential(2)})
				in {data.polish_trace.length - 2} improving iterations.
				Each iteration tries all O(n&sup2;) position swaps and keeps those that reduce end-to-end MSE.
				The final iteration confirms no improving swap remains.
			</p>

			{#if polishOptions}
				<div style="width: 100%; height: 260px;">
					<Chart {init} options={polishOptions} theme="dark" />
				</div>
			{/if}
		</div>

	</div>
{/if}
