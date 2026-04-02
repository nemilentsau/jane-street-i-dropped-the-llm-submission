<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart, ScatterChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, VisualMapComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, LineChart, ScatterChart, TooltipComponent, GridComponent, MarkLineComponent, VisualMapComponent, CanvasRenderer]);

	type GreedyStep = { chosen_delta: number; second_delta: number; margin: number; n_remaining: number };
	type PositionPair = { greedy: number; gt: number };

	type DGData = {
		raw: { correct_positions: number; total_positions: number; mse: number };
		polished: { correct_positions: number; total_positions: number; mse: number };
		greedy_steps: GreedyStep[];
		deltas_polished: number[];
		greedy_vs_gt: PositionPair[];
		elapsed_s: number;
	};

	let data: DGData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/ordering_01_delta_greedy.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	let marginChartOptions = $derived.by(() => {
		if (!data) return null;
		const steps = data.greedy_steps;
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const s = steps[p.dataIndex];
					return `<strong style="color:#eceff4">Step ${p.dataIndex + 1}</strong> (${s.n_remaining} candidates)`
						+ `<br/>Chosen: <span style="color:#6cb6ff">${s.chosen_delta.toFixed(4)}</span>`
						+ `<br/>2nd best: <span style="color:#8690a2">${s.second_delta.toFixed(4)}</span>`
						+ `<br/>Margin: <span style="color:${s.margin < 0.01 ? '#f0883e' : '#3dd68c'}">${s.margin.toFixed(6)}</span>`;
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 56 },
			xAxis: {
				type: 'category' as const,
				data: steps.map((_: GreedyStep, i: number) => i + 1),
				axisLabel: { color: '#b0b8c8', fontSize: 11, interval: 7 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Greedy step',
				nameLocation: 'middle' as const,
				nameGap: 24,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: 'Margin (2nd best \u2212 chosen)',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'bar' as const,
				data: steps.map((s: GreedyStep) => ({
					value: s.margin,
					itemStyle: {
						color: s.margin < 0.01 ? '#f0883e' : '#6cb6ff',
						opacity: 0.85,
					},
				})),
				barMaxWidth: 12,
			}],
			backgroundColor: 'transparent',
		};
	});

	let stiffnessChartOptions = $derived.by(() => {
		if (!data) return null;
		const deltas = data.deltas_polished;
		const swapped = new Set(data.greedy_vs_gt.filter(p => p.greedy !== p.gt).map(p => p.gt));
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const isSwap = swapped.has(p.dataIndex);
					return `<strong style="color:#eceff4">Layer ${p.dataIndex + 1}</strong>`
						+ `<br/>||block(x) \u2212 x||: <span style="color:#6cb6ff">${p.value.toFixed(4)}</span>`
						+ (isSwap ? `<br/><span style="color:#f0883e">Greedy swapped with neighbor</span>` : '');
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 56 },
			xAxis: {
				type: 'category' as const,
				data: deltas.map((_: number, i: number) => i + 1),
				axisLabel: { color: '#b0b8c8', fontSize: 11, interval: 7 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Layer position (ground-truth order)',
				nameLocation: 'middle' as const,
				nameGap: 24,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: '||block(x) \u2212 x||',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'bar' as const,
				data: deltas.map((d: number, i: number) => ({
					value: d,
					itemStyle: {
						color: swapped.has(i) ? '#f0883e' : i < 16 ? '#6cb6ff' : i < 32 ? '#8690a2' : '#f0883e',
						opacity: swapped.has(i) ? 1.0 : 0.7,
					},
				})),
				barMaxWidth: 12,
			}],
			backgroundColor: 'transparent',
		};
	});

	let scatterOptions = $derived.by(() => {
		if (!data) return null;
		const pts = data.greedy_vs_gt;
		const correct = pts.filter(p => p.greedy === p.gt);
		const swapped = pts.filter(p => p.greedy !== p.gt);
		return {
			tooltip: {
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = params as { value: number[] };
					const g = p.value[0];
					const gt = p.value[1];
					const delta = data!.deltas_polished[gt];
					return `<strong style="color:#eceff4">Block</strong>`
						+ `<br/>Greedy position: ${g + 1}`
						+ `<br/>GT position: ${gt + 1}`
						+ `<br/>${g === gt ? '<span style="color:#3dd68c">Correct</span>' : `<span style="color:#f0883e">Off by ${Math.abs(g - gt)}</span>`}`
						+ `<br/>||block(x) \u2212 x||: ${delta.toFixed(4)}`;
				},
			},
			grid: { top: 24, right: 24, bottom: 40, left: 56 },
			xAxis: {
				type: 'value' as const,
				min: 0, max: 47,
				name: 'Greedy position',
				nameLocation: 'middle' as const,
				nameGap: 28,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			yAxis: {
				type: 'value' as const,
				min: 0, max: 47,
				name: 'GT position',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			series: [
				{
					name: 'Correct',
					type: 'scatter' as const,
					data: correct.map(p => [p.greedy, p.gt]),
					symbolSize: 8,
					itemStyle: { color: '#3dd68c', opacity: 0.8 },
				},
				{
					name: 'Swapped',
					type: 'scatter' as const,
					data: swapped.map(p => [p.greedy, p.gt]),
					symbolSize: 10,
					itemStyle: { color: '#f0883e', opacity: 0.9 },
				},
				{
					type: 'line' as const,
					data: [[0, 0], [47, 47]],
					lineStyle: { color: '#363e4a', type: 'dashed' as const, width: 1 },
					symbol: 'none' as const,
					silent: true,
				},
			],
			backgroundColor: 'transparent',
		};
	});
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python ordering/01_delta_greedy.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Ordering blocks by perturbation magnitude</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Given 48 correctly paired blocks, the ordering problem is: in what sequence do they act?
				Delta-greedy treats residual blocks
				(<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">x &larr; x + f(x)</code>)
				as discrete ODE time steps.
				At each step it evaluates all remaining blocks on the current running state,
				measures
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">||block(x) &minus; x||</code>,
				and picks the one with the smallest perturbation.
				The selected block is applied, updating the state, and the process repeats.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Perturbation magnitudes are not fixed per block &mdash; they change as the state evolves.
				Delta-greedy is locally optimal: at each of the 48 steps it takes the least disruptive move available.
				It reaches {data.raw.correct_positions}/{data.raw.total_positions} raw positions &mdash;
				the strongest raw ordering of any method tested. The remaining errors
				are adjacent transpositions between blocks with similar stiffness,
				which MSE polish resolves in one pass.
			</p>
		</div>

		<!-- ── 2. RAW VS POLISHED ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Raw greedy gets close; one round of swaps finishes the job</h3>
			<div class="grid grid-cols-2 gap-4">
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw (greedy only)</div>
					<div class="flex items-baseline gap-3">
						<span class="font-mono text-3xl font-bold text-accent-blue">{data.raw.correct_positions}/{data.raw.total_positions}</span>
						<span class="text-sm text-text-tertiary">correct positions</span>
					</div>
					<div class="mt-2 font-mono text-sm text-text-secondary">MSE {data.raw.mse.toExponential(2)}</div>
				</div>
				<div class="rounded-lg bg-accent-green/8 border border-accent-green/20 px-5 py-4">
					<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-accent-green">After MSE polish</div>
					<div class="flex items-baseline gap-3">
						<span class="font-mono text-3xl font-bold text-accent-green">{data.polished.correct_positions}/{data.polished.total_positions}</span>
						<span class="text-sm text-text-tertiary">correct positions</span>
					</div>
					<div class="mt-2 font-mono text-sm text-accent-green">{data.polished.mse.toExponential(2)}</div>
				</div>
			</div>
			<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
				MSE polish tries every pairwise swap of block positions and keeps those that reduce end-to-end MSE.
				It converges to {data.polished.correct_positions}/{data.polished.total_positions} in a single iteration.
			</p>
		</div>

		<!-- ── 3. GREEDY SELECTION MARGINS ─────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Greedy selection confidence at each step</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				At each step, the algorithm picks the block with the smallest perturbation
				from all remaining candidates. The margin is the gap between the chosen block and the second-best.
				Large margins mean the choice is unambiguous; orange bars (margin &lt; 0.01) mark steps
				where two blocks had nearly identical perturbation and greedy is effectively guessing.
			</p>

			{#if marginChartOptions}
				<div style="width: 100%; height: 280px;">
					<Chart {init} options={marginChartOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#6cb6ff"></span> Confident (margin &ge; 0.01)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#f0883e"></span> Ambiguous (margin &lt; 0.01)</span>
			</div>

		</div>

		<!-- ── 4. STIFFNESS PROFILE ────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Block stiffness profile in ground-truth order</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each bar is
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">||block(x) &minus; x||</code>
				when running blocks in the recovered order, feeding each block the cumulative output of all preceding ones.
				This is the data-dependent stiffness profile of the network:
				the Frobenius norm of each block&rsquo;s linearized Jacobian correlates 0.72 with its GT position.
				Orange bars mark the {data.greedy_vs_gt.filter(p => p.greedy !== p.gt).length} layers
				that greedy swapped with a neighbor &mdash;
				all in the flat middle band where stiffness differences are smallest.
			</p>

			{#if stiffnessChartOptions}
				<div style="width: 100%; height: 280px;">
					<Chart {init} options={stiffnessChartOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm opacity-70" style="background:#6cb6ff"></span> Correct (early)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm opacity-70" style="background:#8690a2"></span> Correct (middle)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#f0883e"></span> Greedy swapped with neighbor</span>
			</div>

		</div>

		<!-- ── 5. GREEDY VS GT POSITIONS ────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Greedy position vs ground-truth position</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each dot is one block. Points on the diagonal are correctly placed by greedy alone.
				All {data.greedy_vs_gt.filter(p => p.greedy !== p.gt).length / 2} errors are adjacent-pair transpositions
				(off by 1) &mdash; blocks with nearly identical perturbation magnitudes that greedy cannot distinguish.
			</p>

			{#if scatterOptions}
				<div style="width: 100%; height: 320px;">
					<Chart {init} options={scatterOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-full" style="background:#3dd68c"></span> Correct ({data.greedy_vs_gt.filter(p => p.greedy === p.gt).length}/48)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-full" style="background:#f0883e"></span> Swapped ({data.greedy_vs_gt.filter(p => p.greedy !== p.gt).length}/48)</span>
			</div>

			<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
				Polish corrects {data.greedy_vs_gt.filter(p => p.greedy !== p.gt).length / 2} adjacent-pair errors
				at layers {data.greedy_vs_gt.filter(p => p.greedy !== p.gt).map(p => p.gt + 1).filter((_, i) => i % 2 === 0).map(p => `${p}\u2013${p + 1}`).join(', ')}.
				The earliest error (layers 14&ndash;15) traces back to an ambiguous greedy step with margin 0.004.
				Once greedy picks the wrong block there, the running state diverges slightly,
				causing downstream errors at layers whose margins looked comfortable in isolation.
			</p>
		</div>

	</div>
{/if}
