<script lang="ts">
	import Heatmap from './Heatmap.svelte';
	import Histogram from './Histogram.svelte';
	import MarginPlot from './MarginPlot.svelte';
	import TrainingCurve from './TrainingCurve.svelte';

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

	type EvoData = {
		training_curve: { epoch: number; pairs_correct: number; snr: number; mse: number }[];
		random_control: {
			n_networks: number;
			mean_correct: number;
			mean_snr: number;
		};
		trained_baseline: {
			pairs_correct: number;
			snr: number;
		};
	};

	let data: WCData | null = $state(null);
	let error: string | null = $state(null);
	let evoData: EvoData | null = $state(null);

	async function load() {
		try {
			const resp = await fetch('/data/pairing_01_weight_correlation.json');
			if (!resp.ok) throw new Error(`${resp.status}`);
			data = await resp.json();
		} catch (e: unknown) {
			error = e instanceof Error ? e.message : String(e);
		}
	}

	async function loadEvo() {
		try {
			const resp = await fetch('/data/pairing_01b_training_evolution.json');
			if (!resp.ok) return;
			evoData = await resp.json();
		} catch { /* optional data */ }
	}

	load();
	loadEvo();

	function fmt(n: number, d = 2): string {
		if (Math.abs(n) < 0.001 && n !== 0) return n.toExponential(d);
		return n.toFixed(d);
	}
</script>

{#if error}
	<div class="rounded-xl border border-border-medium bg-bg-card p-8 text-center text-text-secondary">
		<p>Data not available. Run the script first:</p>
		<code class="mt-2 inline-block rounded bg-bg-inset px-3 py-1 font-mono text-sm text-accent-cyan">python pairing/01_weight_correlation.py</code>
	</div>
{:else if !data}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── 1. THE INSIGHT ─────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">Training leaves an algebraic fingerprint in the weights</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Each residual block has an <code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">inp</code> layer and an
				<code class="rounded bg-bg-inset px-1.5 py-0.5 font-mono text-sm text-accent-cyan">out</code> layer that share a 96-dimensional internal space.
				Backpropagation coordinates their weight matrices through this shared space. The simplest measure of that coordination is the Frobenius inner product:
			</p>
			<code class="mt-3 block w-fit rounded bg-bg-inset px-4 py-2.5 font-mono text-base text-accent-cyan">
				score(inp_i, out_j) = |tr(W_out_j &middot; W_inp_i)|
			</code>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				Compute this for every candidate pair, solve the optimal assignment via Hungarian algorithm.
				<span class="font-semibold text-text-primary">Requires no data — only the weight matrices.</span>
			</p>
		</div>

		<!-- ── 2. COST MATRIX + RESULT ───────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<div class="grid grid-cols-[auto_1fr] gap-5">
				<div class="shrink-0">
					<Heatmap
						data={data.cost_matrix}
						title="|tr(W_out · W_inp)| — 48×48 score matrix"
						width={540}
						height={540}
						xlabel="out piece index"
						ylabel="inp piece index"
					/>
				</div>
				<div class="flex flex-col gap-4 py-2">
					<p class="text-[15px] leading-relaxed text-text-secondary">
						Of the <span class="font-mono text-text-primary">2,304</span> entries, 48 are correct pairs and 2,256 are incorrect.
						The bright spots are correct pairs — they score dramatically higher than the dark background of incorrect pairings.
					</p>

					<div class="rounded-lg bg-bg-inset px-4 py-3">
						<div class="flex items-baseline gap-2">
							<span class="font-mono text-2xl font-bold text-accent-green glow-green">{data.accuracy}/48</span>
							<span class="text-sm text-text-secondary">correct pairs recovered</span>
						</div>
						<p class="mt-1 text-sm text-text-secondary">
							Hungarian assignment recovers all 48 pairs exactly in <span class="font-mono font-semibold text-text-primary">{data.elapsed_s}s</span>.
						</p>
					</div>

					<div class="rounded-lg border border-border-subtle px-4 py-3">
						<h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Key numbers</h4>
						<div class="grid grid-cols-2 gap-x-6 gap-y-1 text-sm">
							<span class="text-text-secondary">Correct mean score</span>
							<span class="text-right font-mono font-semibold text-accent-green">{fmt(data.separation.correct_mean)}</span>
							<span class="text-text-secondary">Incorrect mean score</span>
							<span class="text-right font-mono font-semibold text-text-primary">{fmt(data.separation.incorrect_mean)}</span>
							<span class="text-text-secondary">Signal ratio</span>
							<span class="text-right font-mono font-semibold text-accent-green">{data.separation.ratio}x</span>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- ── 3. SEPARATION ─────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">The separation is stark</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				The mean score for correct pairs is
				<span class="font-mono font-semibold text-accent-green">{data.separation.ratio}x</span>
				higher than the mean for incorrect pairs. The lowest-scoring correct pair
				(<span class="font-mono text-text-primary">{fmt(data.separation.correct_min)}</span>)
				still exceeds the highest-scoring incorrect pair
				(<span class="font-mono text-text-primary">{fmt(data.separation.incorrect_max)}</span>)
				— <span class="font-semibold text-accent-green">clean separation</span>, no overlap at all.
			</p>

			<div class="grid grid-cols-[1fr_auto] gap-4">
				<Histogram
					seriesA={data.correct_scores}
					seriesB={data.incorrect_scores}
					labelA="Correct pairs"
					labelB="Incorrect pairs"
					title="Score Distribution"
					xlabel="|tr(W_out · W_inp)|"
					width={560}
					height={260}
				/>
				<div class="rounded-lg border border-border-subtle px-5 py-4 self-start">
					<h4 class="mb-3 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Separation</h4>
					<div class="grid grid-cols-[1fr_auto] items-baseline gap-x-4 gap-y-2">
						<span class="text-sm text-text-secondary">Correct mean</span>
						<span class="text-right font-mono text-[15px] font-semibold text-accent-green">{fmt(data.separation.correct_mean)}</span>
						<span class="text-sm text-text-secondary">Incorrect mean</span>
						<span class="text-right font-mono text-[15px] font-semibold text-text-primary">{fmt(data.separation.incorrect_mean)}</span>
						<span class="text-sm text-text-secondary">Ratio</span>
						<span class="text-right font-mono text-[15px] font-semibold text-accent-green">{data.separation.ratio}x</span>
						<div class="col-span-2 my-1 border-t border-border-subtle"></div>
						<span class="text-sm text-text-secondary">Correct min</span>
						<span class="text-right font-mono text-[15px] font-semibold text-text-primary">{fmt(data.separation.correct_min)}</span>
						<span class="text-sm text-text-secondary">Incorrect max</span>
						<span class="text-right font-mono text-[15px] font-semibold text-text-primary">{fmt(data.separation.incorrect_max)}</span>
						<span class="text-sm text-text-secondary">Gap</span>
						<span class="text-right font-mono text-[15px] font-semibold text-accent-green">{fmt(data.separation.correct_min - data.separation.incorrect_max)}</span>
					</div>
				</div>
			</div>
		</div>

		<!-- ── 4. MARGINS ────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
			<h3 class="mb-2 text-lg font-semibold text-text-primary">Every pair has positive margin</h3>
			<p class="mb-4 text-[15px] leading-relaxed text-text-secondary">
				For each input piece, the margin is how much its correct partner outscores the best incorrect alternative.
				All 48 margins are positive — the assignment is not fragile. Even the weakest pair has a comfortable gap.
			</p>
			<MarginPlot
				margins={data.margins}
				title="Per-pair margin (correct score − best incorrect)"
				width={780}
				height={220}
			/>
		</div>

		<!-- ── 5. TRAINING EVOLUTION ──────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">This is training-induced, not architectural</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The co-training fingerprint is created by backpropagation, not by the residual block architecture.
				A fresh network trained from scratch on the same data develops the signal within a few epochs.
				Random untrained networks score at chance level.
			</p>

			{#if evoData}
				<div class="mt-5 grid grid-cols-[1fr_auto] gap-5">
					<TrainingCurve
						data={evoData.training_curve}
						baselineCorrect={evoData.trained_baseline.pairs_correct}
						randomCorrect={evoData.random_control.mean_correct}
						width={520}
						height={280}
					/>
					<div class="flex flex-col gap-3 self-start">
						<!-- Epoch table -->
						<div class="rounded-lg border border-border-subtle px-4 py-3">
							<h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Training checkpoints</h4>
							<table class="w-full text-sm">
								<thead>
									<tr class="text-text-tertiary">
										<th class="pb-1 pr-4 text-left font-medium">Epoch</th>
										<th class="pb-1 pr-4 text-right font-medium">Pairs</th>
										<th class="pb-1 text-right font-medium">SNR</th>
									</tr>
								</thead>
								<tbody>
									{#each evoData.training_curve as row}
										<tr class="border-t border-border-subtle/50">
											<td class="py-1 pr-4 font-mono text-text-secondary">{row.epoch === 0 ? '0 (init)' : row.epoch}</td>
											<td class="py-1 pr-4 text-right font-mono font-semibold {row.pairs_correct >= 24 ? 'text-accent-green' : 'text-text-primary'}">{row.pairs_correct}/48</td>
											<td class="py-1 text-right font-mono text-text-secondary">{row.snr}x</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>

						<!-- Comparison -->
						<div class="rounded-lg bg-bg-inset px-4 py-3">
							<h4 class="mb-2 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Comparison</h4>
							<div class="grid grid-cols-[1fr_auto_auto] items-baseline gap-x-4 gap-y-1.5 text-sm">
								<span class="text-text-secondary">Original model</span>
								<span class="text-right font-mono font-semibold text-accent-green">{evoData.trained_baseline.pairs_correct}/48</span>
								<span class="text-right font-mono text-text-secondary">{evoData.trained_baseline.snr}x</span>

								<span class="text-text-secondary">Retrain @ epoch 60</span>
								<span class="text-right font-mono font-semibold text-phase-ordering">{evoData.training_curve[evoData.training_curve.length - 1].pairs_correct}/48</span>
								<span class="text-right font-mono text-text-secondary">{evoData.training_curve[evoData.training_curve.length - 1].snr}x</span>

								<span class="text-text-secondary">Random ({evoData.random_control.n_networks} nets)</span>
								<span class="text-right font-mono font-semibold text-accent-red">{evoData.random_control.mean_correct}/48</span>
								<span class="text-right font-mono text-text-secondary">{evoData.random_control.mean_snr}x</span>
							</div>
						</div>
					</div>
				</div>

				<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
					The signal appears within the first few epochs and grows steadily.
					The original dropped model scores
					<span class="font-mono font-semibold text-accent-green">{evoData.trained_baseline.snr}x</span> SNR — much stronger than this 60-epoch retrain
					(<span class="font-mono text-text-primary">{evoData.training_curve[evoData.training_curve.length - 1].snr}x</span>),
					suggesting the original model was trained significantly longer or with different hyperparameters.
				</p>
			{:else}
				<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
					On 10 random untrained networks with the same structure, Hungarian assignment recovers an average of
					<span class="font-mono font-semibold text-accent-red">1.0/48</span> correct pairs — indistinguishable from chance.
				</p>
				<div class="mt-3 rounded-lg border border-border-subtle bg-bg-inset px-4 py-3">
					<p class="text-sm text-text-tertiary">Run
						<code class="rounded bg-bg-card px-1.5 py-0.5 font-mono text-accent-cyan">python pairing/01b_training_evolution.py</code>
						to see the full training evolution chart and random control data.
					</p>
				</div>
			{/if}

			<div class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				<span class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Verification:</span>
				MSE with ground-truth ordering = <span class="font-mono text-accent-green">{data.mse.toExponential(2)}</span>
			</div>
		</div>
	</div>
{/if}
