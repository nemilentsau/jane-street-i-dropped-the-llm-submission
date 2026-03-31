<script lang="ts">
	import Heatmap from './Heatmap.svelte';
	import Histogram from './Histogram.svelte';
	import MarginPlot from './MarginPlot.svelte';

	type WCData = {
		method: string;
		accuracy: number;
		cost_matrix: number[][];
		correct_scores: number[];
		incorrect_scores: number[];
		margins: number[];
		separation: {
			correct_mean: number;
			correct_min: number;
			incorrect_mean: number;
			incorrect_max: number;
			ratio: number;
			clean: boolean;
		};
		mse: number;
		elapsed_s: number;
	};

	let data: WCData | null = $state(null);
	let error: string | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_01_weight_correlation.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: any) {
			error = e.message;
		}
	}

	load();

	function fmt(n: number, d = 2): string {
		if (Math.abs(n) < 0.001 && n !== 0) return n.toExponential(d);
		return n.toFixed(d);
	}
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-[13px] text-accent-cyan">python pairing/01_weight_correlation.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<!-- Stat cards row -->
	<div class="mb-5 flex gap-2">
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-medium bg-bg-card-hover px-4 py-3 text-center">
			<span class="font-mono text-2xl font-bold text-accent-green">{data.accuracy}/48</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Correct Pairs</span>
		</div>
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-medium bg-bg-card-hover px-4 py-3 text-center">
			<span class="font-mono text-2xl font-bold text-accent-green">{data.separation.ratio}x</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Signal / Noise</span>
		</div>
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center">
			<span class="font-mono text-xl font-bold text-text-primary">{fmt(data.separation.correct_mean)}</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Correct Mean</span>
		</div>
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center">
			<span class="font-mono text-xl font-bold text-text-primary">{fmt(data.separation.incorrect_mean)}</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Incorrect Mean</span>
		</div>
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center">
			<span class="font-mono text-xl font-bold {data.separation.clean ? 'text-accent-green' : 'text-accent-red'}">{data.separation.clean ? 'Yes' : 'No'}</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Clean Separation</span>
		</div>
		<div class="flex flex-1 flex-col items-center rounded-lg border border-border-subtle bg-bg-card px-4 py-3 text-center">
			<span class="font-mono text-xl font-bold text-text-primary">{data.elapsed_s}s</span>
			<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">Runtime</span>
		</div>
	</div>

	<!-- Visualizations -->
	<div class="mb-5 flex items-start gap-4">
		<div class="rounded-xl border border-border-subtle bg-bg-card p-4">
			<Heatmap
				data={data.cost_matrix}
				title="|tr(W_out · W_inp)| — 48×48 cost matrix"
				width={420}
				height={420}
				xlabel="out piece index"
				ylabel="inp piece index"
			/>
		</div>

		<div class="flex flex-1 flex-col gap-3">
			<div class="rounded-xl border border-border-subtle bg-bg-card p-4">
				<Histogram
					seriesA={data.correct_scores}
					seriesB={data.incorrect_scores}
					labelA="Correct pairs"
					labelB="Incorrect pairs"
					title="Score Distribution"
					xlabel="|tr(W_out · W_inp)|"
					width={480}
					height={220}
				/>
			</div>
			<div class="rounded-xl border border-border-subtle bg-bg-card p-4">
				<MarginPlot
					margins={data.margins}
					title="Per-pair Assignment Margin (correct − best incorrect)"
					width={480}
					height={200}
				/>
			</div>
		</div>
	</div>

	<!-- Detail stats -->
	<div class="flex gap-4">
		<div class="flex-1 rounded-xl border border-border-subtle bg-bg-card px-5 py-4">
			<h4 class="mb-3 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">Separation Detail</h4>
			<div class="grid grid-cols-[1fr_auto] items-baseline gap-x-4 gap-y-1.5">
				<span class="text-[13px] text-text-secondary">Correct min</span>
				<span class="text-right font-mono text-[13px] font-semibold text-text-primary">{fmt(data.separation.correct_min)}</span>
				<span class="text-[13px] text-text-secondary">Incorrect max</span>
				<span class="text-right font-mono text-[13px] font-semibold text-text-primary">{fmt(data.separation.incorrect_max)}</span>
				<span class="text-[13px] text-text-secondary">Gap (min correct − max incorrect)</span>
				<span class="text-right font-mono text-[13px] font-semibold text-accent-green">{fmt(data.separation.correct_min - data.separation.incorrect_max)}</span>
				<span class="text-[13px] text-text-secondary">Verification MSE (GT ordering)</span>
				<span class="text-right font-mono text-[13px] font-semibold text-text-primary">{data.mse.toExponential(2)}</span>
			</div>
		</div>
		<div class="flex-1 rounded-xl border border-border-subtle bg-bg-card px-5 py-4">
			<h4 class="mb-3 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">Method</h4>
			<p class="text-[13px] leading-relaxed text-text-secondary">
				Computes <code class="rounded bg-bg-inset px-1.5 py-px font-mono text-xs text-accent-cyan">|tr(W_out · W_inp)|</code> for every candidate (inp, out) pair.
				Training-induced weight correlation makes correct pairs score ~{data.separation.ratio}x higher
				than incorrect pairs. Hungarian algorithm recovers the optimal assignment in O(n³).
				Requires no data — only the weight matrices.
			</p>
		</div>
	</div>
{/if}
