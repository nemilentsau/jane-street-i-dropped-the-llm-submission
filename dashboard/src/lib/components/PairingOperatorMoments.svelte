<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	type Feature = { name: string; accuracy: number };

	type OMData = {
		total_recipes: number;
		exact_count: number;
		accuracy_distribution: Record<string, number>;
		single_features: Feature[];
		top_recipes: { recipe: string; accuracy: number }[];
		best: { recipe: string; accuracy: number };
		e2e: { mse_delta: number; polished_mse: number };
		elapsed_s: number;
	};

	const FEATURES: Record<string, { label: string; group: string; desc: string }> = {
		trace_abs:       { label: '|trace(M)|',       group: 'Trace moments',  desc: 'Sum of eigenvalues of W_out W_inp' },
		tr2_abs:         { label: '|trace(M\u00B2)|', group: 'Trace moments',  desc: 'Sum of squared eigenvalues \u2014 concentrates on dominant modes' },
		tr3_abs:         { label: '|trace(M\u00B3)|', group: 'Trace moments',  desc: 'Sum of cubed eigenvalues \u2014 concentrates further' },
		sym_ratio:       { label: '||sym||/||skew||',  group: 'Symmetry',       desc: 'How symmetric vs antisymmetric the composed operator is' },
		effective_rank:  { label: 'Effective rank',    group: 'SV concentration', desc: 'Shannon entropy of singular value distribution' },
		stable_rank:     { label: 'Stable rank',       group: 'SV concentration', desc: '\u03A3s\u00B2 / s\u2081\u00B2 \u2014 measures spectral spread' },
		neg_top1_share:  { label: 'Top-1 SV share',   group: 'SV concentration', desc: 'Fraction of total energy in the dominant singular value' },
		neg_top4_share:  { label: 'Top-4 SV share',   group: 'SV concentration', desc: 'Fraction of total energy in the top 4 singular values' },
		kl_to_exp:       { label: 'KL to exponential', group: 'SV concentration', desc: 'Divergence from an exponential decay benchmark' },
	};

	let data: OMData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_02_operator_moments.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}
	load();

	function info(name: string) { return FEATURES[name] ?? { label: name, group: '?', desc: '' }; }

	// Features sorted worst-to-best for bottom-to-top bar chart
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
						+ `<br/><strong style="color:${f.accuracy === 48 ? '#3dd68c' : '#6cb6ff'}">${f.accuracy}/48</strong> correct pairs`;
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
						color: f.accuracy === 48 ? '#3dd68c' : f.accuracy >= 28 ? '#6cb6ff' : '#8690a2',
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
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python pairing/02_operator_moments.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. INSIGHT + FEATURE DEFINITIONS ─────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Spectral invariants of the composed operator</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				For each candidate pair (inp, out), form the composed operator
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">M = W_out @ W_inp</code>.
				This 48&times;48 matrix is the linear map from input space back to input space through
				the block's hidden layer, ignoring the ReLU and residual connection.
				From each M, extract 9 scalar invariants in three families:
				<strong class="text-text-primary">trace moments</strong> (|tr(M)|, |tr(M&sup2;)|, |tr(M&sup3;)|),
				<strong class="text-text-primary">symmetry structure</strong> (||sym||/||skew||),
				and <strong class="text-text-primary">singular value concentration</strong>
				(effective rank, stable rank, top-1 share, top-4 share, KL to exponential).
				Each produces a 48&times;48 cost matrix; Hungarian assignment on each independently recovers the optimal pairing.
			</p>
		</div>

		<!-- ── 2. FEATURE RANKING (chart only, full width) ────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Individual feature accuracy</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each feature's 48&times;48 cost matrix fed to Hungarian assignment independently.
				The four trace/symmetry features each recover all 48 pairs;
				the five SV concentration features score 7&ndash;32/48.
				No combination of SV features alone reaches 48/48 &mdash;
				they all discard the same sign and phase information.
			</p>

			{#if barOptions}
				<div style="width: 100%; height: 320px;">
					<Chart {init} options={barOptions} theme="dark" />
				</div>
			{/if}
		</div>

		<!-- ── 3. WHY TRACES DOMINATE ──────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Why traces dominate over singular value features</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The first trace moment <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">|tr(W_out W_inp)|</code>
				is algebraically equivalent to the Frobenius inner product from Method 1 &mdash; it measures
				the total coordination between the two weight matrices through the shared 96-D space.
				Higher trace powers (tr&sup2;, tr&sup3;) increasingly emphasize the dominant eigenvalues,
				yet all three are independently exact. The symmetry ratio captures a different aspect:
				correctly paired blocks have more symmetric composed operators than incorrect pairings.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Singular value features (effective rank, stable rank, top-k share) score 7&ndash;32/48 alone.
				They discard sign and phase information that traces retain &mdash;
				the eigenvalue spectrum of M is complex-valued, and traces preserve the full algebraic structure
				while singular values collapse it to magnitudes.
			</p>
		</div>
	</div>
{/if}
