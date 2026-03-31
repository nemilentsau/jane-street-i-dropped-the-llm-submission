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
	<div class="no-data">
		<p>Data not available. Run the script first:</p>
		<code>python pairing/01_weight_correlation.py</code>
	</div>
{:else if !data}
	<div class="loading">Loading...</div>
{:else}
	<!-- Stat cards row -->
	<div class="stats-row">
		<div class="stat-card hero">
			<span class="stat-value mono accent-green">{data.accuracy}/48</span>
			<span class="stat-label">Correct Pairs</span>
		</div>
		<div class="stat-card hero">
			<span class="stat-value mono accent-green">{data.separation.ratio}x</span>
			<span class="stat-label">Signal / Noise Ratio</span>
		</div>
		<div class="stat-card">
			<span class="stat-value mono">{fmt(data.separation.correct_mean)}</span>
			<span class="stat-label">Correct Mean</span>
		</div>
		<div class="stat-card">
			<span class="stat-value mono">{fmt(data.separation.incorrect_mean)}</span>
			<span class="stat-label">Incorrect Mean</span>
		</div>
		<div class="stat-card">
			<span class="stat-value mono" class:accent-green={data.separation.clean}>{data.separation.clean ? 'Yes' : 'No'}</span>
			<span class="stat-label">Clean Separation</span>
		</div>
		<div class="stat-card">
			<span class="stat-value mono">{data.elapsed_s}s</span>
			<span class="stat-label">Runtime</span>
		</div>
	</div>

	<!-- Visualizations -->
	<div class="viz-grid">
		<div class="viz-card">
			<Heatmap
				data={data.cost_matrix}
				title="|tr(W_out · W_inp)| — 48×48 cost matrix"
				width={420}
				height={420}
				xlabel="out piece index"
				ylabel="inp piece index"
			/>
		</div>

		<div class="viz-stack">
			<div class="viz-card">
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
			<div class="viz-card">
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
	<div class="detail-row">
		<div class="detail-card">
			<h4>Separation Detail</h4>
			<div class="detail-grid">
				<span class="detail-label">Correct min</span>
				<span class="detail-value mono">{fmt(data.separation.correct_min)}</span>
				<span class="detail-label">Incorrect max</span>
				<span class="detail-value mono">{fmt(data.separation.incorrect_max)}</span>
				<span class="detail-label">Gap (min correct − max incorrect)</span>
				<span class="detail-value mono accent-green">{fmt(data.separation.correct_min - data.separation.incorrect_max)}</span>
				<span class="detail-label">Verification MSE (GT ordering)</span>
				<span class="detail-value mono">{data.mse.toExponential(2)}</span>
			</div>
		</div>
		<div class="detail-card">
			<h4>Method</h4>
			<p class="method-desc">
				Computes <code>|tr(W_out · W_inp)|</code> for every candidate (inp, out) pair.
				Training-induced weight correlation makes correct pairs score ~{data.separation.ratio}x higher
				than incorrect pairs. Hungarian algorithm recovers the optimal assignment in O(n³).
				Requires no data — only the weight matrices.
			</p>
		</div>
	</div>
{/if}

<style>
	/* ─── Stats row ──────────────────────────────────────────── */
	.stats-row {
		display: flex;
		gap: 8px;
		margin-bottom: 20px;
	}

	.stat-card {
		flex: 1;
		background: var(--bg-card);
		border: 1px solid var(--border-subtle);
		border-radius: var(--radius-md);
		padding: 12px 16px;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}

	.stat-card.hero {
		border-color: var(--border-medium);
		background: var(--bg-card-hover);
	}

	.stat-value {
		font-size: 20px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.stat-card.hero .stat-value {
		font-size: 24px;
	}

	.stat-label {
		font-size: 10px;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-top: 2px;
	}

	.accent-green { color: var(--accent-green); }

	/* ─── Viz grid ───────────────────────────────────────────── */
	.viz-grid {
		display: flex;
		gap: 16px;
		margin-bottom: 20px;
		align-items: flex-start;
	}

	.viz-stack {
		display: flex;
		flex-direction: column;
		gap: 12px;
		flex: 1;
	}

	.viz-card {
		background: var(--bg-card);
		border: 1px solid var(--border-subtle);
		border-radius: var(--radius-lg);
		padding: 16px;
	}

	/* ─── Detail row ─────────────────────────────────────────── */
	.detail-row {
		display: flex;
		gap: 16px;
	}

	.detail-card {
		flex: 1;
		background: var(--bg-card);
		border: 1px solid var(--border-subtle);
		border-radius: var(--radius-lg);
		padding: 16px 20px;
	}

	.detail-card h4 {
		font-size: 11px;
		font-weight: 600;
		color: var(--text-tertiary);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		margin-bottom: 12px;
	}

	.detail-grid {
		display: grid;
		grid-template-columns: 1fr auto;
		gap: 6px 16px;
		align-items: baseline;
	}

	.detail-label {
		font-size: 13px;
		color: var(--text-secondary);
	}

	.detail-value {
		font-size: 13px;
		font-weight: 600;
		color: var(--text-primary);
		text-align: right;
	}

	.method-desc {
		font-size: 13px;
		color: var(--text-secondary);
		line-height: 1.6;
	}

	.method-desc code {
		background: var(--bg-inset);
		padding: 1px 5px;
		border-radius: 3px;
		font-size: 12px;
		color: var(--accent-cyan);
	}

	/* ─── States ─────────────────────────────────────────────── */
	.no-data {
		background: var(--bg-card);
		border: 1px solid var(--border-medium);
		border-radius: var(--radius-lg);
		padding: 32px;
		text-align: center;
		color: var(--text-secondary);
	}

	.no-data code {
		display: inline-block;
		margin-top: 8px;
		background: var(--bg-inset);
		padding: 4px 12px;
		border-radius: var(--radius-sm);
		font-size: 13px;
		color: var(--accent-cyan);
	}

	.loading {
		padding: 48px;
		text-align: center;
		color: var(--text-tertiary);
	}
</style>
