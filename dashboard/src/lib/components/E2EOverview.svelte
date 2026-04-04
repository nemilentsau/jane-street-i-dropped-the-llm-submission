<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { HeatmapChart } from 'echarts/charts';
	import { init, use } from 'echarts/core';
	import {
		TooltipComponent,
		GridComponent,
		VisualMapComponent,
	} from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';

	use([HeatmapChart, TooltipComponent, GridComponent, VisualMapComponent, CanvasRenderer]);

	interface PairingResult {
		id: string;
		name: string;
		accuracy: number;
		elapsed_s: number;
		needs_data: boolean;
	}

	interface OrderingResult {
		id: string;
		name: string;
		raw_positions: number;
		raw_mse: number;
		elapsed_s: number;
	}

	interface FastestPipeline {
		pairing_method: string;
		ordering_method: string;
		pairing_elapsed: number;
		ordering_elapsed: number;
		total_time: number;
	}

	interface GridRow {
		pairing_id: string;
		pairing_name: string;
		ordering_id: string;
		ordering_name: string;
		pairing_elapsed: number;
		ordering_elapsed: number;
		total_time: number;
	}

	interface E2EData {
		pairing_results: PairingResult[];
		ordering_results: OrderingResult[];
		all_canonical: boolean;
		fastest_pipeline: FastestPipeline;
		grid: GridRow[];
		caveat: string;
	}

	let data: E2EData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const res = await fetch('/data/e2e_overview.json');
		if (res.ok) data = await res.json();
		loaded = true;
	}
	loadAll();

	function fmtTime(s: number): string {
		if (s < 60) return `${s.toFixed(0)}s`;
		const m = Math.floor(s / 60);
		const sec = Math.round(s % 60);
		return `${m}m${sec.toString().padStart(2, '0')}s`;
	}

	function fmtTimeShort(s: number): string {
		if (s < 60) return `${s.toFixed(0)}s`;
		return `${(s / 60).toFixed(1)}m`;
	}

	let nPerfectPairing = $derived.by(() =>
		data ? data.pairing_results.filter((p) => p.accuracy === 48).length : 0,
	);
	let nOrdering = $derived.by(() => (data ? data.ordering_results.length : 0));
	let totalCombos = $derived(nPerfectPairing * nOrdering);
	let totalGrid = $derived.by(() => (data ? data.pairing_results.length * nOrdering : 0));

	const COLORS = {
		text: '#eceff4',
		textDim: '#8690a2',
	};

	let heatmapOptions = $derived.by(() => {
		if (!data) return null;
		const pNames = data.pairing_results.map((p) => p.name);
		const oNames = data.ordering_results.map((o) => o.name);
		const heatData: [number, number, number][] = [];
		let minTime = Infinity;
		let maxTime = 0;
		for (const row of data.grid) {
			const pi = data.pairing_results.findIndex((p) => p.id === row.pairing_id);
			const oi = data.ordering_results.findIndex((o) => o.id === row.ordering_id);
			heatData.push([pi, oi, row.total_time]);
			minTime = Math.min(minTime, row.total_time);
			maxTime = Math.max(maxTime, row.total_time);
		}
		return {
			backgroundColor: 'transparent',
			tooltip: {
				trigger: 'item' as const,
				formatter: (params: unknown) => {
					const p = params as { data: [number, number, number] };
					const pi = p.data[0];
					const oi = p.data[1];
					const row = data!.grid.find(
						(r) =>
							r.pairing_id === data!.pairing_results[pi].id &&
							r.ordering_id === data!.ordering_results[oi].id,
					);
					if (!row) return '';
					return (
						`<b>${row.pairing_name} + ${row.ordering_name}</b><br/>` +
						`Pairing script: ${fmtTime(row.pairing_elapsed)}<br/>` +
						`Ordering script: ${fmtTime(row.ordering_elapsed)}<br/>` +
						`<b>Sum: ~${fmtTime(row.total_time)}</b>`
					);
				},
			},
			grid: { left: 140, right: 60, top: 10, bottom: 60 },
			xAxis: {
				type: 'category' as const,
				data: pNames,
				axisLabel: { color: COLORS.textDim, fontSize: 11, rotate: 30 },
				splitArea: {
					show: true,
					areaStyle: { color: ['transparent', 'rgba(255,255,255,0.02)'] },
				},
			},
			yAxis: {
				type: 'category' as const,
				data: oNames,
				axisLabel: { color: COLORS.textDim, fontSize: 11 },
				splitArea: {
					show: true,
					areaStyle: { color: ['transparent', 'rgba(255,255,255,0.02)'] },
				},
			},
			visualMap: {
				min: minTime,
				max: maxTime,
				calculable: true,
				orient: 'vertical' as const,
				right: 0,
				top: 10,
				bottom: 60,
				inRange: {
					color: ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027'],
				},
				textStyle: { color: COLORS.textDim },
				formatter: (v: unknown) => fmtTimeShort(Number(v)),
			},
			series: [
				{
					type: 'heatmap' as const,
					data: heatData,
					label: {
						show: true,
						color: COLORS.text,
						fontSize: 11,
						fontWeight: 'bold' as const,
						formatter: (params: unknown) => {
							const p = params as { data: [number, number, number] };
							return fmtTimeShort(p.data[2]);
						},
					},
					emphasis: {
						itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' },
					},
				},
			],
		};
	});
</script>

{#if !loaded}
	<div class="flex items-center justify-center py-20 text-text-tertiary">Loading...</div>
{:else if !data}
	<div class="flex items-center justify-center py-20 text-text-tertiary">
		No data found. Run <code>e2e/01_overview.py</code> first.
	</div>
{:else}
	<div class="fade-in-up space-y-6">
		<!-- Headline -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">
				Every Path Leads to Exact Reconstruction
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				{#if data.all_canonical}
					All 5 pairing methods produce the same canonical pairing (48/48 correct).
				{:else}
					{nPerfectPairing} of 5 pairing methods produce the exact canonical pairing
					(48/48).
				{/if}
				All 5 ordering methods, after local polish, converge to the exact ground-truth piece permutation
				(97/97 correct, MSE = 3.16e-14). The ordering search itself runs over 48 paired blocks; the
				97/97 score shown here is after unpacking those blocks back into 48 <span class="font-mono">inp</span>
				pieces, 48 <span class="font-mono">out</span> pieces, and the final readout. The question
				isn't <em>which</em> method works &mdash; they all do &mdash; but <em>how fast</em> each
				pipeline reaches perfect.
			</p>
			<div class="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-phase-e2e/30 px-5 py-4 text-center">
					<div class="text-3xl font-bold text-phase-e2e">
						~{fmtTime(data.fastest_pipeline.total_time)}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">Fastest pipeline</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold text-accent-green">
						{data.fastest_pipeline.pairing_method}
					</div>
					<div class="mt-1 text-sm text-text-tertiary">
						+ {data.fastest_pipeline.ordering_method} + Polish
					</div>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4 text-center">
					<div class="text-3xl font-bold text-text-primary">{totalCombos} / {totalGrid}</div>
					<div class="mt-1 text-sm text-text-tertiary">
						Combos reaching exact ({nPerfectPairing} pairing &times; {nOrdering} ordering)
					</div>
				</div>
			</div>
		</div>

		<!-- Method summary tables side by side -->
		<div class="grid grid-cols-1 gap-6 md:grid-cols-2">
			<!-- Pairing methods -->
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Pairing Methods</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					All 5 solve the combinatorial pairing problem exactly.
				</p>
				<div class="overflow-x-auto">
					<table class="w-full text-left text-[15px]">
						<thead>
							<tr class="border-b border-border-subtle">
								<th
									class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Method</th
								>
								<th
									class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Accuracy</th
								>
								<th
									class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Script time</th
								>
							</tr>
						</thead>
						<tbody>
							{#each data.pairing_results as p, i}
								<tr
									class="border-b border-border-subtle/50 {i % 2 === 0
										? 'bg-bg-inset/30'
										: ''}"
								>
									<td class="py-3 pr-4 text-sm text-text-secondary">
										{p.id}. {p.name}
										{#if !p.needs_data}
											<span class="ml-1 text-xs text-text-tertiary"
												>(weights only)</span
											>
										{/if}
									</td>
									<td class="py-3 pr-4 text-right font-mono text-sm text-accent-green"
										>{p.accuracy}/48</td
									>
									<td class="py-3 text-right font-mono text-sm text-text-secondary"
										>{fmtTime(p.elapsed_s)}</td
									>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>

			<!-- Ordering methods -->
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Ordering Methods</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					All start rough, all polish to exact (97/97). Scores are on the unpacked 97-piece permutation,
					even though the search runs over 48 paired blocks. Times include polish.
				</p>
				<div class="overflow-x-auto">
					<table class="w-full text-left text-[15px]">
						<thead>
							<tr class="border-b border-border-subtle">
								<th
									class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Method</th
								>
								<th
									class="pb-3 pr-4 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Raw</th
								>
								<th
									class="pb-3 text-right text-xs font-semibold uppercase tracking-wider text-text-tertiary"
									>Script time</th
								>
							</tr>
						</thead>
						<tbody>
							{#each data.ordering_results as o, i}
								<tr
									class="border-b border-border-subtle/50 {i % 2 === 0
										? 'bg-bg-inset/30'
										: ''}"
								>
									<td class="py-3 pr-4 text-sm text-text-secondary">
										{o.id}. {o.name}
									</td>
									<td class="py-3 pr-4 text-right font-mono text-sm text-text-secondary">
										{o.raw_positions}/97
									</td>
									<td class="py-3 text-right font-mono text-sm text-text-secondary">
										{fmtTime(o.elapsed_s)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</div>
		</div>

		<!-- 5x5 timing heatmap -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-1 text-lg font-semibold text-text-primary">
				Pipeline Timing Grid (5 &times; 5)
			</h3>
			<p class="mb-4 text-sm text-text-tertiary">
				Estimated total time for each pairing &times; ordering combination (sum of
				individual script runtimes). All 25 reach exact reconstruction.
			</p>
			{#if heatmapOptions}
				<div class="h-80">
					<Chart {init} options={heatmapOptions} />
				</div>
			{/if}
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The fastest cell is <strong>Weight Correlation + Delta Greedy</strong> (~{fmtTime(data.fastest_pipeline.total_time)}).
				Weight Correlation needs only the weight matrices (no data), and Delta Greedy
				starts close enough that polish finishes quickly. The slowest cells combine
				exploration-heavy pairing methods with ordering methods that need many polish
				iterations.
			</p>
		</div>

		<!-- Punchline -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-4 text-lg font-semibold text-text-primary">Key Takeaways</h3>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-accent-green">Robust Solution</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						The problem has a unique correct answer, and every method finds it. Five
						independent pairing approaches all produce the same 48 pairs. Five
						independent ordering approaches all polish to the same permutation.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-phase-e2e">
						Speed vs. Sophistication
					</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						The simplest methods are the fastest. Weight correlation (no data needed)
						beats multi-view fusion. Delta greedy (greedy local search) beats global
						optimization. Sophistication helps with harder problems, but this one has
						strong enough signal for simple methods.
					</p>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-[#d2a8ff]">Polish is King</h4>
					<p class="text-[15px] leading-relaxed text-text-secondary">
						Across the five method-derived starts, local swap-polish converges to the exact solution.
						The basin of attraction is wide enough that all 5 methods land inside it.
						The random starts in these runs get trapped instead.
					</p>
				</div>
			</div>
		</div>

		<!-- Caveat -->
		<div
			class="rounded-lg border border-border-subtle/50 bg-bg-inset/30 px-5 py-4 text-[13px] leading-relaxed text-text-tertiary italic"
		>
			{data.caveat}
		</div>
	</div>
{/if}
