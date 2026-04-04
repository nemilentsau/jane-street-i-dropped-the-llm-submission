<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, LegendComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([LineChart, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, CanvasRenderer]);

	type SFData = {
		smoothness: {
			gt: number;
			spectral_flow: number;
			random_mean: number;
			random_std: number;
		};
		greedy_steps: { step: number; block_idx: number; jitter: number }[];
		eig_indices: number[];
		gt_eig_traces: number[][];
		sf_eig_traces: number[][];
		methods: {
			raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: { iteration: number; mse: number }[];
		random_polish_trace: { iteration: number; mse: number }[];
		elapsed_s: number;
	};

	let data: SFData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/ordering_05_spectral_flow.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	const eigColors = ['#6cb6ff', '#58a6ff', '#3dd68c', '#a5d6ff', '#d2a8ff', '#f0883e', '#f778ba', '#eceff4'];

	/* ── Eigenvalue trajectory chart ───────────────────────── */
	function eigOptions(traces: number[][], indices: number[], title: string, color: string) {
		const steps = Array.from({ length: traces.length }, (_, i) => i + 1);
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 11 },
			},
			legend: { show: false },
			grid: { top: 30, left: 55, right: 15, bottom: 35 },
			title: {
				text: title,
				left: 'center',
				textStyle: { color: '#eceff4', fontSize: 13, fontWeight: 600 },
			},
			xAxis: {
				type: 'category' as const,
				data: steps,
				name: 'Block step',
				nameTextStyle: { color: '#636e7b', fontSize: 10 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2', fontSize: 10, interval: 11 },
			},
			yAxis: {
				type: 'value' as const,
				name: '|eigenvalue|',
				nameTextStyle: { color: '#636e7b', fontSize: 10 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2', fontSize: 10 },
				splitLine: { lineStyle: { color: '#2a313b' } },
			},
			series: indices.map((eigIdx, i) => ({
				name: `eig ${eigIdx}`,
				type: 'line' as const,
				data: traces.map(row => row[i]),
				showSymbol: false,
				lineStyle: { width: 1.5, color: color === 'multi' ? eigColors[i] : color },
				itemStyle: { color: color === 'multi' ? eigColors[i] : color },
			})),
		};
	}

	let gtEigOptions = $derived.by(() => {
		if (!data) return null;
		return eigOptions(data.gt_eig_traces, data.eig_indices, 'Ground truth ordering', 'multi');
	});

	let sfEigOptions = $derived.by(() => {
		if (!data) return null;
		return eigOptions(data.sf_eig_traces, data.eig_indices, 'Spectral flow ordering', 'multi');
	});

	/* ── Jitter per step chart ─────────────────────────────── */
	let jitterOptions = $derived.by(() => {
		if (!data) return null;
		const steps = data.greedy_steps;
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const ps = params as { value: number; dataIndex: number }[];
					const p = ps[0];
					const s = steps[p.dataIndex];
					return `Step ${s.step + 1}<br/>Block ${s.block_idx}<br/>Jitter: <b>${s.jitter.toFixed(6)}</b>`;
				},
			},
			grid: { top: 20, left: 60, right: 20, bottom: 35 },
			xAxis: {
				type: 'category' as const,
				data: steps.map(s => s.step + 1),
				name: 'Greedy step',
				nameTextStyle: { color: '#636e7b', fontSize: 10 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2', fontSize: 10, interval: 11 },
			},
			yAxis: {
				type: 'log' as const,
				name: 'Jitter',
				nameTextStyle: { color: '#636e7b', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				axisLabel: { color: '#8690a2', formatter: (v: number) => v < 0.001 ? v.toExponential(0) : v.toFixed(3) },
				splitLine: { lineStyle: { color: '#2a313b' } },
			},
			series: [{
				type: 'line' as const,
				data: steps.map(s => s.jitter),
				lineStyle: { color: '#d2a8ff', width: 2 },
				symbol: 'circle', symbolSize: 4,
				itemStyle: { color: '#d2a8ff' },
			}],
		};
	});

	/* ── Polish convergence chart ──────────────────────────── */
	let polishOptions = $derived.by(() => {
		if (!data) return null;
		const trace = data.polish_trace;
		const rand = data.random_polish_trace ?? [];

		const series: Record<string, unknown>[] = [
			{
				name: 'Spectral flow',
				type: 'line',
				data: trace.map(p => [p.iteration, Math.max(p.mse, 1e-15)]),
				lineStyle: { color: '#d2a8ff', width: 2.5 },
				symbol: 'circle', symbolSize: 8,
				itemStyle: { color: '#d2a8ff' },
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
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Ordering from eigenvalue smoothness</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Spectral flow is a completely independent ordering philosophy. Instead of comparing
				block pairs via MSE, it linearizes each block as a Jacobian A<sub>k</sub>&nbsp;=&nbsp;W<sub>out</sub>&thinsp;diag(g)&thinsp;W<sub>inp</sub>,
				then greedily picks the block producing the smoothest eigenvalue transition in
				the cumulative product (I&nbsp;+&nbsp;A<sub>k</sub>)&thinsp;J. The resulting raw ordering is
				weak ({data.methods.raw.correct_positions}/97 positions, MSE&nbsp;{fmtMSE(data.methods.raw.mse)})
				but still lands in the basin of attraction where polish reaches exact.
			</p>
		</div>

		<!-- ── 2. STATS ────────────────────────────────────────── -->
		<div class="grid grid-cols-4 gap-3">
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw positions</div>
				<div class="mt-1 font-mono text-2xl font-bold text-accent-amber">{data.methods.raw.correct_positions}/97</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polished</div>
				<div class="mt-1 font-mono text-2xl font-bold text-accent-green">{data.methods.polished.correct_positions}/97</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">SF smoothness</div>
				<div class="mt-1 font-mono text-lg font-bold text-phase-ordering">{data.smoothness.spectral_flow.toFixed(2)}</div>
			</div>
			<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center card-elevated">
				<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">GT smoothness</div>
				<div class="mt-1 font-mono text-lg font-bold text-text-secondary">{data.smoothness.gt.toFixed(2)}</div>
			</div>
		</div>

		<!-- ── 3. EIGENVALUE TRAJECTORIES ──────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Eigenvalue trajectories</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				8 representative eigenvalue magnitudes of the cumulative Jacobian as blocks are composed.
				Spectral flow (smoothness {data.smoothness.spectral_flow.toFixed(2)}) is smoother than
				GT ({data.smoothness.gt.toFixed(2)}) and random ({data.smoothness.random_mean.toFixed(2)}).
			</p>
			<div class="grid grid-cols-2 gap-4">
				<div class="h-64">
					{#if gtEigOptions}
						<Chart {init} options={gtEigOptions} />
					{/if}
				</div>
				<div class="h-64">
					{#if sfEigOptions}
						<Chart {init} options={sfEigOptions} />
					{/if}
				</div>
			</div>
		</div>

		<!-- ── 4. JITTER PER STEP ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Per-step spectral jitter</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Squared eigenvalue change at each greedy step (log scale). Later steps have less
				freedom but jitter stays low throughout.
			</p>
			<div class="h-56">
				{#if jitterOptions}
					<Chart {init} options={jitterOptions} />
				{/if}
			</div>
		</div>

		<!-- ── 5. POLISH CONVERGENCE ───────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Polish convergence</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				MSE during greedy pairwise-swap polish from spectral flow output vs random start (log scale).
			</p>
			<div class="h-72">
				{#if polishOptions}
					<Chart {init} options={polishOptions} />
				{/if}
			</div>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Despite starting at MSE {fmtMSE(data.methods.raw.mse)} &mdash; far worse than
				pairwise methods &mdash; spectral flow still lands in the exact basin.
				The spectral smoothness objective captures a structural invariant of the
				correct ordering that has nothing to do with prediction error.
			</p>
		</div>
	</div>
{/if}
