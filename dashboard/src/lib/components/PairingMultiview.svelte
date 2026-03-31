<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	type Component = { name: string; label: string; accuracy: number };
	type StabilityTrial = { subset_size: number; trials: number[] };

	type FusionData = {
		fused_accuracy: number;
		verification_mse: number;
		components: Component[];
		stability: StabilityTrial[];
		elapsed_s: number;
	};

	const COMPONENT_DESC: Record<string, string> = {
		effective_rank: 'Shannon entropy of singular values of W_out W_inp \u2014 how concentrated vs spread the spectrum is',
		geodesic: 'Principal angle distance between inp column space and out row space on the Grassmannian',
		single_block_mse: 'Prediction loss when evaluating inp\u2192hidden\u2192out\u2192readout on actual data',
	};

	let data: FusionData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_05_multiview_fusion.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	let barOptions = $derived.by(() => {
		if (!data) return null;
		const items = [
			...data.components.map(c => ({ label: c.label, value: c.accuracy, fused: false })),
			{ label: 'Fused (equal weight)', value: data.fused_accuracy, fused: true },
		];
		return {
			tooltip: {
				trigger: 'axis' as const,
				axisPointer: { type: 'shadow' as const },
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number }[])[0];
					const item = items[p.dataIndex];
					return `<strong style="color:#eceff4">${item.label}</strong>`
						+ `<br/><strong style="color:${item.fused ? '#3dd68c' : '#6cb6ff'}">${item.value}/48</strong> correct pairs`;
				},
			},
			grid: { top: 8, right: 60, bottom: 24, left: 160 },
			xAxis: {
				type: 'value' as const,
				min: 0, max: 50,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			yAxis: {
				type: 'category' as const,
				data: items.map(i => i.label),
				axisLabel: { color: '#b0b8c8', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			series: [{
				type: 'bar' as const,
				data: items.map(i => ({
					value: i.value,
					itemStyle: {
						color: i.fused ? '#3dd68c' : '#6cb6ff',
						opacity: i.fused ? 1.0 : 0.7,
					},
				})),
				barMaxWidth: 20,
				label: {
					show: true,
					position: 'right' as const,
					color: '#eceff4',
					fontSize: 12,
					fontFamily: 'JetBrains Mono, monospace',
					formatter: (p: unknown) => `${(p as { value: number }).value}/48`,
				},
				markLine: {
					silent: true,
					symbol: 'none' as const,
					lineStyle: { type: 'dashed' as const, color: '#3dd68c', width: 1, opacity: 0.5 },
					data: [{ xAxis: 48, label: { show: false } }],
				},
			}],
			backgroundColor: 'transparent',
		};
	});
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python pairing/05_multiview_fusion.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Three weak signals, one exact answer</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Weighted combination of three individually weaker signals:
				<strong class="text-text-primary">effective rank</strong> of
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">W_out W_inp</code>
				(Shannon entropy of the singular value distribution),
				<strong class="text-text-primary">geodesic distance</strong> between
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">inp</code> column space and
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">out</code> row space
				(principal angles on the Grassmannian),
				and <strong class="text-text-primary">single-block MSE</strong> evaluated on the data
				(prediction loss through one inp&rarr;hidden&rarr;out&rarr;readout path).
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				None of the three is exact on its own ({data.components.map(c => c.accuracy).join(', ')} out of 48),
				but their errors are complementary. Under equal-weight fusion with robust (median/MAD) normalization,
				Hungarian assignment recovers all
				<span class="font-mono font-semibold text-accent-green">{data.fused_accuracy}/48</span> pairs &mdash;
				demonstrating that medium-strength signals from different domains can combine into solver-grade accuracy.
			</p>
		</div>

		<!-- ── 2. COMPONENTS + FUSION CHART ────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Component accuracy alone vs fused</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each signal produces a 48&times;48 cost matrix. Each matrix is normalized
				(center by median, scale by MAD so heterogeneous scales become comparable),
				then the three are summed element-wise. Hungarian assignment on the summed matrix
				finds the optimal 1:1 pairing. No tuning &mdash; equal weights, one addition, one assignment.
			</p>

			<div class="grid grid-cols-[1fr_auto] gap-5">
				{#if barOptions}
					<div style="width: 640px; height: 200px;">
						<Chart {init} options={barOptions} theme="dark" />
					</div>
				{/if}

				<div class="flex flex-col gap-3 self-start">
					{#each data.components as c}
						<div class="rounded-lg border border-border-subtle px-4 py-2">
							<div class="flex items-baseline justify-between gap-4">
								<span class="text-sm font-medium text-text-primary">{c.label}</span>
								<span class="font-mono text-sm text-accent-blue">{c.accuracy}/48</span>
							</div>
							<p class="mt-0.5 text-sm text-text-secondary">{COMPONENT_DESC[c.name] ?? ''}</p>
						</div>
					{/each}
				</div>
			</div>
		</div>

		<!-- ── 3. STABILITY ────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Stable down to small data subsets</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				The single-block MSE component requires data, so fusion accuracy could degrade with fewer rows.
				Testing across random subsets (5 trials each) shows the signal is robust:
			</p>
			<div class="grid grid-cols-3 gap-4">
				{#each data.stability as s}
					{@const allExact = s.trials.every(t => t === 48)}
					{@const minVal = Math.min(...s.trials)}
					<div class="rounded-lg {allExact ? 'bg-accent-green/8 border border-accent-green/20' : 'border border-border-subtle'} px-4 py-3 text-center">
						<div class="font-mono text-3xl font-bold {allExact ? 'text-accent-green' : 'text-text-primary'}">
							{minVal === 48 ? '48/48' : `${minVal}\u2013${Math.max(...s.trials)}/48`}
						</div>
						<div class="mt-1 text-sm text-text-tertiary">{s.subset_size.toLocaleString()} rows &times; 5 trials</div>
						<div class="mt-2 flex justify-center gap-1">
							{#each s.trials as trial}
								<span class="inline-block rounded px-1.5 py-0.5 font-mono text-xs {trial === 48 ? 'bg-accent-green/15 text-accent-green' : 'bg-accent-amber/15 text-accent-amber'}">{trial}</span>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- ── 4. WHY FUSION WORKS ─────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Why complementary errors enable exact fusion</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Each 48&times;48 cost matrix has the correct pair as a strong entry in its row/column,
				but also has false positives &mdash; incorrect pairs that score nearly as well.
				Because the three signals measure different things (spectral structure, subspace geometry,
				prediction loss), their false positives land in different cells. Summing the matrices
				reinforces the true diagonal while the false positives, scattered across different locations,
				average down. The result: every correct pair becomes the unique minimum in its row and column.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				This is the only method that achieves 48/48 without any individually exact feature &mdash;
				pure complementarity of medium-strength signals.
			</p>
		</div>

		<!-- ── 5. VERIFICATION ─────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<div class="grid grid-cols-2 gap-4">
				<div class="rounded-lg bg-bg-inset px-4 py-3 text-center">
					<div class="font-mono text-3xl font-bold text-accent-green glow-green">{data.fused_accuracy}/48</div>
					<div class="mt-1 text-xs text-text-tertiary">fused pairing accuracy</div>
				</div>
				<div class="rounded-lg bg-bg-inset px-4 py-3 text-center">
					<div class="font-mono text-3xl font-bold text-accent-green glow-green">{data.verification_mse.toExponential(2)}</div>
					<div class="mt-1 text-xs text-text-tertiary">verification MSE (GT ordering)</div>
				</div>
			</div>
		</div>
	</div>
{/if}
