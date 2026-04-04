<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { LineChart, BarChart } from 'echarts/charts';
	import { init, use } from 'echarts/core';
	import {
		TooltipComponent,
		GridComponent,
		LegendComponent,
	} from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';

	use([LineChart, BarChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

	interface ShockCurve {
		name: string;
		kind: string;
		damping_ratio: number;
		mean_abs_pred_shift: number;
		peak_step: number;
		response_norms: number[];
	}

	interface GroupSummary {
		count: number;
		mean_damping_ratio: number;
		mean_abs_pred_shift: number;
		mean_peak_step: number;
	}

	interface RegimeResult {
		top_bottom_ratio: number;
		top_damping: number;
		bot_damping: number;
		top_pred_shift: number;
		bot_pred_shift: number;
	}

	interface ShockData {
		group_summary: Record<string, GroupSummary>;
		top_bottom_ratio: number;
		shock_curves: ShockCurve[];
		regime_stability: Record<string, RegimeResult>;
		elapsed_s: number;
	}

	let data: ShockData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const res = await fetch('/data/distillation_02_shock_response.json');
		if (res.ok) data = await res.json();
		loaded = true;
	}
	loadAll();

	const COLORS = {
		top: '#f0883e',
		bottom: '#6cb6ff',
		feature: '#3dd68c',
		textDim: '#8690a2',
		border: '#363e4a',
	};

	const KIND_COLORS: Record<string, string> = {
		pca_top: COLORS.top,
		pca_bottom: COLORS.bottom,
		feature: COLORS.feature,
	};

	const KIND_LABELS: Record<string, string> = {
		pca_top: 'Top-PC (amplified)',
		pca_bottom: 'Bottom-PC (damped)',
		feature: 'Target-correlated features',
	};

	// Shock response curves chart — averaged by kind
	let curveChartOptions = $derived.by(() => {
		if (!data) return null;
		const steps = Array.from({ length: 49 }, (_, i) => i);
		const grouped: Record<string, number[][]> = {};
		for (const c of data.shock_curves) {
			if (!grouped[c.kind]) grouped[c.kind] = [];
			grouped[c.kind].push(c.response_norms);
		}
		const series = Object.entries(grouped).map(([kind, curves]) => {
			const avgNorms = steps.map((i) => {
				const vals = curves.map((c) => c[i]);
				return vals.reduce((a, b) => a + b, 0) / vals.length;
			});
			return {
				name: KIND_LABELS[kind] || kind,
				type: 'line' as const,
				data: avgNorms,
				lineStyle: { color: KIND_COLORS[kind] || '#888', width: 2.5 },
				itemStyle: { color: KIND_COLORS[kind] || '#888' },
				symbol: 'none',
			};
		});
		return {
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis' as const },
			legend: {
				data: series.map((s) => s.name),
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 60, right: 20, top: 40, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: steps,
				name: 'Block position',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim, fontSize: 10 },
			},
			yAxis: {
				type: 'value' as const,
				name: 'Response norm',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
			},
			series,
		};
	});

	// Regime stability bar chart
	let regimeChartOptions = $derived.by(() => {
		if (!data) return null;
		const regimeNames = Object.keys(data.regime_stability).sort();
		const labels = regimeNames.map((n) =>
			n
				.replace('abs_pred_', 'pred ')
				.replace('input_norm_', 'norm ')
				.replace('pc1_', 'PC1 '),
		);
		const ratios = regimeNames.map((n) => data!.regime_stability[n].top_bottom_ratio);
		return {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis' as const,
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const name = regimeNames[p.dataIndex];
					const r = data!.regime_stability[name];
					return (
						`<b>${name}</b><br/>` +
						`Top/bottom ratio: ${r.top_bottom_ratio}x<br/>` +
						`Top damping: ${r.top_damping}<br/>` +
						`Bottom damping: ${r.bot_damping}`
					);
				},
			},
			grid: { left: 80, right: 20, top: 10, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: labels,
				axisLabel: { color: COLORS.textDim, fontSize: 11, rotate: 25 },
			},
			yAxis: {
				type: 'value' as const,
				name: 'Top/bottom shift ratio',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
			},
			series: [
				{
					type: 'bar' as const,
					data: ratios.map((v) => ({
						value: v,
						itemStyle: { color: v > 20 ? COLORS.top : '#d2a8ff' },
					})),
					barWidth: '50%',
				},
			],
		};
	});
</script>

{#if !loaded}
	<div class="flex items-center justify-center py-20 text-text-tertiary">Loading...</div>
{:else if !data}
	<div class="flex items-center justify-center py-20 text-text-tertiary">
		No data found. Run <code>distillation/02_shock_response.py</code> first.
	</div>
{:else}
	<div class="fade-in-up space-y-6">
		<!-- Headline -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">
				Selective Amplification: Factor Signals vs. Noise
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The network does not treat all perturbations equally. Shocks along
				high-variance input directions (top PCs) are <strong>amplified</strong> through
				depth, while shocks along low-variance directions (bottom PCs) are
				<strong>damped immediately</strong>. The prediction-shift gap is
				<strong>{data.top_bottom_ratio}x</strong>: the network&rsquo;s output is {data.top_bottom_ratio} times
				more sensitive to factor-like perturbations than to noise.
			</p>
			<div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold" style="color: {COLORS.top}">
						{data.group_summary.pca_top.mean_damping_ratio.toFixed(2)}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Top-PC damping (amplifying)</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold" style="color: {COLORS.bottom}">
						{data.group_summary.pca_bottom.mean_damping_ratio.toFixed(2)}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Bottom-PC damping (suppressed)</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold text-phase-interpret">
						{data.top_bottom_ratio}x
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Prediction-shift gap</div>
				</div>
			</div>
		</div>

		<!-- Response curves -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Shock Response Through Depth</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Mean response norm at each block position after injecting calibrated shocks
				along 14 input directions (8 target-correlated features, 3 top PCs, 3 bottom PCs).
			</p>
			{#if curveChartOptions}
				<div class="h-80">
					<Chart {init} options={curveChartOptions} />
				</div>
			{/if}
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				<span style="color: {COLORS.top}">Top-PC shocks</span> grow through the network,
				peaking at the final blocks (mean peak step {data.group_summary.pca_top.mean_peak_step.toFixed(0)}).
				<span style="color: {COLORS.bottom}">Bottom-PC shocks</span> peak at the input (step 0)
				and decay. <span style="color: {COLORS.feature}">Feature shocks</span> are intermediate &mdash;
				amplified but less than top PCs.
			</p>
		</div>

		<!-- Damping summary table -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Shock Group Summary</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Damping ratio &gt; 1 means the shock is amplified; &lt; 1 means it is damped.
			</p>
			<div class="overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Kind</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Count</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Damping</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Pred shift</th>
							<th class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Peak step</th>
						</tr>
					</thead>
					<tbody>
						{#each Object.entries(data.group_summary).sort() as [kind, s], i}
							<tr class="border-b border-border-subtle/50 {i % 2 === 0 ? 'bg-bg-inset/30' : ''}">
								<td class="py-3 pr-4 text-sm font-medium" style="color: {KIND_COLORS[kind] || '#ccc'}">
									{KIND_LABELS[kind] || kind}
								</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{s.count}</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{s.mean_damping_ratio.toFixed(4)}</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{s.mean_abs_pred_shift.toFixed(6)}</td>
								<td class="py-3 text-right font-mono text-sm text-text-secondary">{s.mean_peak_step.toFixed(1)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Regime stability -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Regime Stability</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The selective amplification pattern holds across all data subsets: low/high
				prediction magnitude, low/high input norm, low/high PC1 score. The top/bottom
				prediction-shift ratio stays between {Math.min(...Object.values(data.regime_stability).map((r) => r.top_bottom_ratio))}x
				and {Math.max(...Object.values(data.regime_stability).map((r) => r.top_bottom_ratio))}x.
			</p>
			{#if regimeChartOptions}
				<div class="h-64">
					<Chart {init} options={regimeChartOptions} />
				</div>
			{/if}
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Top-PC shocks remain amplifying (damping ratio
				{Math.min(...Object.values(data.regime_stability).map((r) => r.top_damping))}&ndash;{Math.max(...Object.values(data.regime_stability).map((r) => r.top_damping))})
				and bottom-PC shocks remain damped (ratio
				{Math.min(...Object.values(data.regime_stability).map((r) => r.bot_damping))}&ndash;{Math.max(...Object.values(data.regime_stability).map((r) => r.bot_damping))})
				in every regime. The separation is not a data-average artifact.
			</p>
		</div>
	</div>
{/if}
