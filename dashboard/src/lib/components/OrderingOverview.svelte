<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { LineChart, HeatmapChart, BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, VisualMapComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([LineChart, HeatmapChart, BarChart, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, VisualMapComponent, CanvasRenderer]);

	type PolishPoint = { iteration: number; mse: number };

	type DGData = {
		raw: { correct_positions: number; total_positions: number; mse: number };
		polished: { correct_positions: number; total_positions: number; mse: number };
		elapsed_s: number;
	};
	type PTData = {
		methods: {
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
		best_width_idx: number;
		methods: {
			best_raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: PolishPoint[];
		random_polish_trace?: PolishPoint[];
		elapsed_s: number;
	};
	type SFData = {
		methods: {
			raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: PolishPoint[];
		random_polish_trace?: PolishPoint[];
		elapsed_s: number;
	};

	type PolishPathPoint = {
		iteration: number; mse: number;
		kendall_tau: number; cayley: number;
		correct_positions: number;
	};

	type OverviewData = {
		method_names: string[];
		raw_stats: Record<string, { mse: number; correct_positions: number }>;
		kendall_matrix: number[][];
		cayley_matrix: number[][];
		displacement: Record<string, number[]>;
		polish_paths: Record<string, PolishPathPoint[]>;
		elapsed_s: number;
	};

	let dg: DGData | null = $state(null);
	let pt: PTData | null = $state(null);
	let sk: SKData | null = $state(null);
	let bs: BSData | null = $state(null);
	let sf: SFData | null = $state(null);
	let ov: OverviewData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const [r1, r2, r3, r4, r5, r6] = await Promise.all([
			fetch('/data/ordering_01_delta_greedy.json'),
			fetch('/data/ordering_02_pairwise_tournament.json'),
			fetch('/data/ordering_03_sinkhorn_ranking.json'),
			fetch('/data/ordering_04_beam_search.json'),
			fetch('/data/ordering_05_spectral_flow.json'),
			fetch('/data/ordering_00_overview.json'),
		]);
		if (r1.ok) dg = await r1.json();
		if (r2.ok) pt = await r2.json();
		if (r3.ok) sk = await r3.json();
		if (r4.ok) bs = await r4.json();
		if (r5.ok) sf = await r5.json();
		if (r6.ok) ov = await r6.json();
		loaded = true;
	}
	loadAll();

	type MethodRow = {
		id: string; name: string; description: string;
		raw_positions: number; raw_mse: number;
		polished_positions: number; polished_mse: number;
		polish_iters: number | null; time_s: number;
	};

	let methods = $derived.by((): MethodRow[] => {
		const rows: MethodRow[] = [];
		if (dg) rows.push({ id: '01', name: 'Delta Greedy', description: 'Greedy chain of steepest-descent transitions', raw_positions: dg.raw.correct_positions, raw_mse: dg.raw.mse, polished_positions: dg.polished.correct_positions, polished_mse: dg.polished.mse, polish_iters: null, time_s: dg.elapsed_s });
		if (pt) rows.push({ id: '02', name: 'Pairwise Tournament', description: 'O(n\u00B2) pairwise comparisons \u2192 insertion + refinement', raw_positions: pt.methods.refined.correct_positions, raw_mse: pt.methods.refined.mse, polished_positions: pt.methods.polished.correct_positions, polished_mse: pt.methods.polished.mse, polish_iters: pt.polish_trace.length - 1, time_s: pt.elapsed_s });
		if (sk) rows.push({ id: '03', name: 'Sinkhorn Ranking', description: 'Soft permutation matrix via Sinkhorn iterations', raw_positions: sk.methods.best_raw.correct_positions, raw_mse: sk.methods.best_raw.mse, polished_positions: sk.methods.polished.correct_positions, polished_mse: sk.methods.polished.mse, polish_iters: sk.polish_trace.length - 1, time_s: sk.elapsed_s });
		if (bs) rows.push({ id: '04', name: 'Beam Search', description: `Insertion beam (w=${bs.beam_widths[bs.best_width_idx]}) over pairwise margins`, raw_positions: bs.methods.best_raw.correct_positions, raw_mse: bs.methods.best_raw.mse, polished_positions: bs.methods.polished.correct_positions, polished_mse: bs.methods.polished.mse, polish_iters: bs.polish_trace.length - 1, time_s: bs.elapsed_s });
		if (sf) rows.push({ id: '05', name: 'Spectral Flow', description: 'Greedy eigenvalue-smoothness of linearized Jacobians', raw_positions: sf.methods.raw.correct_positions, raw_mse: sf.methods.raw.mse, polished_positions: sf.methods.polished.correct_positions, polished_mse: sf.methods.polished.mse, polish_iters: sf.polish_trace.length - 1, time_s: sf.elapsed_s });
		return rows;
	});

	/* ── MSE polish convergence chart ──────────────────────── */
	let polishOptions = $derived.by(() => {
		if (!pt && !sk && !bs && !sf) return null;
		const series: Record<string, unknown>[] = [];
		if (pt?.polish_trace) series.push({ name: 'Pairwise tournament', type: 'line', data: pt.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]), lineStyle: { color: '#6cb6ff', width: 2.5 }, symbol: 'circle', symbolSize: 8, itemStyle: { color: '#6cb6ff' } });
		if (sk?.polish_trace) series.push({ name: 'Sinkhorn ranking', type: 'line', data: sk.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]), lineStyle: { color: '#d2a8ff', width: 2.5 }, symbol: 'diamond', symbolSize: 8, itemStyle: { color: '#d2a8ff' } });
		if (bs?.polish_trace) series.push({ name: 'Beam search', type: 'line', data: bs.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]), lineStyle: { color: '#f0883e', width: 2.5 }, symbol: 'triangle', symbolSize: 8, itemStyle: { color: '#f0883e' } });
		if (sf?.polish_trace) series.push({ name: 'Spectral flow', type: 'line', data: sf.polish_trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]), lineStyle: { color: '#f778ba', width: 2.5 }, symbol: 'rect', symbolSize: 7, itemStyle: { color: '#f778ba' } });
		const rand = pt?.random_polish_trace ?? bs?.random_polish_trace ?? sf?.random_polish_trace ?? sk?.random_polish_trace;
		if (rand && rand.length > 0) series.push({ name: 'Random start', type: 'line', data: rand.map(p => [p.iteration, p.mse]), lineStyle: { color: '#8690a2', width: 2.5, type: 'dashed' }, symbol: 'circle', symbolSize: 6, itemStyle: { color: '#8690a2' } });
		if (series.length > 0) series[0] = { ...series[0], markLine: { silent: true, lineStyle: { color: '#3dd68c33', type: 'dashed', width: 1 }, data: [{ yAxis: 3.16e-14, label: { formatter: 'exact', color: '#3dd68c', fontSize: 10 } }] } };
		return { tooltip: { trigger: 'axis' as const, backgroundColor: '#1c2128', borderColor: '#363e4a', textStyle: { color: '#eceff4', fontSize: 12 }, formatter: (params: unknown) => { const ps = params as { seriesName: string; value: [number, number]; marker: string }[]; const iter = ps[0]?.value[0]; return `Iteration ${iter}<br/>` + ps.map(p => { const mse = p.value[1]; return `${p.marker} ${p.seriesName}: <b>${mse < 1e-10 ? mse.toExponential(2) : mse.toFixed(4)}</b>`; }).join('<br/>'); } }, legend: { top: 0, textStyle: { color: '#8690a2', fontSize: 12 } }, grid: { top: 40, left: 70, right: 30, bottom: 40 }, xAxis: { type: 'value' as const, name: 'Polish iteration', nameTextStyle: { color: '#636e7b', fontSize: 11 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2' }, splitLine: { show: false } }, yAxis: { type: 'log' as const, name: 'MSE', nameTextStyle: { color: '#636e7b', fontSize: 11 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2', formatter: (v: number) => v < 1e-10 ? v.toExponential(0) : v.toFixed(2) }, splitLine: { lineStyle: { color: '#2a313b' } } }, series };
	});

	/* ── Distance heatmap ──────────────────────────────────── */
	const methodLabels: Record<string, string> = {
		gt: 'GT', '01_delta_greedy': 'Delta', '02_pairwise': 'Pairwise',
		'03_sinkhorn': 'Sinkhorn', '04_beam': 'Beam', '05_spectral': 'Spectral',
		random_0: 'Rand 0', random_1: 'Rand 1', random_2: 'Rand 2',
		random_3: 'Rand 3', random_4: 'Rand 4',
	};

	let distanceOptions = $derived.by(() => {
		if (!ov) return null;
		const names = ov.method_names;
		const labels = names.map(n => methodLabels[n] ?? n);
		const n = names.length;
		const data: [number, number, number][] = [];
		let maxVal = 0;
		for (let i = 0; i < n; i++)
			for (let j = 0; j < n; j++) {
				const v = ov.cayley_matrix[i][j];
				data.push([j, i, v]);
				if (v > maxVal) maxVal = v;
			}

		return {
			tooltip: {
				formatter: (p: unknown) => {
					const d = p as { value: [number, number, number] };
					return `${labels[d.value[1]]} \u2194 ${labels[d.value[0]]}<br/>Cayley distance: <b>${d.value[2]}</b>`;
				},
			},
			grid: { top: 10, left: 70, right: 50, bottom: 60 },
			xAxis: { type: 'category' as const, data: labels, axisLabel: { color: '#8690a2', fontSize: 10, rotate: 45 }, axisLine: { lineStyle: { color: '#363e4a' } } },
			yAxis: { type: 'category' as const, data: labels, axisLabel: { color: '#8690a2', fontSize: 10 }, axisLine: { lineStyle: { color: '#363e4a' } } },
			visualMap: { min: 0, max: maxVal, calculable: false, orient: 'vertical' as const, right: 0, top: 10, inRange: { color: ['#0d1117', '#1a3a5c', '#6cb6ff', '#f0883e', '#da3633'] }, textStyle: { color: '#8690a2' } },
			series: [{ type: 'heatmap' as const, data, label: { show: true, color: '#eceff4', fontSize: 9, formatter: (p: unknown) => { const d = p as { value: [number, number, number] }; return d.value[2] === 0 ? '' : String(d.value[2]); } } }],
		};
	});

	/* ── Block displacement chart ──────────────────────────── */
	const dispColors: Record<string, string> = {
		'01_delta_greedy': '#3dd68c', '02_pairwise': '#6cb6ff',
		'03_sinkhorn': '#d2a8ff', '04_beam': '#f0883e', '05_spectral': '#f778ba',
	};
	const dispLabels: Record<string, string> = {
		'01_delta_greedy': 'Delta Greedy', '02_pairwise': 'Pairwise',
		'03_sinkhorn': 'Sinkhorn', '04_beam': 'Beam', '05_spectral': 'Spectral',
	};

	let displacementOptions = $derived.by(() => {
		if (!ov?.displacement) return null;
		const keys = Object.keys(ov.displacement);
		const blockLabels = Array.from({ length: 48 }, (_, i) => String(i));

		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 11 },
			},
			legend: { top: 0, textStyle: { color: '#8690a2', fontSize: 11 } },
			grid: { top: 35, left: 50, right: 15, bottom: 35 },
			xAxis: { type: 'category' as const, data: blockLabels, name: 'Block index (GT order)', nameTextStyle: { color: '#636e7b', fontSize: 10 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2', fontSize: 9, interval: 5 } },
			yAxis: { type: 'value' as const, name: 'Displacement', nameTextStyle: { color: '#636e7b', fontSize: 10 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2' }, splitLine: { lineStyle: { color: '#2a313b' } } },
			series: keys.map(k => ({
				name: dispLabels[k] ?? k,
				type: 'line' as const,
				data: ov!.displacement[k],
				showSymbol: false,
				lineStyle: { width: 1.5, color: dispColors[k] ?? '#8690a2' },
				itemStyle: { color: dispColors[k] ?? '#8690a2' },
			})),
		};
	});

	/* ── Polish path: Cayley distance to GT ────────────────── */
	const pathColors: Record<string, string> = {
		'01_delta_greedy': '#3dd68c', '02_pairwise': '#6cb6ff',
		'03_sinkhorn': '#d2a8ff', '04_beam': '#f0883e',
		'05_spectral': '#f778ba', 'random_0': '#8690a2',
	};
	const pathLabels: Record<string, string> = {
		'01_delta_greedy': 'Delta Greedy', '02_pairwise': 'Pairwise',
		'03_sinkhorn': 'Sinkhorn', '04_beam': 'Beam',
		'05_spectral': 'Spectral', 'random_0': 'Random',
	};

	let cayleyPathOptions = $derived.by(() => {
		if (!ov?.polish_paths) return null;
		const keys = Object.keys(ov.polish_paths);
		return {
			tooltip: { trigger: 'axis' as const, backgroundColor: '#1c2128', borderColor: '#363e4a', textStyle: { color: '#eceff4', fontSize: 12 } },
			legend: { top: 0, textStyle: { color: '#8690a2', fontSize: 11 } },
			grid: { top: 35, left: 55, right: 15, bottom: 40 },
			xAxis: { type: 'value' as const, name: 'Polish iteration', nameTextStyle: { color: '#636e7b', fontSize: 11 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2' }, splitLine: { show: false } },
			yAxis: { type: 'value' as const, name: 'Cayley distance to GT', nameTextStyle: { color: '#636e7b', fontSize: 11 }, axisLine: { lineStyle: { color: '#363e4a' } }, axisLabel: { color: '#8690a2' }, splitLine: { lineStyle: { color: '#2a313b' } } },
			series: keys.map(k => ({
				name: pathLabels[k] ?? k,
				type: 'line' as const,
				data: ov!.polish_paths[k].map(p => [p.iteration, p.cayley]),
				lineStyle: { width: 2.5, color: pathColors[k] ?? '#8690a2', type: k.startsWith('random') ? 'dashed' as const : 'solid' as const },
				symbol: 'circle', symbolSize: 6,
				itemStyle: { color: pathColors[k] ?? '#8690a2' },
			})),
		};
	});

	function fmtMSE(v: number): string { return v < 1e-6 ? v.toExponential(2) : v.toFixed(4); }
	function fmtTime(s: number): string { return s < 1 ? `${s.toFixed(2)}s` : s < 60 ? `${s.toFixed(0)}s` : `${(s / 60).toFixed(1)}m`; }
</script>

{#if !loaded}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. HEADLINE ─────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Five methods, one basin of attraction</h3>
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
								<td class="py-3 pr-4"><span class="font-mono text-sm text-text-tertiary">{m.id}</span> <span class="ml-2 font-medium text-text-primary">{m.name}</span></td>
								<td class="py-3 pr-4 text-sm leading-relaxed text-text-secondary">{m.description}</td>
								<td class="py-3 pr-4 text-center"><span class="font-mono text-[15px] {m.raw_positions >= 50 ? 'text-accent-green' : 'text-accent-amber'}">{m.raw_positions}/97</span></td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-tertiary">{fmtMSE(m.raw_mse)}</td>
								<td class="py-3 pr-4 text-center"><span class="font-mono text-[15px] font-semibold text-accent-green">{m.polished_positions}/97</span></td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-accent-green">{fmtMSE(m.polished_mse)}</td>
								<td class="py-3 text-right font-mono text-sm text-text-tertiary">{fmtTime(m.time_s)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- ── 3. MSE POLISH CONVERGENCE ──────────────────────── -->
		{#if polishOptions}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Polish convergence: MSE</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					Each method's raw ordering is refined by exhaustive pairwise-swap search over full-network MSE.
					The y-axis is log-scale: machine precision (3.16&times;10<sup>-14</sup>) is 12 orders of magnitude below
					the random baseline's plateau.
				</p>
				<div class="h-80">
					<Chart {init} options={polishOptions} />
				</div>
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					The chart above is the headline result. All four methods (pairwise, sinkhorn, beam, spectral flow)
					drop from raw MSE 0.09&ndash;0.66 to exact in 4&ndash;8 polish iterations. The dashed line shows the
					same polish procedure starting from a random permutation &mdash; it makes steady progress
					but plateaus above MSE 0.1, trapped in a local minimum. The ordering methods do not need
					to be accurate; they need to start in the right basin.
				</p>
			</div>
		{/if}

		<!-- ── 4. CAYLEY DISTANCE TO GT DURING POLISH ─────────── -->
		{#if cayleyPathOptions}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Polish convergence: structural distance to ground truth</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					Cayley distance counts the minimum number of pairwise swaps needed to transform one ordering into another.
					This measures how structurally far each ordering is from the ground truth at each polish step.
				</p>
				<div class="h-72">
					<Chart {init} options={cayleyPathOptions} />
				</div>
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					This is the companion to the MSE chart above, but measures structure instead of prediction quality.
					Methods start at Cayley distance 5&ndash;42 from GT and converge to 0 &mdash; the polish is not just
					finding <em>any</em> low-MSE ordering, it is converging to the <em>unique</em> ground truth permutation.
					The random start (dashed) hovers at distance ~42&ndash;44 throughout all 10 iterations: MSE polish
					rearranges blocks, but never moves the ordering closer to GT. It is optimizing in a
					completely different region of permutation space.
				</p>
			</div>
		{/if}

		<!-- ── 5. CAYLEY DISTANCE HEATMAP ─────────────────────── -->
		{#if distanceOptions}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Pairwise Cayley distance between raw orderings</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					Each cell shows the minimum number of transpositions to transform one raw ordering into another.
					Dark cells are close; bright cells are far apart.
				</p>
				<div class="h-96">
					<Chart {init} options={distanceOptions} />
				</div>
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					A surprising pattern: in Cayley distance, spectral flow (41 swaps from GT) is almost
					indistinguishable from random orderings (40&ndash;44 swaps). Yet spectral flow polishes to exact
					and random does not. The basin boundary is not a simple sphere in swap-distance space &mdash;
					it depends on <em>which</em> blocks are displaced, not just how many.
					Delta greedy stands out at only 5 swaps from GT, explaining its near-perfect raw score of 77/97.
				</p>
			</div>
		{/if}

		<!-- ── 6. BLOCK DISPLACEMENT FROM GT ───────────────────── -->
		{#if displacementOptions}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Per-block displacement from ground truth</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					For each block (in GT order along the x-axis), the y-value shows how many positions away
					it was placed in each method's raw ordering. Zero means the block is already in the correct position.
				</p>
				<div class="h-64">
					<Chart {init} options={displacementOptions} />
				</div>
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					This resolves the Cayley distance puzzle above. Delta greedy (green) displaces most blocks
					by 0&ndash;1 positions (mean 0.2). The pairwise methods (blue, purple, orange) have mean displacement
					4&ndash;5, with most blocks off by a few positions and rare outliers up to ~20.
					Spectral flow (pink) has the widest scatter (mean 8.3, max 26) yet still polishes to exact.
					The key difference from random: in random orderings, <em>every</em> block is far from home.
					In method orderings, most blocks are close &mdash; polish only needs to fix the outliers.
				</p>
			</div>
		{/if}

		<!-- ── 7. BASIN NARRATIVE ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-4 text-lg font-semibold text-text-primary">What the basin comparison reveals</h3>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">Correct positions are misleading</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						Spectral flow and pairwise methods both show 9/97 correct positions,
						but their Cayley distances to GT differ significantly. Position count
						is a poor proxy for basin membership &mdash; what matters is whether
						the blocks are <em>close</em> to their correct positions, not exactly there.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">Methods are closer to each other than to random</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						The distance heatmap shows a clear cluster: all 5 methods are structurally
						closer to GT (and to each other) than random orderings are. Even spectral
						flow, which uses no MSE signal at all, lands in the same neighborhood.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-primary">One funnel, many entry points</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						The Cayley convergence chart shows all methods entering the same
						funnel toward GT. The random start makes progress too &mdash; but its funnel
						leads to a local minimum, not the global one. The basin boundary
						is the critical threshold that methods cross and random orderings do not.
					</p>
				</div>
			</div>
		</div>
	</div>
{/if}
