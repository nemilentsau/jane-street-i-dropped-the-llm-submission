<script lang="ts">
	import PairingWeightCorr from '$lib/components/PairingWeightCorr.svelte';

	// ── Tab / subtab definitions ─────────────────────────────────
	const tabs = [
		{
			id: 'summary',
			label: 'Summary',
			icon: '&#9670;',
			desc: 'Reassembling a shuffled 48-block residual network from 97 linear layers',
			subtabs: [],
		},
		{
			id: 'pairing',
			label: 'Pairing',
			icon: '&#9638;',
			desc: 'Which inp goes with which out -- 48! possible, 5 methods, all 48/48',
			subtabs: [
				{ id: 'overview', label: 'Overview' },
				{ id: '01-weight-corr', label: '01 Weight Correlation' },
				{ id: '02-operator-moments', label: '02 Operator Moments' },
				{ id: '03-svd-alignment', label: '03 SVD Alignment' },
				{ id: '04-affine-linear', label: '04 Affine Linearization' },
				{ id: '05-multiview', label: '05 Multi-View Fusion' },
			],
		},
		{
			id: 'ordering',
			label: 'Ordering',
			icon: '&#9650;',
			desc: 'In what sequence the 48 blocks act -- 5 methods, all converge after polish',
			subtabs: [
				{ id: 'overview', label: 'Overview' },
				{ id: '01-delta-greedy', label: '01 Delta Greedy' },
				{ id: '02-pairwise', label: '02 Pairwise Tournament' },
				{ id: '03-sinkhorn', label: '03 Sinkhorn Ranking' },
				{ id: '04-beam-search', label: '04 Beam Search' },
				{ id: '05-spectral-flow', label: '05 Spectral Flow' },
			],
		},
		{
			id: 'e2e',
			label: 'End-to-End',
			icon: '&#9654;',
			desc: 'Full pipeline demonstrations -- pairing + ordering + polish',
			subtabs: [
				{ id: 'overview', label: 'Overview' },
				{ id: '01-fastest', label: '01 Fastest Solve' },
				{ id: '02-all-pairing', label: '02 All Pairing Methods' },
				{ id: '03-all-ordering', label: '03 All Ordering Methods' },
				{ id: '04-full-grid', label: '04 Full Grid' },
			],
		},
		{
			id: 'interpretability',
			label: 'Interpretability',
			icon: '&#9679;',
			desc: 'What the recovered network actually does',
			subtabs: [
				{ id: 'overview', label: 'Overview' },
				{ id: '01-structure', label: '01 Network Structure' },
				{ id: '02-shock', label: '02 Shock Response' },
				{ id: '03-observer', label: '03 Latent Observer' },
			],
		},
	] as const;

	type TabId = (typeof tabs)[number]['id'];

	let activeTab: TabId = $state('summary');
	let activeSubtabs: Record<string, string> = $state({
		pairing: 'overview',
		ordering: 'overview',
		e2e: 'overview',
		interpretability: 'overview',
	});

	let currentTab = $derived(tabs.find(t => t.id === activeTab)!);
	let currentSubtab = $derived(activeSubtabs[activeTab] ?? '');
</script>

<div class="flex h-screen overflow-hidden">
	<!-- ─── SIDEBAR ─────────────────────────────────────────────── -->
	<aside class="flex w-52 shrink-0 flex-col border-r border-border-subtle bg-bg-surface">
		<div class="px-5 pt-5 pb-4">
			<h1 class="font-display text-[15px] font-bold tracking-tight text-text-primary">I Dropped the LLM</h1>
			<p class="mt-0.5 text-[10px] leading-snug text-text-tertiary">48-block residual network<br/>97 shuffled linear layers</p>
		</div>

		<nav class="flex flex-1 flex-col gap-0.5 px-2">
			{#each tabs as tab}
				<button
					class="flex items-center gap-2.5 rounded-lg px-3 py-2 text-left font-display text-[13px] font-medium transition-colors cursor-pointer
						{activeTab === tab.id
							? 'bg-bg-card-hover text-text-primary'
							: 'text-text-secondary hover:bg-bg-card hover:text-text-primary'}"
					onclick={() => { activeTab = tab.id; }}
				>
					<span class="text-[11px] opacity-60">{@html tab.icon}</span>
					{tab.label}
				</button>
			{/each}
		</nav>

		<div class="border-t border-border-subtle px-4 py-3">
			<p class="text-[10px] leading-snug text-text-tertiary">
				Verified at <span class="font-mono text-accent-green">MSE 3.16e-14</span><br/>on all 10,000 rows
			</p>
		</div>
	</aside>

	<!-- ─── MAIN CONTENT ───────────────────────────────────────── -->
	<main class="flex flex-1 flex-col overflow-y-auto">
		{#if activeTab === 'summary'}
			<!-- ══════ SUMMARY TAB ══════ -->
			<div class="mx-auto w-full max-w-[960px] px-8 pt-8 pb-16">
				<!-- Hero -->
				<div class="mb-8">
					<h2 class="font-display text-2xl font-bold tracking-tight text-text-primary">Reassembling a Dropped Trading Model</h2>
					<p class="mt-2 max-w-[680px] text-[13px] leading-relaxed text-text-secondary">
						A residual neural network used for trading fell apart into 97 shuffled linear layers.
						The search space is <span class="font-mono text-text-primary">(48!)&sup2; &approx; 10&sup1;&sup2;&sup1;</span>.
						The recovered answer is verified at <span class="font-mono text-accent-green">MSE = 3.16e-14</span>.
					</p>
				</div>

				<!-- Key metrics -->
				<div class="mb-8 grid grid-cols-4 gap-3">
					<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-4 text-center">
						<span class="font-mono text-2xl font-bold text-accent-green">3.16e-14</span>
						<span class="mt-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">Final MSE</span>
					</div>
					<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-4 text-center">
						<span class="font-mono text-2xl font-bold text-text-primary">(48!)&sup2;</span>
						<span class="mt-0.5 block font-mono text-[11px] text-text-tertiary">&approx; 10&sup1;&sup2;&sup1;</span>
						<span class="mt-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">Search Space</span>
					</div>
					<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-4 text-center">
						<span class="font-mono text-2xl font-bold text-accent-green">77/97</span>
						<span class="mt-0.5 block font-mono text-[11px] text-text-tertiary">before polish</span>
						<span class="mt-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">Best Raw Ordering</span>
					</div>
					<div class="rounded-lg border border-border-subtle bg-bg-card px-4 py-4 text-center">
						<span class="font-mono text-2xl font-bold text-accent-green">23x</span>
						<span class="mt-0.5 block font-mono text-[11px] text-text-tertiary">correct / incorrect</span>
						<span class="mt-1 block text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">Pairing Signal</span>
					</div>
				</div>

				<!-- Architecture -->
				<div class="mb-8 rounded-xl border border-border-subtle bg-bg-card px-6 py-5">
					<h3 class="mb-3 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">Architecture</h3>
					<code class="block rounded bg-bg-inset px-4 py-3 font-mono text-[13px] leading-relaxed text-accent-cyan">
						x &rarr; x + W_out(ReLU(W_inp &middot; x + b_inp)) + b_out
					</code>
					<p class="mt-3 text-[13px] leading-relaxed text-text-secondary">
						48 residual blocks, each with an <span class="font-mono text-text-primary">inp</span> layer (R&sup4;&sup8; &rarr; R&sup9;&sup6;) and an <span class="font-mono text-text-primary">out</span> layer (R&sup9;&sup6; &rarr; R&sup4;&sup8;), plus one final linear readout.
						The puzzle factorizes into two independent inverse problems.
					</p>
				</div>

				<!-- Two propositions -->
				<div class="mb-6 grid grid-cols-2 gap-4">
					<!-- Pairing -->
					<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-5">
						<h3 class="mb-1 text-sm font-semibold text-text-primary">Pairing: Weight Correlation</h3>
						<p class="mb-3 text-[10px] font-semibold uppercase tracking-wider text-accent-green">All 5 methods &rarr; 48/48</p>
						<p class="mb-3 text-[13px] leading-relaxed text-text-secondary">
							Each block's <span class="font-mono text-text-primary">inp</span> and <span class="font-mono text-text-primary">out</span> share a 96-D internal space. Backpropagation leaves an algebraic co-training fingerprint:
							<code class="rounded bg-bg-inset px-1.5 py-px font-mono text-xs text-accent-cyan">|tr(W_out &middot; W_inp)|</code>
							scores correct pairs 23x higher than incorrect ones. Clean separation -- no data needed.
						</p>
						<div class="space-y-1.5 text-[12px] text-text-secondary">
							<div class="flex justify-between"><span>Weight Correlation</span><span class="font-mono text-accent-green">48/48</span></div>
							<div class="flex justify-between"><span>Operator Moments</span><span class="font-mono text-accent-green">48/48</span></div>
							<div class="flex justify-between"><span>SVD Cross-Alignment</span><span class="font-mono text-accent-green">48/48</span></div>
							<div class="flex justify-between"><span>Affine Linearization</span><span class="font-mono text-accent-green">48/48</span></div>
							<div class="flex justify-between"><span>Multi-View Fusion</span><span class="font-mono text-accent-green">48/48</span></div>
						</div>
					</div>

					<!-- Ordering -->
					<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-5">
						<h3 class="mb-1 text-sm font-semibold text-text-primary">Ordering: Land Near, Then Polish</h3>
						<p class="mb-3 text-[10px] font-semibold uppercase tracking-wider text-accent-green">All methods &rarr; exact after polish</p>
						<p class="mb-3 text-[13px] leading-relaxed text-text-secondary">
							No raw ordering method recovers the exact sequence. Every successful one lands close enough that greedy pairwise swap polish (try every swap, keep improvements, repeat) finishes the job in 2-5 iterations.
						</p>
						<div class="space-y-1.5 text-[12px] text-text-secondary">
							<div class="flex justify-between"><span>Delta Greedy</span><span class="font-mono text-text-primary">77/97 raw</span></div>
							<div class="flex justify-between"><span>Pairwise Tournament</span><span class="font-mono text-text-primary">exact after polish</span></div>
							<div class="flex justify-between"><span>Sinkhorn Ranking</span><span class="font-mono text-text-primary">9/97 raw</span></div>
							<div class="flex justify-between"><span>Beam Search</span><span class="font-mono text-text-primary">11/97 raw</span></div>
							<div class="flex justify-between"><span>Spectral Flow</span><span class="font-mono text-text-primary">9/97 raw</span></div>
						</div>
					</div>
				</div>

				<!-- Interpretability summary -->
				<div class="mb-6 rounded-xl border border-border-subtle bg-bg-card px-5 py-5">
					<h3 class="mb-1 text-sm font-semibold text-text-primary">The Recovered Network</h3>
					<p class="mb-3 text-[10px] font-semibold uppercase tracking-wider text-text-tertiary">Structure of a trading model</p>
					<div class="grid grid-cols-3 gap-4 text-[13px] leading-relaxed text-text-secondary">
						<div>
							<span class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-accent-blue">Low-Rank Factor Track</span>
							96% of trajectory variance in first 3 PCs. The 48-block trajectory through 48-D space is effectively 3-dimensional.
						</div>
						<div>
							<span class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-accent-amber">Selective Amplification</span>
							Top-PC shocks amplified (1.88x), bottom-PC shocks damped (0.69x). Prediction sensitivity gap: 22x.
						</div>
						<div>
							<span class="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-accent-purple">Three Phases</span>
							Early blocks stabilize (delta ~0.53), middle blocks compress (~0.43), late blocks correct (~1.10). Different features at each depth.
						</div>
					</div>
				</div>

				<!-- Uniqueness -->
				<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-5">
					<h3 class="mb-3 text-sm font-semibold text-text-primary">Local Uniqueness</h3>
					<p class="text-[13px] leading-relaxed text-text-secondary">
						All <span class="font-mono text-text-primary">2,256</span> single-swap neighbors are strictly worse. The closest competitor -- a single adjacent block swap -- has MSE <span class="font-mono text-text-primary">0.000042</span>, nine orders of magnitude above the solution. The exact answer is recoverable from as few as <span class="font-mono text-text-primary">500</span> of the 10,000 provided rows.
					</p>
				</div>
			</div>

		{:else}
			<!-- ══════ DATA TABS ══════ -->
			<div class="flex flex-1 flex-col">
				<!-- Tab header + subtabs -->
				<div class="border-b border-border-subtle bg-bg-surface px-8 pt-5 pb-0">
					<div class="mb-3">
						<h2 class="text-lg font-semibold text-text-primary">{currentTab.label}</h2>
						<p class="mt-0.5 text-[13px] text-text-secondary">{currentTab.desc}</p>
					</div>

					{#if currentTab.subtabs.length > 0}
						<nav class="flex gap-1">
							{#each currentTab.subtabs as sub}
								<button
									class="cursor-pointer whitespace-nowrap border-b-2 px-3.5 py-2 font-display text-xs font-medium transition-colors
										{currentSubtab === sub.id
											? 'border-accent-green text-text-primary'
											: 'border-transparent text-text-secondary hover:text-text-primary'}"
									onclick={() => { activeSubtabs[activeTab] = sub.id; }}
								>
									{sub.label}
								</button>
							{/each}
						</nav>
					{/if}
				</div>

				<!-- Content area -->
				<div class="flex-1 overflow-y-auto px-8 pt-6 pb-16">
					<div class="mx-auto max-w-[1100px]">
						{#if activeTab === 'pairing'}
							{#if currentSubtab === 'overview'}
								<div class="grid grid-cols-2 gap-4">
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Pairing Accuracy Comparison</span>
										<span class="mt-1 text-xs text-text-secondary">Bar chart: all 5 methods at 48/48</span>
									</div>
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Method Comparison Table</span>
										<span class="mt-1 text-xs text-text-secondary">Method | Accuracy | Data needed | Time</span>
									</div>
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9632;</span>
										<span class="text-sm font-semibold text-text-primary">Weight Correlation Heatmap (48x48)</span>
										<span class="mt-1 text-xs text-text-secondary">Strongest signal -- correct pairs on diagonal</span>
									</div>
								</div>
							{:else if currentSubtab === '01-weight-corr'}
								<PairingWeightCorr />
							{:else}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9632;</span>
										<span class="text-sm font-semibold text-text-primary">Cost Matrix (48x48)</span>
										<span class="mt-1 text-xs text-text-secondary">Script output for {currentSubtab}</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Separation Stats</span>
										<span class="mt-1 text-xs text-text-secondary">Correct vs incorrect pair scores</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9654;</span>
										<span class="text-sm font-semibold text-text-primary">Script Output</span>
										<span class="mt-1 text-xs text-text-secondary">Raw terminal output</span>
									</div>
								</div>
							{/if}

						{:else if activeTab === 'ordering'}
							{#if currentSubtab === 'overview'}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Ordering Comparison Table</span>
										<span class="mt-1 text-xs text-text-secondary">Method | Raw positions | Polished | Raw MSE | Polished MSE</span>
									</div>
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Raw vs Polished Positions</span>
										<span class="mt-1 text-xs text-text-secondary">Grouped bar chart: raw vs 97/97 polished</span>
									</div>
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9644;</span>
										<span class="text-sm font-semibold text-text-primary">Stiffness by Block Position</span>
										<span class="mt-1 text-xs text-text-secondary">Frobenius norm through GT ordering</span>
									</div>
								</div>
							{:else}
								<div class="grid grid-cols-2 gap-4">
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Ordering Quality</span>
										<span class="mt-1 text-xs text-text-secondary">Raw positions, MSE, convergence</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9644;</span>
										<span class="text-sm font-semibold text-text-primary">Position Comparison</span>
										<span class="mt-1 text-xs text-text-secondary">Found ordering vs GT ordering</span>
									</div>
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9654;</span>
										<span class="text-sm font-semibold text-text-primary">Script Output</span>
										<span class="mt-1 text-xs text-text-secondary">Raw terminal output for {currentSubtab}</span>
									</div>
								</div>
							{/if}

						{:else if activeTab === 'e2e'}
							{#if currentSubtab === 'overview'}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9733;</span>
										<span class="text-sm font-semibold text-text-primary">Fastest Path</span>
										<span class="mt-1 text-xs text-text-secondary">Weight correlation + delta greedy + polish</span>
									</div>
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9632;</span>
										<span class="text-sm font-semibold text-text-primary">Pairing x Ordering Grid</span>
										<span class="mt-1 text-xs text-text-secondary">Which combos reach perfect MSE</span>
									</div>
									<div class="flex min-h-[220px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Timing Breakdown</span>
										<span class="mt-1 text-xs text-text-secondary">Time per stage across methods</span>
									</div>
								</div>
							{:else}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9654;</span>
										<span class="text-sm font-semibold text-text-primary">Script Output</span>
										<span class="mt-1 text-xs text-text-secondary">Full results for {currentSubtab}</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Results Summary</span>
										<span class="mt-1 text-xs text-text-secondary">Key metrics from this run</span>
									</div>
								</div>
							{/if}

						{:else if activeTab === 'interpretability'}
							{#if currentSubtab === 'overview'}
								<div class="grid grid-cols-2 gap-4">
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9670;</span>
										<span class="text-sm font-semibold text-text-primary">Jacobian Analysis</span>
										<span class="mt-1 text-xs text-text-secondary">All contractive, mean-reverting</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Phase Structure</span>
										<span class="mt-1 text-xs text-text-secondary">Early stabilize, mid compress, late correct</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Shock Response</span>
										<span class="mt-1 text-xs text-text-secondary">22x prediction gap: top vs bottom PCs</span>
									</div>
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9644;</span>
										<span class="text-sm font-semibold text-text-primary">Trajectory PCA</span>
										<span class="mt-1 text-xs text-text-secondary">48-step trajectory is effectively 3-dimensional</span>
									</div>
								</div>
							{:else if currentSubtab === '01-structure'}
								<div class="grid grid-cols-2 gap-4">
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9670;</span>
										<span class="text-sm font-semibold text-text-primary">Jacobian Traces</span>
										<span class="mt-1 text-xs text-text-secondary">Per-block trace values, all negative</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Phase Delta Chart</span>
										<span class="mt-1 text-xs text-text-secondary">Early (blue) / Mid (green) / Late (red)</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9644;</span>
										<span class="text-sm font-semibold text-text-primary">Cumulative Operator SVs</span>
										<span class="mt-1 text-xs text-text-secondary">Scree plot: factor compression</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9679;</span>
										<span class="text-sm font-semibold text-text-primary">Trajectory PCA</span>
										<span class="mt-1 text-xs text-text-secondary">Mean state projected onto top PCs</span>
									</div>
								</div>
							{:else if currentSubtab === '02-shock'}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Shock Response Curves</span>
										<span class="mt-1 text-xs text-text-secondary">Top-PC (amplified) vs bottom-PC (damped) through depth</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9670;</span>
										<span class="text-sm font-semibold text-text-primary">Damping Ratios</span>
										<span class="mt-1 text-xs text-text-secondary">Per-direction damping summary</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9638;</span>
										<span class="text-sm font-semibold text-text-primary">Regime Stability</span>
										<span class="mt-1 text-xs text-text-secondary">Gap persists across data subsets</span>
									</div>
								</div>
							{:else}
								<div class="grid grid-cols-2 gap-4">
									<div class="col-span-2 flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9654;</span>
										<span class="text-sm font-semibold text-text-primary">Script Output</span>
										<span class="mt-1 text-xs text-text-secondary">Results for {currentSubtab}</span>
									</div>
									<div class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed border-border-medium bg-bg-card p-8 text-center transition-colors hover:border-border-accent hover:bg-bg-card-hover">
										<span class="mb-3 text-3xl text-text-secondary opacity-50">&#9650;</span>
										<span class="text-sm font-semibold text-text-primary">Model Comparison</span>
										<span class="mt-1 text-xs text-text-secondary">Autonomous vs observer surrogate</span>
									</div>
								</div>
							{/if}
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</main>
</div>
