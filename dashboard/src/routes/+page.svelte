<script lang="ts">
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
	const kpis = [
		{ label: 'Final MSE', value: '3.16e-14', status: 'green' as const },
		{ label: 'Search Space', value: '(48!)²', detail: '≈ 10¹²¹', status: 'neutral' as const },
		{ label: 'Best Raw Ordering', value: '77/97', detail: 'before polish', status: 'green' as const },
		{ label: 'Pairing Signal', value: '—', detail: 'pending script run', status: 'pending' as const },
	];
</script>

<div class="shell">
	<!-- ─── HEADER ──────────────────────────────────────────────── -->
	<header class="header">
		<div class="header-top">
			<div class="brand">
				<h1 class="title">I Dropped the LLM</h1>
				<p class="subtitle">Reassembling a shuffled 48-block residual network from 97 linear layers</p>
			</div>
		</div>

		<!-- KPI Summary Bar -->
		<div class="kpi-bar">
			{#each kpis as kpi}
				<div class="kpi" class:kpi-green={kpi.status === 'green'} class:kpi-pending={kpi.status === 'pending'}>
					<span class="kpi-value mono">{kpi.value}</span>
					{#if kpi.detail}
						<span class="kpi-detail mono">{kpi.detail}</span>
					{/if}
					<span class="kpi-label">{kpi.label}</span>
				</div>
			{/each}
		</div>

		<!-- Main Tabs -->
		<nav class="tabs">
			{#each tabs as tab}
				<button
					class="tab"
					class:active={activeTab === tab.id}
					onclick={() => { activeTab = tab.id; }}
				>
					{tab.label}
				</button>
			{/each}
		</nav>
	</header>

	<!-- ─── CONTENT ─────────────────────────────────────────────── -->
	<main class="content">
		<!-- Tab description -->
		<div class="tab-header">
			<h2 class="tab-title">{currentTab.label}</h2>
			<p class="tab-desc">{currentTab.desc}</p>
		</div>

		<!-- Subtabs -->
		<nav class="subtabs">
			{#each currentTab.subtabs as sub}
				<button
					class="subtab"
					class:active={currentSubtab === sub.id}
					onclick={() => { activeSubtabs[activeTab] = sub.id; }}
				>
					{sub.label}
				</button>
			{/each}
		</nav>

		<!-- Content area -->
		<div class="panel">
			{#if activeTab === 'pairing'}
				{#if currentSubtab === 'overview'}
					<div class="placeholder-grid">
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Pairing Accuracy Comparison</span>
							<span class="placeholder-desc">Bar chart: all 5 methods at 48/48</span>
						</div>
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Method Comparison Table</span>
							<span class="placeholder-desc">Method | Accuracy | Data needed | Time</span>
						</div>
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9632;</div>
							<span class="placeholder-title">Weight Correlation Heatmap (48x48)</span>
							<span class="placeholder-desc">Strongest signal — correct pairs on diagonal</span>
						</div>
					</div>
				{:else}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9632;</div>
							<span class="placeholder-title">Cost Matrix (48x48)</span>
							<span class="placeholder-desc">Script output for {currentSubtab}</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Separation Stats</span>
							<span class="placeholder-desc">Correct vs incorrect pair scores</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9654;</div>
							<span class="placeholder-title">Script Output</span>
							<span class="placeholder-desc">Raw terminal output</span>
						</div>
					</div>
				{/if}

			{:else if activeTab === 'ordering'}
				{#if currentSubtab === 'overview'}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Ordering Comparison Table</span>
							<span class="placeholder-desc">Method | Raw positions | Polished | Raw MSE | Polished MSE</span>
						</div>
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Raw vs Polished Positions</span>
							<span class="placeholder-desc">Grouped bar chart: raw vs 97/97 polished</span>
						</div>
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9644;</div>
							<span class="placeholder-title">Stiffness by Block Position</span>
							<span class="placeholder-desc">Frobenius norm through GT ordering</span>
						</div>
					</div>
				{:else}
					<div class="placeholder-grid">
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Ordering Quality</span>
							<span class="placeholder-desc">Raw positions, MSE, convergence</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9644;</div>
							<span class="placeholder-title">Position Comparison</span>
							<span class="placeholder-desc">Found ordering vs GT ordering</span>
						</div>
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9654;</div>
							<span class="placeholder-title">Script Output</span>
							<span class="placeholder-desc">Raw terminal output for {currentSubtab}</span>
						</div>
					</div>
				{/if}

			{:else if activeTab === 'e2e'}
				{#if currentSubtab === 'overview'}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9733;</div>
							<span class="placeholder-title">Fastest Path</span>
							<span class="placeholder-desc">Weight correlation + delta greedy + polish</span>
						</div>
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9632;</div>
							<span class="placeholder-title">Pairing x Ordering Grid</span>
							<span class="placeholder-desc">Which combos reach perfect MSE</span>
						</div>
						<div class="placeholder-card tall">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Timing Breakdown</span>
							<span class="placeholder-desc">Time per stage across methods</span>
						</div>
					</div>
				{:else}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9654;</div>
							<span class="placeholder-title">Script Output</span>
							<span class="placeholder-desc">Full results for {currentSubtab}</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Results Summary</span>
							<span class="placeholder-desc">Key metrics from this run</span>
						</div>
					</div>
				{/if}

			{:else if activeTab === 'interpretability'}
				{#if currentSubtab === 'overview'}
					<div class="placeholder-grid">
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9670;</div>
							<span class="placeholder-title">Jacobian Analysis</span>
							<span class="placeholder-desc">All contractive, mean-reverting</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Phase Structure</span>
							<span class="placeholder-desc">Early stabilize, mid compress, late correct</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Shock Response</span>
							<span class="placeholder-desc">22x prediction gap: top vs bottom PCs</span>
						</div>
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9644;</div>
							<span class="placeholder-title">Trajectory PCA</span>
							<span class="placeholder-desc">48-step trajectory is effectively 3-dimensional</span>
						</div>
					</div>
				{:else if currentSubtab === '01-structure'}
					<div class="placeholder-grid">
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9670;</div>
							<span class="placeholder-title">Jacobian Traces</span>
							<span class="placeholder-desc">Per-block trace values, all negative</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Phase Delta Chart</span>
							<span class="placeholder-desc">Early (blue) / Mid (green) / Late (red)</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9644;</div>
							<span class="placeholder-title">Cumulative Operator SVs</span>
							<span class="placeholder-desc">Scree plot: factor compression</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9679;</div>
							<span class="placeholder-title">Trajectory PCA</span>
							<span class="placeholder-desc">Mean state projected onto top PCs</span>
						</div>
					</div>
				{:else if currentSubtab === '02-shock'}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Shock Response Curves</span>
							<span class="placeholder-desc">Top-PC (amplified) vs bottom-PC (damped) through depth</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9670;</div>
							<span class="placeholder-title">Damping Ratios</span>
							<span class="placeholder-desc">Per-direction damping summary</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9638;</div>
							<span class="placeholder-title">Regime Stability</span>
							<span class="placeholder-desc">Gap persists across data subsets</span>
						</div>
					</div>
				{:else}
					<div class="placeholder-grid">
						<div class="placeholder-card wide">
							<div class="placeholder-icon">&#9654;</div>
							<span class="placeholder-title">Script Output</span>
							<span class="placeholder-desc">Results for {currentSubtab}</span>
						</div>
						<div class="placeholder-card">
							<div class="placeholder-icon">&#9650;</div>
							<span class="placeholder-title">Model Comparison</span>
							<span class="placeholder-desc">Autonomous vs observer surrogate</span>
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</main>
</div>

<style>
	/* ─── Shell ──────────────────────────────────────────────── */
	.shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	/* ─── Header ─────────────────────────────────────────────── */
	.header {
		position: sticky;
		top: 0;
		z-index: 100;
		background: var(--bg-surface);
		border-bottom: 1px solid var(--border-subtle);
		padding: 0 32px;
	}

	.header-top {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		padding: 16px 0 8px;
	}

	.title {
		font-family: var(--font-display);
		font-size: 20px;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--text-primary);
	}

	.subtitle {
		font-size: 13px;
		color: var(--text-secondary);
		margin-top: 2px;
	}

	/* ─── KPI Bar ────────────────────────────────────────────── */
	.kpi-bar {
		display: flex;
		gap: 2px;
		padding: 12px 0;
		border-bottom: 1px solid var(--border-subtle);
	}

	.kpi {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 8px 12px;
		background: var(--bg-card);
		border-radius: var(--radius-md);
	}

	.kpi:first-child { border-radius: var(--radius-md) var(--radius-sm) var(--radius-sm) var(--radius-md); }
	.kpi:last-child { border-radius: var(--radius-sm) var(--radius-md) var(--radius-md) var(--radius-sm); }
	.kpi:not(:first-child):not(:last-child) { border-radius: var(--radius-sm); }

	.kpi-value {
		font-size: 18px;
		font-weight: 700;
		color: var(--text-primary);
	}

	.kpi-green .kpi-value {
		color: var(--accent-green);
	}

	.kpi-pending .kpi-value {
		color: var(--text-tertiary);
		font-style: italic;
	}

	.kpi-detail {
		font-size: 11px;
		font-weight: 400;
		color: var(--text-tertiary);
		margin-top: -2px;
	}

	.kpi-label {
		font-size: 10px;
		font-weight: 600;
		color: var(--text-secondary);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		margin-top: 2px;
	}

	/* ─── Main Tabs ──────────────────────────────────────────── */
	.tabs {
		display: flex;
		gap: 0;
		padding-top: 4px;
	}

	.tab {
		all: unset;
		cursor: pointer;
		padding: 10px 20px;
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 600;
		color: var(--text-secondary);
		border-bottom: 2px solid transparent;
		transition: color 0.15s, border-color 0.15s;
	}

	.tab:hover {
		color: var(--text-primary);
	}

	.tab.active {
		color: var(--text-primary);
		border-bottom-color: var(--accent-green);
	}

	/* ─── Content ────────────────────────────────────────────── */
	.content {
		flex: 1;
		padding: 24px 32px 64px;
		max-width: 1200px;
		width: 100%;
		margin: 0 auto;
	}

	.tab-header {
		margin-bottom: 16px;
	}

	.tab-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--text-primary);
	}

	.tab-desc {
		font-size: 13px;
		color: var(--text-secondary);
		margin-top: 2px;
	}

	/* ─── Subtabs ────────────────────────────────────────────── */
	.subtabs {
		display: flex;
		gap: 4px;
		padding: 4px;
		background: var(--bg-card);
		border-radius: var(--radius-md);
		margin-bottom: 20px;
		overflow-x: auto;
	}

	.subtab {
		all: unset;
		cursor: pointer;
		padding: 6px 14px;
		font-family: var(--font-display);
		font-size: 12px;
		font-weight: 500;
		color: var(--text-secondary);
		border-radius: var(--radius-sm);
		white-space: nowrap;
		transition: color 0.15s, background 0.15s;
	}

	.subtab:hover {
		color: var(--text-primary);
		background: var(--bg-card-hover);
	}

	.subtab.active {
		color: var(--text-primary);
		background: var(--bg-surface);
		box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
	}

	/* ─── Panel ──────────────────────────────────────────────── */
	.panel {
		min-height: 400px;
	}

	/* ─── Placeholder Grid ───────────────────────────────────── */
	.placeholder-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16px;
	}

	.placeholder-card {
		background: var(--bg-card);
		border: 1px dashed var(--border-medium);
		border-radius: var(--radius-lg);
		padding: 32px 24px;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		text-align: center;
		min-height: 180px;
		transition: border-color 0.15s, background 0.15s;
	}

	.placeholder-card:hover {
		border-color: var(--border-accent);
		background: var(--bg-card-hover);
	}

	.placeholder-card.wide {
		grid-column: span 2;
	}

	.placeholder-card.tall {
		min-height: 220px;
	}

	.placeholder-icon {
		font-size: 28px;
		color: var(--text-secondary);
		margin-bottom: 12px;
		opacity: 0.5;
	}

	.placeholder-title {
		font-size: 14px;
		font-weight: 600;
		color: var(--text-primary);
		margin-bottom: 4px;
	}

	.placeholder-desc {
		font-size: 12px;
		color: var(--text-secondary);
		max-width: 280px;
	}
</style>
