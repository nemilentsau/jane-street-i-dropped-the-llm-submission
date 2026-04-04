<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, LegendComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, LineChart, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, CanvasRenderer]);

	type BeamResult = {
		width: number;
		pairwise_score: number;
		raw_mse: number;
		raw_positions: number;
		total_positions: number;
	};

	type BSData = {
		beam_widths: number[];
		beam_results: BeamResult[];
		best_width_idx: number;
		methods: {
			best_raw: { correct_positions: number; total_positions: number; mse: number; pairwise_score: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: { iteration: number; mse: number }[];
		random_polish_trace: { iteration: number; mse: number }[];
		elapsed_s: number;
	};

	let data: BSData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/ordering_04_beam_search.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	/* ── Beam width comparison chart ───────────────────────── */
	let widthOptions = $derived.by(() => {
		if (!data) return null;
		const results = data.beam_results;
		const bestIdx = data.best_width_idx;

		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
			},
			grid: { top: 30, left: 60, right: 60, bottom: 40 },
			xAxis: {
				type: 'category' as const,
				data: results.map(r => `w=${r.width}`),
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2', fontSize: 12 },
			},
			yAxis: [
				{
					type: 'value' as const,
					name: 'Raw MSE',
					nameTextStyle: { color: '#636e7b', fontSize: 11 },
					axisLine: { lineStyle: { color: '#363e4a' } },
					axisLabel: { color: '#8690a2', formatter: (v: number) => v.toFixed(2) },
					splitLine: { lineStyle: { color: '#2a313b' } },
				},
				{
					type: 'value' as const,
					name: 'Pairwise score',
					nameTextStyle: { color: '#636e7b', fontSize: 11 },
					axisLine: { lineStyle: { color: '#363e4a' } },
					axisLabel: { color: '#8690a2' },
					splitLine: { show: false },
				},
			],
			series: [
				{
					name: 'Raw MSE',
					type: 'bar' as const,
					data: results.map((r, i) => ({
						value: r.raw_mse,
						itemStyle: { color: i === bestIdx ? '#6cb6ff' : '#6cb6ff66' },
					})),
					barWidth: '40%',
				},
				{
					name: 'Pairwise score',
					type: 'line' as const,
					yAxisIndex: 1,
					data: results.map(r => r.pairwise_score),
					lineStyle: { color: '#d2a8ff', width: 2 },
					symbol: 'circle',
					symbolSize: 8,
					itemStyle: { color: '#d2a8ff' },
				},
			],
		};
	});

	/* ── Polish convergence chart ──────────────────────────── */
	let polishOptions = $derived.by(() => {
		if (!data) return null;
		const trace = data.polish_trace;
		const rand = data.random_polish_trace ?? [];

		const series: Record<string, unknown>[] = [
			{
				name: `Beam (w=${data.beam_widths[data.best_width_idx]})`,
				type: 'line',
				data: trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]),
				lineStyle: { color: '#6cb6ff', width: 2.5 },
				symbol: 'circle', symbolSize: 8,
				itemStyle: { color: '#6cb6ff' },
				markLine: {
					silent: true,
					lineStyle: { color: '#3dd68c33', type: 'dashed', width: 1 },
					data: [{ yAxis: 3.16e-14, label: { formatter: 'exact', color: '#3dd68c', fontSize: 10 } }],
				},
			},
		];

		if (rand.length > 0) {
			series.push({
				name: 'Random start',
				type: 'line',
				data: rand.map(p => [p.iteration, p.mse]),
				lineStyle: { color: '#8690a2', width: 2.5, type: 'dashed' },
				symbol: 'circle', symbolSize: 6,
				itemStyle: { color: '#8690a2' },
			});
		}

		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const ps = params as { seriesName: string; value: [number, number]; marker: string }[];
					const iter = ps[0]?.value[0];
					const lines = ps.map(p => {
						const mse = p.value[1];
						const fmt = mse < 1e-10 ? mse.toExponential(2) : mse.toFixed(4);
						return `${p.marker} ${p.seriesName}: <b>${fmt}</b>`;
					});
					return `Iteration ${iter}<br/>` + lines.join('<br/>');
				},
			},
			legend: {
				top: 0,
				textStyle: { color: '#8690a2', fontSize: 12 },
			},
			grid: { top: 40, left: 70, right: 30, bottom: 40 },
			xAxis: {
				type: 'value' as const,
				name: 'Polish iteration',
				nameTextStyle: { color: '#636e7b', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2' },
				splitLine: { show: false },
			},
			yAxis: {
				type: 'log' as const,
				name: 'MSE',
				nameTextStyle: { color: '#636e7b', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: {
					color: '#8690a2',
					formatter: (v: number) => v < 1e-10 ? v.toExponential(0) : v.toFixed(2),
				},
				splitLine: { lineStyle: { color: '#2a313b' } },
			},
			series,
		};
	});

	function fmtMSE(v: number): string {
		return v < 1e-6 ? v.toExponential(2) : v.toFixed(4);
	}
</script>

{#if error}
	<div class="rounded-xl border border-red-500/30 bg-red-500/5 px-6 py-5">
		<p class="text-red-400">Failed to load data: {error}</p>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Widening the search beam</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Greedy insertion (Method 2) picks the single best position for each block.
				Beam search keeps the top-<em>k</em> partial orderings at each step, exploring more
				of the search space at linear cost. Using the same pairwise margin matrix,
				beam width 5 improves raw MSE from 0.12 to 0.09 &mdash; and all widths
				still land in the basin of attraction where polish reaches exact.
			</p>
		</div>

		<!-- ── 2. STATS ────────────────────────────────────────── -->
		<div class="grid grid-cols-4 gap-3">
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Widths tested</div>
				<div class="mt-1 font-mono text-2xl font-bold text-text-primary">{data.beam_widths.length}</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Best width</div>
				<div class="mt-1 font-mono text-2xl font-bold text-phase-ordering">{data.beam_widths[data.best_width_idx]}</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Best raw MSE</div>
				<div class="mt-1 font-mono text-lg font-bold text-accent-amber">{fmtMSE(data.methods.best_raw.mse)}</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polished</div>
				<div class="mt-1 font-mono text-2xl font-bold text-accent-green">{data.methods.polished.correct_positions}/97</div>
			</div>
		</div>

		<!-- ── 3. WIDTH COMPARISON ─────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Beam width comparison</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Raw MSE (bars) and pairwise score (line) for each beam width. Best width highlighted.
			</p>
			<div class="h-64">
				{#if widthOptions}
					<Chart {init} options={widthOptions} />
				{/if}
			</div>

			<!-- Width detail table -->
			<div class="mt-4 overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-2 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Width</th>
							<th class="pb-2 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Pairwise score</th>
							<th class="pb-2 pr-4 text-center text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw positions</th>
							<th class="pb-2 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw MSE</th>
						</tr>
					</thead>
					<tbody>
						{#each data.beam_results as r, i}
							<tr class="border-b border-border-subtle/50 {i === data.best_width_idx ? 'bg-phase-ordering/5' : ''}">
								<td class="py-2 pr-4 font-mono text-sm {i === data.best_width_idx ? 'text-phase-ordering font-semibold' : 'text-text-primary'}">
									w={r.width}
								</td>
								<td class="py-2 pr-4 text-right font-mono text-sm text-text-tertiary">{r.pairwise_score}</td>
								<td class="py-2 pr-4 text-center font-mono text-sm text-accent-amber">{r.raw_positions}/97</td>
								<td class="py-2 text-right font-mono text-sm text-text-tertiary">{fmtMSE(r.raw_mse)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- ── 4. POLISH CONVERGENCE ───────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Polish convergence</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				MSE during greedy pairwise-swap polish from beam search output vs random start (log scale).
			</p>
			<div class="h-72">
				{#if polishOptions}
					<Chart {init} options={polishOptions} />
				{/if}
			</div>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Beam search with width {data.beam_widths[data.best_width_idx]} starts at MSE {fmtMSE(data.methods.best_raw.mse)} and
				reaches exact ({data.methods.polished.mse.toExponential(2)}) in {data.polish_trace.length - 2} improving iterations.
				The random baseline, given the same budget, remains above MSE 0.1.
			</p>
		</div>
	</div>
{/if}
