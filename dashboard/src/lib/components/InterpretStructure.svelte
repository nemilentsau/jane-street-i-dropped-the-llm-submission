<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart } from 'echarts/charts';
	import { init, use } from 'echarts/core';
	import {
		TooltipComponent,
		GridComponent,
		LegendComponent,
		MarkLineComponent,
	} from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';

	use([
		BarChart,
		LineChart,
		TooltipComponent,
		GridComponent,
		LegendComponent,
		MarkLineComponent,
		CanvasRenderer,
	]);

	interface StructureData {
		sym_antisym: { sym_ratios: number[]; diffusion_pct: number };
		traces: { values: number[]; all_negative: boolean; range: [number, number] };
		mean_reverting: { frac_negative_per_block: number[]; mean_frac_negative: number };
		cumulative_drift: {
			spectral_radius: number[];
			effective_rank: number[];
			condition_number: number[];
		};
		factor_structure: {
			effective_rank: number;
			explained: Record<string, number>;
			singular_values: number[];
		};
		phase_structure: {
			deltas: number[];
			phase_means: Record<string, number>;
			late_early_ratio: number;
			max_delta_position: number;
		};
		feature_sensitivity: Record<string, { mean_var: number; top5_features: number[] }>;
		feature_sensitivity_ratio: number;
		feature_overlap: number;
		trajectory_pca: { pc1: number; pc1_2: number; pc1_3: number };
		elapsed_s: number;
	}

	let data: StructureData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const res = await fetch('/data/distillation_01_network_structure.json');
		if (res.ok) data = await res.json();
		loaded = true;
	}
	loadAll();

	const COLORS = {
		early: '#6cb6ff',
		mid: '#3dd68c',
		late: '#f0883e',
		accent: '#d2a8ff',
		text: '#eceff4',
		textDim: '#8690a2',
		border: '#363e4a',
	};

	// Phase delta bar chart
	let deltaChartOptions = $derived.by(() => {
		if (!data) return null;
		const deltas = data.phase_structure.deltas;
		const colors = deltas.map((_, i) => {
			if (i < 16) return COLORS.early;
			if (i < 32) return COLORS.mid;
			return COLORS.late;
		});
		return {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis' as const,
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					const phase = p.dataIndex < 16 ? 'Early' : p.dataIndex < 32 ? 'Mid' : 'Late';
					return `Position ${p.dataIndex}<br/>${phase}: ||delta|| = ${p.value.toFixed(4)}`;
				},
			},
			grid: { left: 60, right: 20, top: 10, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: deltas.map((_, i) => i),
				axisLabel: { color: COLORS.textDim, fontSize: 10 },
			},
			yAxis: {
				type: 'value' as const,
				name: '||delta||',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
			},
			series: [
				{
					type: 'bar' as const,
					data: deltas.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
					barWidth: '70%',
				},
			],
		};
	});

	// Cumulative drift chart (spectral radius + effective rank)
	let driftChartOptions = $derived.by(() => {
		if (!data) return null;
		const steps = Array.from({ length: 48 }, (_, i) => i);
		return {
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis' as const },
			legend: {
				data: ['Spectral Radius', 'Effective Rank'],
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 60, right: 60, top: 40, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: steps,
				name: 'Block position',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim, fontSize: 10 },
			},
			yAxis: [
				{
					type: 'value' as const,
					name: 'Spectral radius',
					nameTextStyle: { color: COLORS.early },
					axisLabel: { color: COLORS.textDim },
					splitLine: { lineStyle: { color: COLORS.border } },
				},
				{
					type: 'value' as const,
					name: 'Effective rank',
					nameTextStyle: { color: COLORS.accent },
					axisLabel: { color: COLORS.textDim },
					splitLine: { show: false },
				},
			],
			series: [
				{
					name: 'Spectral Radius',
					type: 'line' as const,
					data: data.cumulative_drift.spectral_radius,
					lineStyle: { color: COLORS.early, width: 2 },
					itemStyle: { color: COLORS.early },
					symbol: 'none',
					yAxisIndex: 0,
					markLine: {
						data: [{ yAxis: 1.0, label: { formatter: 'rho = 1' } }],
						lineStyle: { color: '#f778ba', type: 'dashed' as const },
						silent: true,
					},
				},
				{
					name: 'Effective Rank',
					type: 'line' as const,
					data: data.cumulative_drift.effective_rank,
					lineStyle: { color: COLORS.accent, width: 2 },
					itemStyle: { color: COLORS.accent },
					symbol: 'none',
					yAxisIndex: 1,
				},
			],
		};
	});

	// Factor structure scree plot
	let screeChartOptions = $derived.by(() => {
		if (!data) return null;
		const svs = data.factor_structure.singular_values.slice(0, 20);
		const total = data.factor_structure.singular_values.reduce(
			(s, v) => s + v * v,
			0,
		);
		let cumSum = 0;
		const cumExplained = svs.map((v) => {
			cumSum += v * v;
			return (cumSum / total) * 100;
		});
		return {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis' as const,
				formatter: (params: unknown) => {
					const items = params as { dataIndex: number; seriesName: string; value: number }[];
					let html = `<b>Factor ${items[0].dataIndex + 1}</b><br/>`;
					for (const it of items) {
						html += `${it.seriesName}: ${it.value.toFixed(2)}${it.seriesName.includes('%') ? '%' : ''}<br/>`;
					}
					return html;
				},
			},
			legend: {
				data: ['Singular Value', 'Cumulative %'],
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 60, right: 60, top: 40, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: svs.map((_, i) => i + 1),
				name: 'Factor',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
			},
			yAxis: [
				{
					type: 'value' as const,
					name: 'Singular value',
					nameTextStyle: { color: COLORS.early },
					axisLabel: { color: COLORS.textDim },
					splitLine: { lineStyle: { color: COLORS.border } },
				},
				{
					type: 'value' as const,
					name: 'Cumulative %',
					nameTextStyle: { color: COLORS.late },
					axisLabel: { color: COLORS.textDim },
					max: 100,
					splitLine: { show: false },
				},
			],
			series: [
				{
					name: 'Singular Value',
					type: 'bar' as const,
					data: svs,
					itemStyle: { color: COLORS.early },
					yAxisIndex: 0,
				},
				{
					name: 'Cumulative %',
					type: 'line' as const,
					data: cumExplained,
					lineStyle: { color: COLORS.late, width: 2 },
					itemStyle: { color: COLORS.late },
					symbol: 'circle',
					symbolSize: 4,
					yAxisIndex: 1,
				},
			],
		};
	});

	// Trace values bar chart
	let traceChartOptions = $derived.by(() => {
		if (!data) return null;
		return {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'axis' as const,
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number; value: number }[])[0];
					return `Block ${p.dataIndex}<br/>trace(A) = ${p.value.toFixed(3)}`;
				},
			},
			grid: { left: 60, right: 20, top: 10, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: data.traces.values.map((_, i) => i),
				axisLabel: { color: COLORS.textDim, fontSize: 10 },
			},
			yAxis: {
				type: 'value' as const,
				name: 'trace(A_k)',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
			},
			series: [
				{
					type: 'bar' as const,
					data: data.traces.values,
					itemStyle: { color: '#f778ba' },
					barWidth: '70%',
				},
			],
		};
	});
</script>

{#if !loaded}
	<div class="flex items-center justify-center py-20 text-text-tertiary">Loading...</div>
{:else if !data}
	<div class="flex items-center justify-center py-20 text-text-tertiary">
		No data found. Run <code>distillation/01_network_structure.py</code> first.
	</div>
{:else}
	<div class="fade-in-up space-y-6">
		<!-- Headline insight -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">
				A Stable, Factor-Compressing Residual Network
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The recovered network is a discretized ODE: each block applies a small update
				<code>x &rarr; x + f(x)</code>. Its linearized dynamics are
				<strong>{data.sym_antisym.diffusion_pct}%</strong> diffusive (contractive/expansive)
				and <strong>{(100 - data.sym_antisym.diffusion_pct).toFixed(0)}%</strong> rotational.
				All 48 blocks are locally contractive (negative trace), and ~{(data.mean_reverting.mean_frac_negative * 100).toFixed(0)}%
				of modes are mean-reverting. The cumulative operator compresses
				48 dimensions down to an effective rank of <strong>{data.factor_structure.effective_rank.toFixed(1)}</strong>.
			</p>
			<div class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
				<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
					<div class="text-2xl font-bold text-phase-interpret">
						{data.sym_antisym.diffusion_pct}%
					</div>
					<div class="mt-1 text-xs text-text-tertiary">Diffusion</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
					<div class="text-2xl font-bold text-accent-green">48/48</div>
					<div class="mt-1 text-xs text-text-tertiary">Contractive blocks</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
					<div class="text-2xl font-bold text-[#6cb6ff]">
						{data.cumulative_drift.spectral_radius[data.cumulative_drift.spectral_radius.length - 1].toFixed(2)}
					</div>
					<div class="mt-1 text-xs text-text-tertiary">Final spectral radius</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
					<div class="text-2xl font-bold text-[#d2a8ff]">
						{data.factor_structure.effective_rank.toFixed(1)}
					</div>
					<div class="mt-1 text-xs text-text-tertiary">Final effective rank</div>
				</div>
			</div>
		</div>

		<!-- Trace values -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Volume Contraction</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Every block has negative Jacobian trace (range [{data.traces.range[0].toFixed(2)}, {data.traces.range[1].toFixed(2)}]),
				meaning each block shrinks phase-space volume. No block is expansive.
			</p>
			{#if traceChartOptions}
				<div class="h-48">
					<Chart {init} options={traceChartOptions} />
				</div>
			{/if}
		</div>

		<!-- Cumulative drift -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Cumulative Drift</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Spectral radius starts mildly expansive (~1.05), then falls below 1.0 &mdash;
				the network is globally stable. Effective rank drops from ~47 to ~{data.factor_structure.effective_rank.toFixed(0)}:
				the state is compressed onto a narrow factor subspace.
			</p>
			{#if driftChartOptions}
				<div class="h-72">
					<Chart {init} options={driftChartOptions} />
				</div>
			{/if}
		</div>

		<!-- Factor structure scree plot -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Factor Structure</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				SVD of the final cumulative operator. Top-5 factors explain
				<strong>{data.factor_structure.explained.top_5.toFixed(1)}%</strong> of variance.
				The network compresses 48 input dimensions into ~5 active factors.
			</p>
			{#if screeChartOptions}
				<div class="h-72">
					<Chart {init} options={screeChartOptions} />
				</div>
			{/if}
		</div>

		<!-- Phase structure -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Phase Structure</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The computation has three phases: early blocks stabilize (mean delta {data.phase_structure.phase_means.early.toFixed(2)}),
				middle blocks are quietest ({data.phase_structure.phase_means.mid.toFixed(2)}),
				late blocks make sharp corrections ({data.phase_structure.phase_means.late.toFixed(2)}).
				Late/early ratio: <strong>{data.phase_structure.late_early_ratio.toFixed(1)}x</strong>.
			</p>
			{#if deltaChartOptions}
				<div class="h-64">
					<Chart {init} options={deltaChartOptions} />
				</div>
			{/if}
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				<span style="color: {COLORS.early}">Blue</span> = early (0&ndash;15),
				<span style="color: {COLORS.mid}">green</span> = mid (16&ndash;31),
				<span style="color: {COLORS.late}">orange</span> = late (32&ndash;47).
				The largest single perturbation ({data.phase_structure.deltas[data.phase_structure.max_delta_position].toFixed(2)})
				occurs at the final position.
			</p>
		</div>

		<!-- Feature sensitivity -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Feature Sensitivity by Phase</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Early and late blocks modify different features entirely.
			</p>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				{#each ['early', 'mid', 'late'] as phase}
					{@const info = data.feature_sensitivity[phase]}
					{@const color = phase === 'early' ? COLORS.early : phase === 'mid' ? COLORS.mid : COLORS.late}
					<div class="rounded-lg border border-border-subtle px-5 py-4">
						<h4 class="mb-2 text-base font-semibold" style="color: {color}">
							{phase.charAt(0).toUpperCase() + phase.slice(1)}
						</h4>
						<div class="mb-1 font-mono text-sm text-text-secondary">
							mean variance: {info.mean_var.toFixed(6)}
						</div>
						<div class="font-mono text-sm text-text-tertiary">
							top features: [{info.top5_features.join(', ')}]
						</div>
					</div>
				{/each}
			</div>
			<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
				Late blocks have <strong>{data.feature_sensitivity_ratio.toFixed(1)}x</strong> more
				per-feature variance than middle blocks. The top-5 most-affected features are
				{#if data.feature_overlap === 0}
					<strong>completely disjoint</strong> between early and late phases
				{:else}
					overlapping by {data.feature_overlap} features
				{/if}
				&mdash; the network processes different aspects of the input at different depths.
			</p>
		</div>

		<!-- Trajectory PCA -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Trajectory PCA</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The 48-step trajectory through 48-dimensional state space is effectively
				three-dimensional.
			</p>
			<div class="grid grid-cols-3 gap-4">
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-2xl font-bold text-phase-interpret">
						{data.trajectory_pca.pc1.toFixed(1)}%
					</div>
					<div class="mt-1 text-sm text-text-tertiary">PC1</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-2xl font-bold text-phase-interpret">
						{data.trajectory_pca.pc1_2.toFixed(1)}%
					</div>
					<div class="mt-1 text-sm text-text-tertiary">PC1&ndash;2</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-2xl font-bold text-phase-interpret">
						{data.trajectory_pca.pc1_3.toFixed(1)}%
					</div>
					<div class="mt-1 text-sm text-text-tertiary">PC1&ndash;3</div>
				</div>
			</div>
		</div>
	</div>
{/if}
