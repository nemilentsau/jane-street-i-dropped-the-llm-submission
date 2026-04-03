<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent, LegendComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, LineChart, TooltipComponent, GridComponent, MarkLineComponent, LegendComponent, CanvasRenderer]);

	type Restart = {
		seed: number;
		mse: number;
		correct_positions: number;
		total_positions: number;
		best_score: number;
		training_curve: { epoch: number; score: number; tau: number }[];
	};

	type SinkhornData = {
		restarts: Restart[];
		best_restart_idx: number;
		soft_matrix_reordered: number[][];
		position_confidence: number[];
		methods: {
			best_raw: { correct_positions: number; total_positions: number; mse: number };
			polished: { correct_positions: number; total_positions: number; mse: number };
		};
		polish_trace: { iteration: number; mse: number }[];
		elapsed_s: number;
	};

	let data: SinkhornData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/ordering_03_sinkhorn_ranking.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	/* ── Training curve: best restart + temperature ─────────── */
	let trainingOptions = $derived.by(() => {
		if (!data) return null;
		const best = data.restarts[data.best_restart_idx];
		const curve = best.training_curve;
		const epochs = curve.map(p => p.epoch);

		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const ps = params as { seriesName: string; dataIndex: number; value: number }[];
					const idx = ps[0].dataIndex;
					const p = curve[idx];
					return `<strong style="color:#eceff4">Epoch ${p.epoch}</strong>`
						+ `<br/>Score: <span style="color:#6cb6ff">${p.score.toFixed(3)}</span>`
						+ `<br/>τ: <span style="color:#f0b429">${p.tau.toFixed(3)}</span>`;
				},
			},
			legend: {
				data: ['Pairwise score', 'Temperature τ'],
				textStyle: { color: '#8690a2', fontSize: 10 },
				top: 0,
				itemWidth: 14,
				itemHeight: 8,
			},
			grid: { top: 32, right: 52, bottom: 36, left: 56 },
			xAxis: {
				type: 'category' as const,
				data: epochs,
				axisLabel: { color: '#b0b8c8', fontSize: 11, interval: 39 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Epoch',
				nameLocation: 'middle' as const,
				nameGap: 22,
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			yAxis: [
				{
					type: 'value' as const,
					min: 0,
					axisLabel: { color: '#b0b8c8', fontSize: 11 },
					axisLine: { lineStyle: { color: '#363e4a' } },
					splitLine: { lineStyle: { color: '#262d38' } },
					name: 'Pairwise score',
					nameTextStyle: { color: '#8690a2', fontSize: 11 },
				},
				{
					type: 'value' as const,
					min: 0,
					max: 1.1,
					axisLabel: { color: '#f0b429', fontSize: 10, formatter: (v: number) => v.toFixed(1) },
					axisLine: { lineStyle: { color: '#f0b42966' } },
					splitLine: { show: false },
					name: 'τ',
					nameTextStyle: { color: '#f0b429', fontSize: 11 },
				},
			],
			series: [
				{
					name: 'Pairwise score',
					type: 'line' as const,
					data: curve.map(p => p.score),
					lineStyle: { color: '#6cb6ff', width: 2.5 },
					itemStyle: { color: '#6cb6ff' },
					symbol: 'none' as const,
					areaStyle: { color: 'rgba(108,182,255,0.06)' },
				},
				{
					name: 'Temperature τ',
					type: 'line' as const,
					yAxisIndex: 1,
					data: curve.map(p => p.tau),
					lineStyle: { color: '#f0b429', width: 2, type: 'dashed' as const },
					itemStyle: { color: '#f0b429' },
					symbol: 'none' as const,
				},
			],
			backgroundColor: 'transparent',
		};
	});

	/* ── Multi-restart MSE comparison ───────────────────────── */
	let restartOptions = $derived.by(() => {
		if (!data) return null;
		const bestIdx = data.best_restart_idx;
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const r = data!.restarts[p.dataIndex];
					return `<strong style="color:#eceff4">Seed ${r.seed}${p.dataIndex === bestIdx ? ' (best)' : ''}</strong>`
						+ `<br/>MSE: <span style="color:#6cb6ff">${r.mse.toExponential(3)}</span>`
						+ `<br/>Positions: ${r.correct_positions}/${r.total_positions}`
						+ `<br/>Score: ${r.best_score.toFixed(3)}`;
				},
			},
			grid: { top: 8, right: 24, bottom: 28, left: 56 },
			xAxis: {
				type: 'category' as const,
				data: data.restarts.map(r => `Seed ${r.seed}`),
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
				name: 'Raw MSE',
				nameTextStyle: { color: '#8690a2', fontSize: 11 },
			},
			series: [{
				type: 'bar' as const,
				data: data.restarts.map((r, i) => ({
					value: r.mse,
					itemStyle: {
						color: i === bestIdx ? '#3dd68c' : '#6cb6ff',
						opacity: i === bestIdx ? 1.0 : 0.6,
					},
				})),
				barMaxWidth: 36,
			}],
			backgroundColor: 'transparent',
		};
	});

	/* ── Polish convergence ─────────────────────────────────── */
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
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python ordering/03_sinkhorn_ranking.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Continuous optimization over soft permutations</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Instead of searching combinatorially, relax the permutation to a
				continuous doubly-stochastic matrix Q (each row and column sums to 1)
				and optimize with gradient descent. The Sinkhorn operator
				projects any matrix onto the doubly-stochastic polytope via alternating
				row/column normalization in log-space.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The objective is the <strong class="text-text-primary">expected pairwise score</strong>
				under the soft permutation: how well does Q respect the pairwise margin preferences?
				Temperature &tau; controls sharpness &mdash; starting at 1.0 (uniform, exploratory)
				and annealing to 0.03 (near-deterministic). After 200 epochs, extract a hard ordering
				via linear assignment on the converged soft matrix.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Five random restarts (seeds 0&ndash;4) land in different local optima.
				The best achieves <strong class="text-text-primary">{data.methods.best_raw.correct_positions}/{data.methods.best_raw.total_positions}</strong> raw positions
				(MSE {data.methods.best_raw.mse.toExponential(2)}) &mdash;
				far from exact, but close enough for MSE polish to finish the job.
			</p>
		</div>

		<!-- ── 2. STATS ────────────────────────────────────────── -->
		<div class="grid grid-cols-4 gap-3">
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Best raw</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{data.methods.best_raw.correct_positions}/{data.methods.best_raw.total_positions}</div>
				<div class="mt-1 text-xs text-text-tertiary">seed {data.best_restart_idx}</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Raw MSE range</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{Math.min(...data.restarts.map(r => r.mse)).toFixed(3)}</div>
				<div class="mt-1 text-xs text-text-tertiary">to {Math.max(...data.restarts.map(r => r.mse)).toFixed(3)}</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Restarts</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{data.restarts.length}</div>
				<div class="mt-1 text-xs text-text-tertiary">random seeds</div>
			</div>
			<div class="rounded-lg border border-border-subtle px-4 py-3">
				<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Polish iterations</div>
				<div class="font-mono text-2xl font-bold text-accent-blue">{data.polish_trace.filter(t => t.mse > 1e-10).length - 1}</div>
				<div class="mt-1 text-xs text-text-tertiary">to exact</div>
			</div>
		</div>

		<!-- ── 3. RAW VS POLISHED ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Landing in the right basin is enough</h3>
			<div class="grid grid-cols-2 gap-4">
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Best raw (Sinkhorn)</div>
					<div class="flex items-baseline gap-3">
						<span class="font-mono text-3xl font-bold text-accent-blue">{data.methods.best_raw.correct_positions}/{data.methods.best_raw.total_positions}</span>
						<span class="text-sm text-text-tertiary">correct positions</span>
					</div>
					<div class="mt-2 font-mono text-sm text-text-secondary">MSE {data.methods.best_raw.mse.toExponential(2)}</div>
				</div>
				<div class="rounded-lg bg-accent-green/8 border border-accent-green/20 px-5 py-4">
					<div class="mb-1 text-xs font-semibold uppercase tracking-wider text-accent-green">After MSE polish</div>
					<div class="flex items-baseline gap-3">
						<span class="font-mono text-3xl font-bold text-accent-green">{data.methods.polished.correct_positions}/{data.methods.polished.total_positions}</span>
						<span class="text-sm text-text-tertiary">correct positions</span>
					</div>
					<div class="mt-2 font-mono text-sm text-accent-green">{data.methods.polished.mse.toExponential(2)}</div>
				</div>
			</div>
			<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
				Sinkhorn converges to a confident solution (position confidence &gt; {Math.min(...data.position_confidence).toFixed(2)} everywhere)
				that is far from exact but in the correct basin.
				Greedy pairwise swap polish closes the remaining gap
				in {data.polish_trace.filter(t => t.mse > 1e-10).length - 1} improving iterations.
			</p>
		</div>

		<!-- ── 4. TRAINING CURVE ───────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Score convergence and temperature annealing</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				The pairwise score climbs rapidly in the first ~20 epochs as the
				soft matrix leaves uniformity, then plateaus while temperature &tau;
				continues annealing from 1.0 to 0.03. The remaining 180 epochs
				sharpen the soft matrix toward a hard permutation without
				meaningfully improving the objective. All five restarts follow
				essentially the same trajectory
				(final scores {Math.min(...data.restarts.map(r => r.best_score)).toFixed(2)}&ndash;{Math.max(...data.restarts.map(r => r.best_score)).toFixed(2)},
				spread &lt; 0.5%) &mdash; the deterministic temperature schedule
				dominates the optimization path.
			</p>

			{#if trainingOptions}
				<div style="width: 100%; height: 300px;">
					<Chart {init} options={trainingOptions} theme="dark" />
				</div>
			{/if}
		</div>

		<!-- ── 5. MULTI-RESTART COMPARISON ─────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Raw MSE per restart</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				All five restarts land in the same MSE range (0.12&ndash;0.16).
				The spread is narrow &mdash; no restart catastrophically fails.
				Seed {data.best_restart_idx} achieves the lowest raw MSE
				({data.methods.best_raw.mse.toExponential(3)})
				with {data.methods.best_raw.correct_positions}/{data.methods.best_raw.total_positions} correct positions.
			</p>

			{#if restartOptions}
				<div style="width: 100%; height: 200px;">
					<Chart {init} options={restartOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 grid grid-cols-5 gap-2 text-center text-xs">
				{#each data.restarts as r, i}
					<div class="rounded border px-2 py-1.5 {i === data.best_restart_idx ? 'border-accent-green/30 bg-accent-green/8 text-accent-green' : 'border-border-subtle text-text-tertiary'}">
						<div class="font-mono font-semibold">{r.correct_positions}/97</div>
						<div class="mt-0.5">{r.mse.toFixed(4)}</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- ── 6. POLISH CONVERGENCE ───────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Polish convergence</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Starting from Sinkhorn&rsquo;s best raw MSE {data.methods.best_raw.mse.toExponential(2)},
				greedy pairwise swap polish converges to the exact solution
				in {data.polish_trace.filter(t => t.mse > 1e-10).length - 1} improving iterations.
				Each order of magnitude in MSE reduction corresponds to correcting
				a few more block positions.
			</p>

			{#if polishOptions}
				<div style="width: 100%; height: 260px;">
					<Chart {init} options={polishOptions} theme="dark" />
				</div>
			{/if}
		</div>

	</div>
{/if}
