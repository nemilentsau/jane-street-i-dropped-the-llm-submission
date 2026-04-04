<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart, LineChart } from 'echarts/charts';
	import { init, use } from 'echarts/core';
	import {
		TooltipComponent,
		GridComponent,
		LegendComponent,
	} from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';

	use([BarChart, LineChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

	interface RankResult {
		rank: number;
		model: string;
		track_state_mse: number;
		final_prediction_mse: number;
		spectral_radius: number;
	}

	interface ShockRow {
		name: string;
		kind: string;
		gt_damping: number;
		gt_pred_shift: number;
		auto_damping_gap: number;
		auto_pred_shift_gap: number;
		obs_damping_gap: number;
		obs_pred_shift_gap: number;
	}

	interface ObserverData {
		rank_results: RankResult[];
		best_rank: number;
		best_auto_pred_mse: number;
		best_obs_pred_mse: number;
		best_auto_track_mse: number;
		best_obs_track_mse: number;
		shock_fidelity: {
			auto_mean_damping_gap: number;
			obs_mean_damping_gap: number;
			auto_mean_pred_shift_gap: number;
			obs_mean_pred_shift_gap: number;
			damping_improvement_pct: number;
		};
		shock_rows: ShockRow[];
		elapsed_s: number;
	}

	let data: ObserverData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const res = await fetch('/data/distillation_03_latent_observer.json');
		if (res.ok) data = await res.json();
		loaded = true;
	}
	loadAll();

	const COLORS = {
		auto: '#f0883e',
		obs: '#6cb6ff',
		accent: '#d2a8ff',
		green: '#3dd68c',
		textDim: '#8690a2',
		border: '#363e4a',
	};

	// Prediction MSE by rank — grouped bar chart
	let predMseChartOptions = $derived.by(() => {
		if (!data) return null;
		const ranks = [...new Set(data.rank_results.map((r) => r.rank))];
		const autoMse = ranks.map(
			(rank) => data!.rank_results.find((r) => r.rank === rank && r.model === 'autonomous')!.final_prediction_mse,
		);
		const obsMse = ranks.map(
			(rank) => data!.rank_results.find((r) => r.rank === rank && r.model === 'observer')!.final_prediction_mse,
		);
		return {
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis' as const },
			legend: {
				data: ['Autonomous', 'Observer'],
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 60, right: 20, top: 40, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: ranks.map((r) => `Rank ${r}`),
				axisLabel: { color: COLORS.textDim },
			},
			yAxis: {
				type: 'value' as const,
				name: 'Prediction MSE',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
				min: (v: { min: number }) => Math.floor(v.min * 100) / 100,
			},
			series: [
				{
					name: 'Autonomous',
					type: 'bar' as const,
					data: autoMse,
					itemStyle: { color: COLORS.auto },
					barGap: '10%',
				},
				{
					name: 'Observer',
					type: 'bar' as const,
					data: obsMse,
					itemStyle: { color: COLORS.obs },
				},
			],
		};
	});

	// Shock fidelity comparison — bar chart
	let shockChartOptions = $derived.by(() => {
		if (!data) return null;
		const sf = data.shock_fidelity;
		return {
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis' as const },
			legend: {
				data: ['Autonomous', 'Observer'],
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 80, right: 20, top: 40, bottom: 30 },
			xAxis: {
				type: 'category' as const,
				data: ['Damping gap', 'Pred-shift gap'],
				axisLabel: { color: COLORS.textDim, fontSize: 12 },
			},
			yAxis: {
				type: 'value' as const,
				name: 'Mean absolute gap vs GT',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
			},
			series: [
				{
					name: 'Autonomous',
					type: 'bar' as const,
					data: [sf.auto_mean_damping_gap, sf.auto_mean_pred_shift_gap],
					itemStyle: { color: COLORS.auto },
					barGap: '10%',
				},
				{
					name: 'Observer',
					type: 'bar' as const,
					data: [sf.obs_mean_damping_gap, sf.obs_mean_pred_shift_gap],
					itemStyle: { color: COLORS.obs },
				},
			],
		};
	});

	// Per-direction shock fidelity
	let directionChartOptions = $derived.by(() => {
		if (!data) return null;
		const rows = data.shock_rows;
		const names = rows.map((r) => r.name.replace('pca_top_', 'Top ').replace('pca_bottom_', 'Bot ').replace('noise_', 'Noise '));
		return {
			backgroundColor: 'transparent',
			tooltip: { trigger: 'axis' as const },
			legend: {
				data: ['Autonomous', 'Observer'],
				textStyle: { color: COLORS.textDim },
				top: 0,
			},
			grid: { left: 80, right: 20, top: 40, bottom: 40 },
			xAxis: {
				type: 'category' as const,
				data: names,
				axisLabel: { color: COLORS.textDim, fontSize: 10, rotate: 25 },
			},
			yAxis: {
				type: 'value' as const,
				name: 'Damping gap vs GT',
				nameTextStyle: { color: COLORS.textDim },
				axisLabel: { color: COLORS.textDim },
				splitLine: { lineStyle: { color: COLORS.border } },
			},
			series: [
				{
					name: 'Autonomous',
					type: 'bar' as const,
					data: rows.map((r) => r.auto_damping_gap),
					itemStyle: { color: COLORS.auto },
					barGap: '10%',
				},
				{
					name: 'Observer',
					type: 'bar' as const,
					data: rows.map((r) => r.obs_damping_gap),
					itemStyle: { color: COLORS.obs },
				},
			],
		};
	});
</script>

{#if !loaded}
	<div class="flex items-center justify-center py-20 text-text-tertiary">Loading...</div>
{:else if !data}
	<div class="flex items-center justify-center py-20 text-text-tertiary">
		No data found. Run <code>distillation/03_latent_observer.py</code> first.
	</div>
{:else}
	<div class="fade-in-up space-y-6">
		<!-- Headline -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">
				What kind of dynamical system is this network?
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The previous sections established <em>what</em> the network does &mdash; contractive
				Jacobians, phase structure, selective shock amplification. This section asks a
				different question: <strong>what is the simplest dynamical system that reproduces
				this behavior?</strong> If a compact surrogate can match the network&rsquo;s outputs
				and perturbation responses, it serves as an interpretable summary of the
				network&rsquo;s computational strategy.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Two surrogate models were fitted. Both project the 48-D hidden trajectory into a
				low-rank PCA basis and fit linear transition rules via least-squares.
				The <strong>autonomous</strong> surrogate evolves purely in latent space:
				<code class="text-xs">z&#x2081; = a + z&#x2080;F</code> &mdash; a self-contained
				linear dynamical system. The <strong>observer</strong>
				adds a correction from the full-dimensional residual:
				<code class="text-xs">z&#x2081; = a + z&#x2080;F + r&#x2080;C</code>,
				where <code class="text-xs">r</code> is the gap between the true state and its
				low-rank projection. This is the classic observer/Kalman-filter structure:
				a latent model that <em>corrects itself</em> using information it cannot
				represent internally.
			</p>
			<div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold" style="color: {COLORS.auto}">
						{data.best_auto_pred_mse.toFixed(4)}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Autonomous pred MSE</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold" style="color: {COLORS.obs}">
						{data.best_obs_pred_mse.toFixed(4)}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Observer pred MSE</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold text-phase-interpret">
						{data.shock_fidelity.damping_improvement_pct}%
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Shock fidelity improvement</div>
				</div>
			</div>
		</div>

		<!-- Prediction MSE by rank -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Test 1: Prediction Accuracy</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The first test: can the surrogate reproduce the real network&rsquo;s final
				predictions? Each surrogate is teacher-forced through 48 steps (receiving the
				true state at each step) and its decoded final state is passed through the
				readout layer. The chart shows final prediction MSE on a held-out 20% test set
				at three latent ranks (5, 7, 9). The observer wins at every rank.
			</p>
			{#if predMseChartOptions}
				<div class="h-72">
					<Chart {init} options={predMseChartOptions} />
				</div>
			{/if}
		</div>

		<!-- Rank results table -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Full Metric Breakdown</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				<strong>Track MSE</strong> measures how closely the surrogate&rsquo;s decoded
				states match the true 48-D trajectory at every step.
				<strong>Prediction MSE</strong> measures final output accuracy after the readout
				layer. These two metrics can diverge: the observer sometimes reconstructs
				the trajectory <em>less</em> faithfully in a least-squares sense, yet produces
				<em>better</em> predictions &mdash; because the residual correction steers the
				latent state toward the subspace that matters for the output.
			</p>
			<div class="overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Rank</th>
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Model</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Track MSE</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Pred MSE</th>
							<th class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Spectral radius</th>
						</tr>
					</thead>
					<tbody>
						{#each data.rank_results as r, i}
							<tr class="border-b border-border-subtle/50 {i % 2 === 0 ? 'bg-bg-inset/30' : ''}">
								<td class="py-3 pr-4 font-mono text-sm text-text-secondary">{r.rank}</td>
								<td class="py-3 pr-4 text-sm font-medium" style="color: {r.model === 'observer' ? COLORS.obs : COLORS.auto}">
									{r.model}
								</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{r.track_state_mse.toFixed(6)}</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{r.final_prediction_mse.toFixed(6)}</td>
								<td class="py-3 text-right font-mono text-sm text-text-secondary">{r.spectral_radius.toFixed(4)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Shock fidelity -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Test 2: Shock-Response Fidelity</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The second &mdash; and harder &mdash; test: can the surrogate reproduce how
				the real network <em>responds to perturbations</em>? Section 02 showed the
				network selectively amplifies top-PC shocks and damps bottom-PC shocks.
				A good surrogate must reproduce this selective behavior, not just match
				average outputs. Calibrated shocks are injected along 6 directions (3 top-PC,
				3 bottom-PC), and the surrogate&rsquo;s damping ratio and prediction shift
				are compared against the real network. <strong>Damping gap</strong> =
				|surrogate damping &minus; GT damping|; <strong>pred-shift gap</strong> =
				|surrogate shift &minus; GT shift|. Lower is better.
			</p>
			{#if shockChartOptions}
				<div class="h-64">
					<Chart {init} options={shockChartOptions} />
				</div>
			{/if}
			<div class="mt-4 overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Metric</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary" style="color: {COLORS.auto}">Autonomous</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary" style="color: {COLORS.obs}">Observer</th>
							<th class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">Improvement</th>
						</tr>
					</thead>
					<tbody>
						<tr class="border-b border-border-subtle/50 bg-bg-inset/30">
							<td class="py-3 pr-4 text-sm text-text-secondary">Damping gap</td>
							<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{data.shock_fidelity.auto_mean_damping_gap.toFixed(4)}</td>
							<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{data.shock_fidelity.obs_mean_damping_gap.toFixed(4)}</td>
							<td class="py-3 text-right font-mono text-sm" style="color: {COLORS.green}">{data.shock_fidelity.damping_improvement_pct}%</td>
						</tr>
						<tr>
							<td class="py-3 pr-4 text-sm text-text-secondary">Pred-shift gap</td>
							<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{data.shock_fidelity.auto_mean_pred_shift_gap.toFixed(6)}</td>
							<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{data.shock_fidelity.obs_mean_pred_shift_gap.toFixed(6)}</td>
							<td class="py-3 text-right font-mono text-sm" style="color: {COLORS.green}">{((1 - data.shock_fidelity.obs_mean_pred_shift_gap / data.shock_fidelity.auto_mean_pred_shift_gap) * 100).toFixed(1)}%</td>
						</tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- Per-direction breakdown -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">Per-Direction Breakdown</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				The aggregate improvement is not driven by a single outlier direction.
				The table below shows the damping gap for each of the 6 shock directions
				individually. The observer is closer to ground truth on <em>every</em>
				direction &mdash; top PCs (where the real network amplifies) and bottom PCs
				(where it damps). The observer&rsquo;s residual correction captures the
				selective amplification pattern that the autonomous model misses.
			</p>
			{#if directionChartOptions}
				<div class="h-64">
					<Chart {init} options={directionChartOptions} />
				</div>
			{/if}
			<div class="mt-4 overflow-x-auto">
				<table class="w-full text-left text-[15px]">
					<thead>
						<tr class="border-b border-border-subtle">
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Direction</th>
							<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Kind</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary">GT damping</th>
							<th class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary" style="color: {COLORS.auto}">Auto gap</th>
							<th class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary" style="color: {COLORS.obs}">Obs gap</th>
						</tr>
					</thead>
					<tbody>
						{#each data.shock_rows as row, i}
							<tr class="border-b border-border-subtle/50 {i % 2 === 0 ? 'bg-bg-inset/30' : ''}">
								<td class="py-3 pr-4 font-mono text-sm text-text-secondary">{row.name}</td>
								<td class="py-3 pr-4 text-sm text-text-secondary">{row.kind}</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{row.gt_damping.toFixed(4)}</td>
								<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">{row.auto_damping_gap.toFixed(4)}</td>
								<td class="py-3 text-right font-mono text-sm text-text-secondary">{row.obs_damping_gap.toFixed(4)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>

		<!-- Conclusion -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Putting It Together</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				An autonomous low-rank ODE can approximate the trajectory but fails to
				reproduce the network&rsquo;s <em>behavioral signature</em> &mdash; the
				selective amplification of factor-like directions that Section 02 identified.
				Adding a single correction term (the observer residual <code class="text-xs">r&#x2080;C</code>)
				closes {data.shock_fidelity.damping_improvement_pct}% of that gap. This
				correction allows information from the full 48-D state to flow into the
				latent model at every step, compensating for what the low-rank projection discards.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The implication: the best compact summary of this network is not &ldquo;a
				low-rank autonomous dynamical system.&rdquo; It is
				<strong>a low-rank stable factor system with observer-like correction from the
				current high-dimensional state</strong> &mdash; closer to a Kalman filter than
				to a standalone ODE. The network maintains a compact latent representation
				but continuously refines it using residual information that cannot be
				captured in any fixed low-rank basis.
			</p>
		</div>
	</div>
{/if}
