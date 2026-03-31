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
		sym_ratio:       { label: '||sym||/||skew||',  group: 'Matrix shape',   desc: 'How symmetric vs antisymmetric the composed operator is' },
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

	let exactFeatures: Feature[] = $derived.by(() => data ? data.single_features.filter(f => f.accuracy === 48) : []);
	let partialFeatures: Feature[] = $derived.by(() => data ? data.single_features.filter(f => f.accuracy < 48) : []);
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

		<!-- ── 1. INSIGHT ──────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">The composed operator encodes pairing in multiple ways</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				For each candidate pair, multiply the weight matrices to form the composed operator
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">M = W_out @ W_inp</code>.
				This 48x48 matrix is the linear map from input space back to input space through the block's hidden layer,
				ignoring the ReLU and residual connection. Extract 9 algebraic invariants from it &mdash;
				trace moments, symmetry structure, and singular value concentration &mdash;
				then search over weighted combinations via Hungarian assignment.
			</p>
		</div>

		<!-- ── 2. FEATURE RANKING ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Four features are individually exact, five are partial</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				Each feature used alone with Hungarian assignment. The split is sharp:
				trace moments and symmetry ratio each recover all 48 pairs;
				singular value concentration measures capture partial signal (7&ndash;32 pairs)
				but reach exact when combined.
			</p>

			<div class="grid grid-cols-[1fr_auto] gap-5">
				{#if barOptions}
					<div style="width: 640px; height: 320px;">
						<Chart {init} options={barOptions} theme="dark" />
					</div>
				{/if}

				<div class="flex flex-col gap-4 self-start">
					<!-- Exact tier -->
					<div class="rounded-lg bg-accent-green/8 border border-accent-green/20 px-4 py-3">
						<h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-accent-green">Exact alone (48/48)</h4>
						{#each exactFeatures as f}
							<div class="flex items-start gap-2 py-1">
								<span class="mt-0.5 shrink-0 text-sm text-accent-green">&#10003;</span>
								<div>
									<span class="text-sm font-medium text-text-primary">{info(f.name).label}</span>
									<p class="text-xs text-text-tertiary">{info(f.name).desc}</p>
								</div>
							</div>
						{/each}
					</div>

					<!-- Partial tier -->
					<div class="rounded-lg border border-border-subtle px-4 py-3">
						<h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Partial alone</h4>
						{#each partialFeatures as f}
							<div class="flex items-baseline justify-between gap-3 py-0.5">
								<span class="text-sm text-text-secondary">{info(f.name).label}</span>
								<span class="font-mono text-xs text-text-tertiary">{f.accuracy}/48</span>
							</div>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- ── 3. ROBUSTNESS ───────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">Robustness: the signal survives any reasonable combination</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				All 1-, 2-, and 3-feature subsets were tested at 5 weight levels each
				(<span class="font-mono text-text-primary">{data.total_recipes.toLocaleString()}</span> total recipes).
				<span class="font-mono font-semibold text-accent-green">{data.exact_count.toLocaleString()}</span> recover the exact pairing
				&mdash; <span class="font-mono font-semibold text-accent-green">{(100 * data.exact_count / data.total_recipes).toFixed(1)}%</span>
				of all combinations tested.
				Even partial features combine to exact: adding any trace moment to a weak spectral feature lifts it to 48/48.
			</p>
			<div class="grid grid-cols-3 gap-4">
				<div class="rounded-lg bg-bg-inset px-4 py-3 text-center">
					<div class="font-mono text-2xl font-bold text-text-primary">{data.total_recipes.toLocaleString()}</div>
					<div class="mt-1 text-xs text-text-tertiary">recipes tested</div>
				</div>
				<div class="rounded-lg bg-bg-inset px-4 py-3 text-center">
					<div class="font-mono text-2xl font-bold text-accent-green glow-green">{data.exact_count.toLocaleString()}</div>
					<div class="mt-1 text-xs text-text-tertiary">exact (48/48)</div>
				</div>
				<div class="rounded-lg bg-bg-inset px-4 py-3 text-center">
					<div class="font-mono text-2xl font-bold text-accent-green glow-green">{data.e2e.polished_mse.toExponential(2)}</div>
					<div class="mt-1 text-xs text-text-tertiary">polished MSE</div>
				</div>
			</div>
		</div>

		<!-- ── 4. WHY TRACES DOMINATE ──────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Why traces are strongest</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The first trace moment <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">|tr(W_out W_inp)|</code>
				is algebraically equivalent to the Frobenius inner product from Method 1 &mdash; it measures
				the total coordination between the two weight matrices through the shared 96-D space.
				Higher trace powers (trace<sup>2</sup>, trace<sup>3</sup>) increasingly emphasize the dominant eigenvalues,
				yet all three are independently exact. The symmetry ratio captures a different aspect:
				correctly paired blocks have more symmetric composed operators than incorrect pairings.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Singular value features alone failed in earlier experiments (35/48 with 5 SV features).
				They discard sign and phase information that the trace retains.
				The composed operator <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">W_out W_inp</code>
				is the right object; its full algebraic structure, not just its spectrum, encodes the co-training fingerprint.
			</p>
		</div>
	</div>
{/if}
