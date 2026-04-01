<script lang="ts">
	import Pipeline from './Pipeline.svelte';
</script>

<div class="mx-auto w-full max-w-[1100px] px-8 pt-8 pb-16">
	<!-- Hero -->
	<div class="mb-8 fade-in-up">
		<h2 class="font-display text-[28px] font-bold tracking-tight text-text-primary">Reassembling a Dropped Trading Model</h2>
		<p class="mt-2 text-[15px] leading-relaxed text-text-secondary">
			A residual neural network used for trading fell apart into 97 shuffled linear layers.
			The search space is <span class="font-mono text-text-primary">(48!)&#178; &#8776; 10&#185;&#178;&#185;</span>.
			The recovered answer is verified at <span class="font-mono text-accent-green glow-green">MSE = 3.16e-14</span>.
		</p>
	</div>

	<!-- Key metrics -->
	<div class="mb-8 grid grid-cols-4 gap-3">
		<div class="card-elevated rounded-lg border border-border-subtle bg-bg-card px-4 py-5 text-center fade-in-up" style="animation-delay: 0.05s">
			<span class="font-mono text-3xl font-bold text-accent-green glow-green">3.16e-14</span>
			<span class="mt-1.5 block text-xs font-semibold uppercase tracking-wider text-text-tertiary">Final MSE</span>
		</div>
		<div class="card-elevated rounded-lg border border-border-subtle bg-bg-card px-4 py-5 text-center fade-in-up" style="animation-delay: 0.1s">
			<span class="font-mono text-3xl font-bold text-text-primary">(48!)&#178;</span>
			<span class="mt-0.5 block font-mono text-[13px] text-text-tertiary">&#8776; 10&#185;&#178;&#185;</span>
			<span class="mt-1.5 block text-xs font-semibold uppercase tracking-wider text-text-tertiary">Search Space</span>
		</div>
		<div class="card-elevated rounded-lg border border-border-subtle bg-bg-card px-4 py-5 text-center fade-in-up" style="animation-delay: 0.15s">
			<span class="font-mono text-3xl font-bold text-accent-green glow-green">23x</span>
			<span class="mt-0.5 block font-mono text-[13px] text-text-tertiary">correct / incorrect</span>
			<span class="mt-1.5 block text-xs font-semibold uppercase tracking-wider text-text-tertiary">Pairing Signal</span>
		</div>
		<div class="card-elevated rounded-lg border border-border-subtle bg-bg-card px-4 py-5 text-center fade-in-up" style="animation-delay: 0.2s">
			<span class="font-mono text-3xl font-bold text-accent-blue glow-blue">77/97</span>
			<span class="mt-0.5 block font-mono text-[13px] text-text-tertiary">before polish</span>
			<span class="mt-1.5 block text-xs font-semibold uppercase tracking-wider text-text-tertiary">Best Raw Ordering</span>
		</div>
	</div>

	<!-- Pipeline diagram -->
	<div class="mb-8 fade-in-up" style="animation-delay: 0.25s">
		<Pipeline />
	</div>

	<!-- Architecture -->
	<div class="mb-8 rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated fade-in-up" style="animation-delay: 0.3s">
		<h3 class="mb-3 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Architecture</h3>
		<code class="block rounded bg-bg-inset px-4 py-3 font-mono text-[15px] leading-relaxed">
			<span class="text-text-secondary">x</span>
			<span class="text-text-tertiary"> &#8594; </span>
			<span class="text-text-secondary">x + </span>
			<span class="text-accent-amber">W_out</span><span class="text-text-tertiary">(</span><span class="text-accent-red">ReLU</span><span class="text-text-tertiary">(</span><span class="text-accent-cyan">W_inp</span>
			<span class="text-text-tertiary"> &#183; </span>
			<span class="text-text-secondary">x</span>
			<span class="text-text-tertiary"> + </span>
			<span class="text-accent-cyan">b_inp</span><span class="text-text-tertiary">)) + </span>
			<span class="text-accent-amber">b_out</span>
		</code>
		<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
			48 residual blocks, each with an <span class="font-mono text-accent-cyan">inp</span> layer (R&#8308;&#8312; &#8594; R&#8313;&#8310;) and an <span class="font-mono text-accent-amber">out</span> layer (R&#8313;&#8310; &#8594; R&#8308;&#8312;), plus one final linear readout.
			The puzzle factorizes into two independent inverse problems.
		</p>
	</div>

	<!-- Two propositions -->
	<div class="mb-6 grid grid-cols-2 gap-4">
		<div class="rounded-xl border border-phase-pairing/20 bg-bg-card px-5 py-5 card-elevated fade-in-up" style="animation-delay: 0.35s">
			<h3 class="mb-1 text-base font-semibold text-text-primary">Pairing: Weight Correlation</h3>
			<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-phase-pairing">All 5 methods &#8594; 48/48</p>
			<p class="mb-3 text-[15px] leading-relaxed text-text-secondary">
				Each block's <span class="font-mono text-accent-cyan">inp</span> and <span class="font-mono text-accent-amber">out</span> share a 96-D internal space. Backpropagation leaves an algebraic co-training fingerprint:
				<code class="rounded bg-bg-inset px-1.5 py-px font-mono text-sm text-accent-cyan">|tr(W_out &#183; W_inp)|</code>
				scores correct pairs 23x higher than incorrect ones. Clean separation — no data needed.
			</p>
			<div class="space-y-1.5 text-sm text-text-secondary">
				<div class="flex justify-between"><span>Weight Correlation</span><span class="font-mono text-accent-green">48/48</span></div>
				<div class="flex justify-between"><span>Operator Moments</span><span class="font-mono text-accent-green">48/48</span></div>
				<div class="flex justify-between"><span>SVD Cross-Alignment</span><span class="font-mono text-accent-green">48/48</span></div>
				<div class="flex justify-between"><span>Affine Linearization</span><span class="font-mono text-accent-green">48/48</span></div>
				<div class="flex justify-between"><span>Multi-View Fusion</span><span class="font-mono text-accent-green">48/48</span></div>
			</div>
		</div>

		<div class="rounded-xl border border-phase-ordering/20 bg-bg-card px-5 py-5 card-elevated fade-in-up" style="animation-delay: 0.4s">
			<h3 class="mb-1 text-base font-semibold text-text-primary">Ordering: Land Near, Then Polish</h3>
			<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-phase-ordering">All methods &#8594; exact after polish</p>
			<p class="mb-3 text-[15px] leading-relaxed text-text-secondary">
				No raw ordering method recovers the exact sequence. Every successful one lands close enough that greedy pairwise swap polish (try every swap, keep improvements, repeat) finishes the job in 2–5 iterations.
			</p>
			<div class="space-y-1.5 text-sm text-text-secondary">
				<div class="flex justify-between"><span>Delta Greedy</span><span class="text-right font-mono text-text-primary">77/97 raw</span></div>
				<div class="flex justify-between"><span>Pairwise Tournament</span><span class="text-right font-mono text-text-primary">~15/97 raw</span></div>
				<div class="flex justify-between"><span>Sinkhorn Ranking</span><span class="text-right font-mono text-text-primary">9/97 raw</span></div>
				<div class="flex justify-between"><span>Beam Search</span><span class="text-right font-mono text-text-primary">11/97 raw</span></div>
				<div class="flex justify-between"><span>Spectral Flow</span><span class="text-right font-mono text-text-primary">9/97 raw</span></div>
			</div>
		</div>
	</div>

	<!-- Interpretability summary -->
	<div class="mb-6 rounded-xl border border-phase-interpret/20 bg-bg-card px-5 py-5 card-elevated fade-in-up" style="animation-delay: 0.45s">
		<h3 class="mb-1 text-base font-semibold text-text-primary">The Recovered Network</h3>
		<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Structure of a trading model</p>
		<div class="grid grid-cols-3 gap-4 text-[15px] leading-relaxed text-text-secondary">
			<div>
				<span class="mb-1 block text-xs font-semibold uppercase tracking-wider text-phase-ordering">Low-Rank Factor Track</span>
				96% of trajectory variance in first 3 PCs. The 48-block trajectory through 48-D space is effectively 3-dimensional.
			</div>
			<div>
				<span class="mb-1 block text-xs font-semibold uppercase tracking-wider text-phase-e2e">Selective Amplification</span>
				Top-PC shocks amplified (1.88x), bottom-PC shocks damped (0.69x). Prediction sensitivity gap: 22x.
			</div>
			<div>
				<span class="mb-1 block text-xs font-semibold uppercase tracking-wider text-phase-interpret">Three Phases</span>
				Early blocks stabilize (delta ~0.53), middle blocks compress (~0.43), late blocks correct (~1.10). Different features at each depth.
			</div>
		</div>
	</div>

	<!-- Uniqueness -->
	<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-5 card-elevated fade-in-up" style="animation-delay: 0.5s">
		<h3 class="mb-3 text-base font-semibold text-text-primary">Local Uniqueness</h3>
		<p class="text-[15px] leading-relaxed text-text-secondary">
			All <span class="font-mono text-text-primary">2,256</span> single-swap neighbors are strictly worse. The closest competitor — a single adjacent block swap — has MSE <span class="font-mono text-text-primary">0.000042</span>, nine orders of magnitude above the solution. The exact answer is recoverable from as few as <span class="font-mono text-text-primary">500</span> of the 10,000 provided rows.
		</p>
	</div>
</div>
