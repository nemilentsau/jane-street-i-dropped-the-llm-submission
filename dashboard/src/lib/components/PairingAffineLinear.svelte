<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	type Feature = { name: string; accuracy: number };

	type AffineData = {
		total_recipes: number;
		exact_count: number;
		single_features: Feature[];
		c_only: {
			best_recipe: string;
			best_accuracy: number;
			single_features: Feature[];
		};
		best: { recipe: string; accuracy: number };
		e2e: { mse_delta: number; polished_mse: number };
		elapsed_s: number;
	};

	const FEATURES: Record<string, { label: string; group: string; desc: string }> = {
		trace_abs:       { label: '|trace(A)|',       group: 'Operator (gated)', desc: 'Sum of eigenvalues of the gated composed operator' },
		tr2_abs:         { label: '|trace(A\u00B2)|', group: 'Operator (gated)', desc: 'Sum of squared eigenvalues' },
		tr3_abs:         { label: '|trace(A\u00B3)|', group: 'Operator (gated)', desc: 'Sum of cubed eigenvalues' },
		sym_ratio:       { label: '||sym||/||skew||',  group: 'Operator (gated)', desc: 'Symmetry ratio of the gated operator' },
		effective_rank:  { label: 'Effective rank',    group: 'Operator (gated)', desc: 'Shannon entropy of singular value distribution' },
		neg_top4_share:  { label: 'Top-4 SV share',   group: 'Operator (gated)', desc: 'Fraction of total energy in top 4 singular values' },
		c_norm:          { label: '||c||',             group: 'Offset only',      desc: 'L2 norm of the bias offset vector' },
		c_rel_last:      { label: 'c \u00B7 w_last',  group: 'Offset only',      desc: 'Projection of offset onto final layer weights' },
		c_quad_abs:      { label: '|c\u1D40Ac|',      group: 'Offset only',      desc: 'Quadratic form of offset through the operator' },
	};

	let data: AffineData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_04_affine_linearization.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	function info(name: string) { return FEATURES[name] ?? { label: name, group: '?', desc: '' }; }

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
						+ `<br/><span style="color:#8690a2">${meta.group}</span>`
						+ `<br/><span style="color:#b0b8c8">${meta.desc}</span>`
						+ `<br/><strong style="color:${f.accuracy === 48 ? '#3dd68c' : f.accuracy > 0 ? '#6cb6ff' : '#f47067'}">${f.accuracy}/48</strong> correct pairs`;
				},
			},
			grid: { top: 8, right: 60, bottom: 24, left: 130 },
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
						color: f.accuracy === 48 ? '#3dd68c' : f.accuracy > 0 ? '#6cb6ff' : '#f47067',
						opacity: 0.85,
					},
				})),
				barMaxWidth: 18,
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

	let operatorExact: Feature[] = $derived.by(() => {
		if (!data) return [];
		return data.single_features.filter(f => f.accuracy === 48);
	});
	let operatorPartial: Feature[] = $derived.by(() => {
		if (!data) return [];
		return data.single_features.filter(f => f.accuracy > 0 && f.accuracy < 48);
	});
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python pairing/04_affine_linearization.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Linearizing each block with data-derived ReLU gates</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Instead of the raw product <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">W_out W_inp</code>,
				this method uses the gated operator
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">A = W_out diag(g) W_inp</code>
				where <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">g</code> is the
				average ReLU gate activation per hidden neuron, computed from the data.
				This captures what each candidate block <em>actually does</em> under typical inputs,
				plus the bias offset
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">c = W_out (g &odot; b_inp) + b_out</code>.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				This is the first data-dependent pairing method &mdash; it requires actual inputs to compute gate statistics.
				From (A, c), extract 9 features in three groups:
			</p>
			<ul class="mt-3 space-y-1.5 text-[15px] leading-relaxed text-text-secondary">
				<li><strong class="text-text-primary">Operator features (from A)</strong> &mdash; <span class="font-mono text-text-primary">|tr(A)|</span>, <span class="font-mono text-text-primary">|tr(A&sup2;)|</span>, <span class="font-mono text-text-primary">|tr(A&sup3;)|</span>, <span class="font-mono text-text-primary">||sym||/||skew||</span>, <span class="font-mono text-text-primary">effective rank</span>, <span class="font-mono text-text-primary">top-4 SV share</span> &mdash; same invariants as Method 2 but on the gated operator</li>
				<li><strong class="text-text-primary">Offset features (from c)</strong> &mdash; <span class="font-mono text-text-primary">||c||</span>, <span class="font-mono text-text-primary">c &middot; w_last</span>, <span class="font-mono text-text-primary">|c<sup>T</sup>Ac|</span> &mdash; bias-derived signals</li>
			</ul>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The question: does data-dependent gating add information beyond raw weights?
			</p>
		</div>

		<!-- ── 2. FEATURE RANKING ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Operator features carry the signal; offset features carry none</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				9 features extracted from the full affine parameterization (A, c).
				The same 4 trace/symmetry features that were exact on the raw operator (Method 2)
				remain exact on the gated operator &mdash; gating preserves the dominant signal.
				All 3 offset-only features score 0/48.
			</p>

			{#if barOptions}
				<div style="width: 100%; height: 340px;">
					<Chart {init} options={barOptions} theme="dark" />
				</div>
			{/if}
		</div>

		<!-- ── 3. KEY FINDING ─────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Gating preserves the operator signal</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The same 4 trace/symmetry features that were exact on the raw operator
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">M = W_out W_inp</code>
				(Method 2) remain exact on the gated operator
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">A = W_out diag(g) W_inp</code>.
				Zeroing out inactive hidden neurons does not alter which invariants recover the pairing.
				The offset vector <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">c</code>
				alone carries no pairing signal (all 3 offset features score 0/48),
				but appears in successful combined recipes as a complementary tiebreaker.
			</p>
		</div>
	</div>
{/if}
