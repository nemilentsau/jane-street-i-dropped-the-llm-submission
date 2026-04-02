<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	type Feature = { name: string; accuracy: number };

	type SVDData = {
		total_recipes: number;
		exact_count: number;
		single_features: Feature[];
		best: { recipe: string; accuracy: number };
		e2e: { mse_delta: number; polished_mse: number };
		elapsed_s: number;
	};

	const FEATURE_INFO: Record<string, { label: string; desc: string }> = {
		hidden_diag:  { label: 'Diagonal match',   desc: 'Mode-by-mode alignment: how well the k-th write direction aligns with the k-th read direction' },
		hidden_top8:  { label: 'Top-8 diagonal',   desc: 'Same as diagonal but only the 8 strongest modes \u2014 focuses on dominant directions' },
		hidden_match: { label: 'Optimal matching',  desc: 'Hungarian assignment within the alignment matrix \u2014 best 1:1 mode correspondence' },
		hidden_frob:  { label: 'Frobenius norm',    desc: 'Total energy in the absolute alignment matrix. Related to Method 1\u2019s Frobenius inner product, but uses only hidden-space modes and discards sign' },
	};

	let data: SVDData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_03_svd_cross_alignment.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	function info(name: string) { return FEATURE_INFO[name] ?? { label: name, desc: '' }; }

	let sorted: Feature[] = $derived.by(() => {
		if (!data) return [];
		return [...data.single_features].sort((a, b) => a.accuracy - b.accuracy);
	});

	let barOptions = $derived.by(() => {
		if (!sorted.length) return null;
		return {
			tooltip: {
				trigger: 'axis' as const,
				axisPointer: { type: 'shadow' as const },
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = (params as { dataIndex: number }[])[0];
					const f = sorted[p.dataIndex];
					const meta = info(f.name);
					return `<strong style="color:#eceff4">${meta.label}</strong>`
						+ `<br/><span style="color:#b0b8c8">${meta.desc}</span>`
						+ `<br/><strong style="color:${f.accuracy === 48 ? '#3dd68c' : '#6cb6ff'}">${f.accuracy}/48</strong>`;
				},
			},
			grid: { top: 8, right: 60, bottom: 24, left: 140 },
			xAxis: {
				type: 'value' as const,
				min: 0, max: 50,
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			yAxis: {
				type: 'category' as const,
				data: sorted.map(f => info(f.name).label),
				axisLabel: { color: '#b0b8c8', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			series: [{
				type: 'bar' as const,
				data: sorted.map(f => ({
					value: f.accuracy,
					itemStyle: {
						color: f.accuracy === 48 ? '#3dd68c' : f.accuracy >= 40 ? '#6cb6ff' : '#8690a2',
						opacity: 0.85,
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
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python pairing/03_svd_cross_alignment.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. THE GEOMETRIC INSIGHT ────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Aligning write/read directions in the shared hidden space</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Each <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">inp</code> layer
				(R<sup>48</sup> &rarr; R<sup>96</sup>) writes into the 96-D hidden space along its left-singular vectors.
				Each <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">out</code> layer
				(R<sup>96</sup> &rarr; R<sup>48</sup>) reads from the same space along its right-singular vectors.
				Correctly paired layers have aligned principal modes at this shared interface.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				For each candidate pair, build the SV-weighted alignment matrix
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">|U_inp<sup>T</sup> V_out| &odot; (s_inp &otimes; s_out)</code>
				and extract 4 alignment scores:
			</p>
			<ul class="mt-3 space-y-1.5 text-[15px] leading-relaxed text-text-secondary">
				<li><span class="font-mono text-text-primary">Frobenius norm</span> &mdash; total energy in the alignment matrix</li>
				<li><span class="font-mono text-text-primary">Optimal matching</span> &mdash; Hungarian assignment within the alignment matrix, best 1:1 mode correspondence</li>
				<li><span class="font-mono text-text-primary">Diagonal match</span> &mdash; how well the k-th write direction aligns with the k-th read direction</li>
				<li><span class="font-mono text-text-primary">Top-8 diagonal</span> &mdash; same but restricted to the 8 strongest modes</li>
			</ul>
		</div>

		<!-- ── 2. OUTER VS HIDDEN ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Where you look matters more than how you look</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each weight matrix touches two spaces: the outer 48-D input/output space and the
				shared 96-D hidden space. The alignment signal lives exclusively at the hidden-space interface
				where blocks actually write and read.
			</p>
			<div class="grid grid-cols-2 gap-4">
				<div class="rounded-lg border border-accent-red/30 bg-accent-red/5 px-5 py-4">
					<div class="mb-2 flex items-baseline gap-2">
						<span class="font-mono text-2xl font-bold text-accent-red">16/48</span>
						<span class="text-xs font-semibold uppercase tracking-wider text-accent-red/70">Outer space</span>
					</div>
					<h4 class="mb-1 text-base font-semibold text-text-primary">Outer 48-D alignment</h4>
					<p class="text-sm leading-relaxed text-text-secondary">
						Aligning right-singular vectors of W_inp with left-singular vectors of W_out
						in their respective 48-D input/output spaces.
						These spaces are disconnected from where the block computes &mdash;
						no training pressure aligns modes here.
					</p>
				</div>
				<div class="rounded-lg border border-accent-green/30 bg-accent-green/5 px-5 py-4">
					<div class="mb-2 flex items-baseline gap-2">
						<span class="font-mono text-2xl font-bold text-accent-green">{data.best.accuracy}/48</span>
						<span class="text-xs font-semibold uppercase tracking-wider text-accent-green/70">Hidden space</span>
					</div>
					<h4 class="mb-1 text-base font-semibold text-text-primary">Hidden 96-D alignment</h4>
					<p class="text-sm leading-relaxed text-text-secondary">
						Aligning left-singular vectors of W_inp with right-singular vectors of W_out
						in the shared 96-D hidden space. Co-trained layers develop
						coordinated write/read directions at this interface.
					</p>
				</div>
			</div>
			<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
				The 16/48 &rarr; 48/48 gap confirms that the co-training fingerprint is spatial:
				it lives at the hidden-space interface where blocks communicate, not in
				the outer spaces where the architecture merely defines dimensionality.
			</p>
		</div>

		<!-- ── 3. FEATURE RANKING ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Four alignment measures, all in hidden space</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each feature extracts a different summary from the SV-weighted alignment matrix.
				Frobenius norm (total energy) is the only one exact alone.
				The other three score 9&ndash;32/48 and cannot combine to exact without it (best: 37/48).
			</p>

			{#if barOptions}
				<div style="width: 100%; height: 200px;">
					<Chart {init} options={barOptions} theme="dark" />
				</div>
			{/if}
		</div>
	</div>
{/if}
