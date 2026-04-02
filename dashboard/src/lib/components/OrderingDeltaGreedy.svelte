<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, LineChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	type DGData = {
		raw: { correct_positions: number; total_positions: number; mse: number };
		polished: { correct_positions: number; total_positions: number; mse: number };
		deltas: number[];
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

	let deltaChartOptions = $derived.by(() => {
		if (!data) return null;
		const deltas = data.deltas;
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					return `<strong style="color:#eceff4">Position ${p.dataIndex + 1}</strong>`
						+ `<br/>Perturbation: <span style="color:#6cb6ff">${p.value.toFixed(4)}</span>`;
				},
			},
			grid: { top: 16, right: 24, bottom: 36, left: 56 },
			xAxis: {
				type: 'category' as const,
				data: deltas.map((_: number, i: number) => i + 1),
				axisLabel: { color: '#b0b8c8', fontSize: 11, interval: 7 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				name: 'Block position (greedy order)',
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
						color: i < 16 ? '#6cb6ff' : i < 32 ? '#8690a2' : '#f0883e',
						opacity: 0.8,
					},
				})),
				barMaxWidth: 12,
			}],
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
				Delta-greedy treats residual blocks as discrete ODE time steps.
				At each step it passes the full dataset (10,000 rows) through every remaining block
				and picks the one with smallest perturbation
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">||block(x) &minus; x||</code>.
				The selected block is applied, updating the running state, and the process repeats.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The assumption: in a well-trained residual network
				(<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">x &larr; x + f(x)</code>),
				early blocks make small corrections and late blocks make larger ones.
				Delta-greedy recovers this ordering directly from the data,
				constructing the smoothest possible trajectory through the 48-step sequence.
				It reaches {data.raw.correct_positions}/{data.raw.total_positions} raw positions &mdash;
				the strongest raw ordering of any method tested. The remaining errors
				are local transpositions between adjacent blocks with similar perturbation sizes,
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
				MSE polish tries every pairwise swap of block positions and keeps those that reduce MSE.
				Starting from 77/97, it converges to 97/97 in a single iteration &mdash;
				only a handful of swaps separate the greedy solution from the exact answer.
			</p>
		</div>

		<!-- ── 3. PERTURBATION TRAJECTORY ──────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Perturbation trajectory along greedy order</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each bar shows <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">||block(x) &minus; x||</code>
				at the moment the block is selected. The trajectory is U-shaped:
				the first block selected has a large perturbation ({data.deltas[0].toFixed(2)}),
				the middle blocks settle into a flat plateau (~0.4),
				then late blocks rise sharply to the final block&rsquo;s {data.deltas[data.deltas.length - 1].toFixed(2)}.
				The greedy algorithm picks the globally smallest perturbation first, not the earliest &mdash;
				block 1 is simply the least disruptive starting point for the initial state.
			</p>

			{#if deltaChartOptions}
				<div style="width: 100%; height: 280px;">
					<Chart {init} options={deltaChartOptions} theme="dark" />
				</div>
			{/if}

			<div class="mt-3 flex gap-6 text-xs text-text-tertiary">
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#6cb6ff"></span> Early (1&ndash;16)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#8690a2"></span> Middle (17&ndash;32)</span>
				<span><span class="mr-1 inline-block h-2.5 w-2.5 rounded-sm" style="background:#f0883e"></span> Late (33&ndash;48)</span>
			</div>
		</div>

	</div>
{/if}
