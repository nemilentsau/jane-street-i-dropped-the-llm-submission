<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, LegendComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([LineChart, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, CanvasRenderer]);

	type PolishPoint = { iteration: number; mse: number };

	type DGData = {
		raw: { correct_positions: number; total_positions: number; mse: number };
		polished: { correct_positions: number; total_positions: number; mse: number };
		elapsed_s: number;
	};

	type PTData = {
		methods: {
			win_count: { correct_positions: number; total_positions: number; mse: number };
			insertion: { correct_positions: number; total_positions: number; mse: number };
			refined: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: PolishPoint[];
		random_polish_trace?: PolishPoint[];
		elapsed_s: number;
	};

	type SKData = {
		methods: {
			best_raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: PolishPoint[];
		random_polish_trace?: PolishPoint[];
		elapsed_s: number;
	};

	type BSData = {
		beam_widths: number[];
		beam_results: { width: number; raw_mse: number; raw_positions: number }[];
		best_width_idx: number;
		methods: {
			best_raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: PolishPoint[];
		random_polish_trace?: PolishPoint[];
		elapsed_s: number;
	};

	let dg: DGData | null = $state(null);
	let pt: PTData | null = $state(null);
	let sk: SKData | null = $state(null);
	let bs: BSData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const [r1, r2, r3, r4] = await Promise.all([
			fetch('/data/ordering_01_delta_greedy.json'),
			fetch('/data/ordering_02_pairwise_tournament.json'),
			fetch('/data/ordering_03_sinkhorn_ranking.json'),
			fetch('/data/ordering_04_beam_search.json'),
		]);
		if (r1.ok) dg = await r1.json();
		if (r2.ok) pt = await r2.json();
		if (r3.ok) sk = await r3.json();
		if (r4.ok) bs = await r4.json();
		loaded = true;
	}
	loadAll();

	type MethodRow = {
		id: string;
		name: string;
		description: string;
		raw_positions: number;
		raw_mse: number;
		polished_positions: number;
		polished_mse: number;
		polish_iters: number | null;
		time_s: number;
	};

	let methods = $derived.by((): MethodRow[] => {
		const rows: MethodRow[] = [];
		if (dg) rows.push({
			id: '01', name: 'Delta Greedy',
			description: 'Greedy chain of steepest-descent transitions between consecutive blocks',
			raw_positions: dg.raw.correct_positions, raw_mse: dg.raw.mse,
			polished_positions: dg.polished.correct_positions, polished_mse: dg.polished.mse,
			polish_iters: null, time_s: dg.elapsed_s,
		});
		if (pt) rows.push({
			id: '02', name: 'Pairwise Tournament',
			description: 'O(n\u00B2) pairwise comparisons \u2192 insertion + refinement',
			raw_positions: pt.methods.refined.correct_positions, raw_mse: pt.methods.refined.mse,
			polished_positions: pt.methods.polished.correct_positions, polished_mse: pt.methods.polished.mse,
			polish_iters: pt.polish_trace.length - 1, time_s: pt.elapsed_s,
		});
		if (sk) rows.push({
			id: '03', name: 'Sinkhorn Ranking',
			description: 'Soft permutation matrix optimized via Sinkhorn iterations',
			raw_positions: sk.methods.best_raw.correct_positions, raw_mse: sk.methods.best_raw.mse,
			polished_positions: sk.methods.polished.correct_positions, polished_mse: sk.methods.polished.mse,
			polish_iters: sk.polish_trace.length - 1, time_s: sk.elapsed_s,
		});
		if (bs) rows.push({
			id: '04', name: 'Beam Search',
			description: `Insertion beam (width ${bs.beam_widths[bs.best_width_idx]}) over pairwise margins`,
			raw_positions: bs.methods.best_raw.correct_positions, raw_mse: bs.methods.best_raw.mse,
			polished_positions: bs.methods.polished.correct_positions, polished_mse: bs.methods.polished.mse,
			polish_iters: bs.polish_trace.length - 1, time_s: bs.elapsed_s,
		});
		return rows;
	});

	/* ── Combined polish convergence chart ──────────────────── */
	let polishOptions = $derived.by(() => {
		if (!pt && !sk && !bs) return null;

		const series: Record<string, unknown>[] = [];

		if (pt?.polish_trace) {
			series.push({
				name: 'Pairwise tournament',
				type: 'line',
				data: pt.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]),
				lineStyle: { color: '#6cb6ff', width: 2.5 },
				symbol: 'circle', symbolSize: 8,
				itemStyle: { color: '#6cb6ff' },
			});
		}

		if (sk?.polish_trace) {
			series.push({
				name: 'Sinkhorn ranking',
				type: 'line',
				data: sk.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]),
				lineStyle: { color: '#d2a8ff', width: 2.5 },
				symbol: 'diamond', symbolSize: 8,
				itemStyle: { color: '#d2a8ff' },
			});
		}

		if (bs?.polish_trace) {
			series.push({
				name: 'Beam search',
				type: 'line',
				data: bs.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]),
				lineStyle: { color: '#f0883e', width: 2.5 },
				symbol: 'triangle', symbolSize: 8,
				itemStyle: { color: '#f0883e' },
			});
		}

		/* Use the longest random trace */
		const rand = pt?.random_polish_trace ?? bs?.random_polish_trace ?? sk?.random_polish_trace;
		if (rand && rand.length > 0) {
			series.push({
				name: 'Random start',
				type: 'line',
				data: rand.map(p => [p.iteration, p.mse]),
				lineStyle: { color: '#8690a2', width: 2.5, type: 'dashed' },
				symbol: 'circle', symbolSize: 6,
				itemStyle: { color: '#8690a2' },
			});
		}

		/* Exact solution reference line */
		series[0] = {
			...series[0],
			markLine: {
				silent: true,
				lineStyle: { color: '#3dd68c33', type: 'dashed', width: 1 },
				data: [{ yAxis: 3.16e-14, label: { formatter: 'exact', color: '#3dd68c', fontSize: 10 } }],
			},
		};

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

	function fmtTime(s: number): string {
		return s < 1 ? `${s.toFixed(2)}s` : s < 60 ? `${s.toFixed(0)}s` : `${(s / 60).toFixed(1)}m`;
	}
</script>

{#if !loaded}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. HEADLINE ─────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Four methods, one basin of attraction</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The ordering problem &mdash; in what sequence do 48 blocks act &mdash; has 48! &asymp; 10<sup>61</sup> possible permutations.
				Each method below produces a coarse initial ordering (as few as 9/97 correct positions),
				yet greedy MSE polish from any of them converges to the <em>exact</em> solution in under 10 iterations.
				Polish from a random starting point, given the same budget, gets stuck above MSE&nbsp;0.1.
				The methods do not solve the problem directly &mdash; they identify the right basin of attraction.
			</p>
		</div>

		<!-- ── 2. METHOD TABLE ─────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-4 text-lg font-semibold text-text-primary">Method comparison</h3>
			<div class="overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Method</th>
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Approach</th>
							<th class="pb-3 pr-4 text-center text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw positions</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw MSE</th>
							<th class="pb-3 pr-4 text-center text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polished</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polished MSE</th>
							<th class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Time</th>
						</tr>
					</thead>
					<tbody>
						{#each methods as m, i}
							<tr class="border-b border-border-subtle/50 {i % 2 === 0 ? 'bg-bg-inset/30' : ''}">
								<td class="py-3 pr-4">
									<span class="font-mono text-sm text-text-tertiary">{m.id}</span>
									<span class="ml-2 font-medium text-text-primary">{m.name}</span>
								</td>
								<td class="py-3 pr-4 text-sm leading-relaxed text-text-secondary">{m.description}</td>
								<td class="py-3 pr-4 text-center">
									<span class="font-mono text-[15px] {m.raw_positions >= 50 ? 'text-accent-green' : 'text-accent-amber'}">{m.raw_positions}/97</span>
								</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-tertiary">{fmtMSE(m.raw_mse)}</td>
								<td class="py-3 pr-4 text-center">
									<span class="font-mono text-[15px] font-semibold text-accent-green">{m.polished_positions}/97</span>
								</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-accent-green">{fmtMSE(m.polished_mse)}</td>
								<td class="py-3 text-right font-mono text-sm text-text-tertiary">{fmtTime(m.time_s)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- ── 3. POLISH CONVERGENCE ──────────────────────────── -->
		{#if polishOptions}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Polish convergence: method vs random start</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					Greedy pairwise-swap polish (log MSE) starting from each method's output vs a random permutation.
				</p>
				<div class="h-80">
					<Chart {init} options={polishOptions} />
				</div>
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					Both methods reach machine-precision MSE (3.16&times;10<sup>-14</sup>) within a few iterations.
					The random-start baseline, given the same polish budget, plateaus above 0.1 &mdash;
					trapped in a local minimum with no improving swap.
					This gap is the core contribution of the ordering methods:
					<strong>they don't need to be right everywhere &mdash; just close enough for polish to finish the job.</strong>
				</p>
			</div>
		{/if}

		<!-- ── 4. BASIN OF ATTRACTION ─────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-4 text-lg font-semibold text-text-primary">Why coarse orderings are enough</h3>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">The MSE landscape has deep wells</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						The correct ordering sits in a steep-walled basin where every swap away
						increases MSE sharply. Once inside this basin, greedy polish follows the
						gradient to the exact minimum &mdash; no backtracking needed.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">Random starts land outside</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						A random permutation starts far from any good basin.
						Polish finds the nearest local minimum, but that minimum is orders of
						magnitude worse than the global one. The landscape has many
						shallow traps and one deep well.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">9/97 is close enough</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						Even orderings with only 9 correct positions out of 97 can be close
						in swap-distance to the true ordering. The number of correct positions
						is misleading &mdash; what matters is being within the basin of attraction,
						and all three methods reliably land there.
					</p>
				</div>
			</div>
		</div>
	</div>
{/if}
