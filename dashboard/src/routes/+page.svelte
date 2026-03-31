<script lang="ts">
	import PairingWeightCorr from '$lib/components/PairingWeightCorr.svelte';

	// ── Tab / subtab definitions ─────────────────────────────────
	const tabs = [
		{
			id: 'pairing',
			label: 'Pairing',
			desc: 'Which inp goes with which out — 48! possible, 5 methods, all 48/48',
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
			desc: 'In what sequence the 48 blocks act — 5 methods, all converge after polish',
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
			desc: 'Full pipeline demonstrations — pairing + ordering + polish',
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

	let activeTab: TabId = $state('pairing');
	let activeSubtabs: Record<TabId, string> = $state({
		pairing: 'overview',
		ordering: 'overview',
		e2e: 'overview',
		interpretability: 'overview',
	});

	let currentTab = $derived(tabs.find(t => t.id === activeTab)!);
	let currentSubtab = $derived(activeSubtabs[activeTab]);

	// ── Hero KPIs ────────────────────────────────────────────────
	type KpiStatus = 'green' | 'neutral' | 'pending';
	const kpis: { label: string; value: string; detail?: string; status: KpiStatus }[] = [
		{ label: 'Final MSE', value: '3.16e-14', status: 'green' },
		{ label: 'Search Space', value: '(48!)²', detail: '≈ 10¹²¹', status: 'neutral' },
		{ label: 'Best Raw Ordering', value: '77/97', detail: 'before polish', status: 'green' },
		{ label: 'Pairing Signal', value: '23x', detail: 'correct / incorrect', status: 'green' },
	];
</script>

<div class="flex min-h-screen flex-col">
	<!-- ─── HEADER ──────────────────────────────────────────────── -->
	<header class="sticky top-0 z-50 border-b border-border-subtle bg-bg-surface px-8">
		<div class="flex items-baseline justify-between pt-4 pb-2">
			<div>
				<h1 class="font-display text-xl font-bold tracking-tight text-text-primary">I Dropped the LLM</h1>
				<p class="mt-0.5 text-[13px] text-text-secondary">Reassembling a shuffled 48-block residual network from 97 linear layers</p>
			</div>
		</div>

		<!-- KPI Summary Bar -->
		<div class="flex gap-0.5 border-b border-border-subtle py-3">
			{#each kpis as kpi}
				<div class="flex flex-1 flex-col items-center rounded-lg bg-bg-card px-3 py-2 first:rounded-l-lg last:rounded-r-lg">
					<span class="font-mono text-lg font-bold {kpi.status === 'green' ? 'text-accent-green' : kpi.status === 'pending' ? 'italic text-text-tertiary' : 'text-text-primary'}">{kpi.value}</span>
					{#if kpi.detail}
						<span class="font-mono text-[11px] text-text-tertiary">{kpi.detail}</span>
					{/if}
					<span class="mt-0.5 text-[10px] font-semibold uppercase tracking-wider text-text-secondary">{kpi.label}</span>
				</div>
			{/each}
		</div>

		<!-- Main Tabs -->
		<nav class="flex pt-1">
			{#each tabs as tab}
				<button
					class="cursor-pointer border-b-2 px-5 py-2.5 font-display text-[13px] font-semibold transition-colors
						{activeTab === tab.id
							? 'border-accent-green text-text-primary'
							: 'border-transparent text-text-secondary hover:text-text-primary'}"
					onclick={() => { activeTab = tab.id; }}
				>
					{tab.label}
				</button>
			{/each}
		</nav>
	</header>

	<!-- ─── CONTENT ─────────────────────────────────────────────── -->
	<main class="mx-auto w-full max-w-[1200px] flex-1 px-8 pt-6 pb-16">
		<!-- Tab description -->
		<div class="mb-4">
			<h2 class="text-lg font-semibold text-text-primary">{currentTab.label}</h2>
			<p class="mt-0.5 text-[13px] text-text-secondary">{currentTab.desc}</p>
		</div>

		<!-- Subtabs -->
		<nav class="mb-5 flex gap-1 overflow-x-auto rounded-lg bg-bg-card p-1">
			{#each currentTab.subtabs as sub}
				<button
					class="cursor-pointer whitespace-nowrap rounded px-3.5 py-1.5 font-display text-xs font-medium transition-colors
						{currentSubtab === sub.id
							? 'bg-bg-surface text-text-primary shadow-sm'
							: 'text-text-secondary hover:bg-bg-card-hover hover:text-text-primary'}"
					onclick={() => { activeSubtabs[activeTab] = sub.id; }}
				>
					{sub.label}
				</button>
			{/each}
		</nav>

		<!-- Content area -->
		<div class="min-h-[400px]">
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
							<span class="mt-1 text-xs text-text-secondary">Strongest signal — correct pairs on diagonal</span>
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
	</main>
</div>
