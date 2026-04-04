<script lang="ts">
	interface StructureData {
		sym_antisym: { diffusion_pct: number };
		traces: { all_negative: boolean; range: [number, number] };
		mean_reverting: { mean_frac_negative: number };
		factor_structure: { effective_rank: number };
		trajectory_pca: { pc1: number; pc1_2: number; pc1_3: number };
		feature_sensitivity_ratio: number;
		feature_overlap: number;
		phase_structure: { phase_means: Record<string, number> };
	}

	interface ShockData {
		top_bottom_ratio: number;
		group_summary: Record<string, { mean_damping_ratio: number; mean_abs_pred_shift: number }>;
	}

	interface ObserverData {
		best_auto_pred_mse: number;
		best_obs_pred_mse: number;
		shock_fidelity: { damping_improvement_pct: number; auto_mean_damping_gap: number; obs_mean_damping_gap: number };
	}

	let structure: StructureData | null = $state(null);
	let shock: ShockData | null = $state(null);
	let observer: ObserverData | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const [r1, r2, r3] = await Promise.all([
			fetch('/data/distillation_01_network_structure.json'),
			fetch('/data/distillation_02_shock_response.json'),
			fetch('/data/distillation_03_latent_observer.json'),
		]);
		if (r1.ok) structure = await r1.json();
		if (r2.ok) shock = await r2.json();
		if (r3.ok) observer = await r3.json();
		loaded = true;
	}
	loadAll();

	const COLORS = {
		early: '#6cb6ff',
		mid: '#3dd68c',
		late: '#f0883e',
		accent: '#d2a8ff',
		textDim: '#8690a2',
	};
</script>

{#if !loaded}
	<div class="py-12 text-center text-text-tertiary">Loading...</div>
{:else}
	<div class="space-y-6 fade-in-up">

		<!-- ── HEADLINE ────────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-xl font-semibold text-text-primary">
				What the recovered network actually does
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The pairing and ordering sections recovered the network&rsquo;s architecture.
				This section asks what computation that architecture performs. Three complementary
				analyses build up a picture: <strong>static structure</strong> (what the Jacobians
				look like), <strong>dynamic response</strong> (how the network reacts to
				perturbations), and <strong>surrogate modeling</strong> (what kind of dynamical
				system best approximates the network). Each subsection below links to a
				detailed analysis page.
			</p>
		</div>

		<!-- ── THREE-COLUMN SUMMARY STATS ─────────────────────── -->
		{#if structure && shock && observer}
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-4 card-elevated">
					<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Diffusion</div>
					<div class="mt-1 text-3xl font-bold text-phase-interpret">{structure.sym_antisym.diffusion_pct}%</div>
					<div class="mt-1 text-sm text-text-tertiary">symmetric (diffusion-like)</div>
				</div>
				<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-4 card-elevated">
					<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Selectivity</div>
					<div class="mt-1 text-3xl font-bold text-phase-interpret">{shock.top_bottom_ratio}x</div>
					<div class="mt-1 text-sm text-text-tertiary">top vs bottom PC shift</div>
				</div>
				<div class="rounded-xl border border-border-subtle bg-bg-card px-5 py-4 card-elevated">
					<div class="text-xs font-semibold uppercase tracking-wider text-text-tertiary">Observer gain</div>
					<div class="mt-1 text-3xl font-bold text-phase-interpret">{observer.shock_fidelity.damping_improvement_pct}%</div>
					<div class="mt-1 text-sm text-text-tertiary">shock fidelity improvement</div>
				</div>
			</div>
		{/if}

		<!-- ── 01 NETWORK STRUCTURE ───────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">
				<span class="mr-2 font-mono text-sm text-text-tertiary">01</span>Network Structure
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The linearized Jacobian of each block (<code class="text-xs">A&#x2096; = W_out &middot; diag(g) &middot; W_inp</code>)
				reveals what each layer does to the hidden state. Decomposing into symmetric and
				antisymmetric parts separates diffusion (smoothing) from rotation (mixing).
			</p>
			{#if structure}
				<div class="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-text-primary">{structure.sym_antisym.diffusion_pct}%</div>
						<div class="mt-1 text-xs text-text-tertiary">diffusion-dominated</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-text-primary">{structure.traces.all_negative ? '48/48' : 'partial'}</div>
						<div class="mt-1 text-xs text-text-tertiary">negative traces (contractive)</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-text-primary">{structure.factor_structure.effective_rank.toFixed(0)}</div>
						<div class="mt-1 text-xs text-text-tertiary">effective rank (of 48)</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-text-primary">{structure.trajectory_pca.pc1_3.toFixed(0)}%</div>
						<div class="mt-1 text-xs text-text-tertiary">variance in 3 PCs</div>
					</div>
				</div>
				<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
					<strong>Key finding:</strong> every block is contractive (negative trace), the dynamics are
					{structure.sym_antisym.diffusion_pct}% diffusion, and the cumulative effect collapses a
					48-D state into an effective rank-{structure.factor_structure.effective_rank.toFixed(0)} subspace.
					The 48-step trajectory is effectively 3-dimensional ({structure.trajectory_pca.pc1_3.toFixed(1)}% variance
					in 3 PCs). Three phases emerge: early blocks stabilize, middle blocks compress,
					late blocks apply {structure.feature_sensitivity_ratio.toFixed(1)}x stronger feature corrections
					along entirely disjoint feature sets.
				</p>
			{:else}
				<p class="mt-3 text-sm italic text-text-tertiary">
					Data not available. Run <code>distillation/01_network_structure.py</code>.
				</p>
			{/if}
		</div>

		<!-- ── 02 SHOCK RESPONSE ──────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">
				<span class="mr-2 font-mono text-sm text-text-tertiary">02</span>Shock Response
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Static Jacobian analysis shows the network is contractive on average, but does it
				treat all directions equally? Calibrated perturbations were injected along different
				input directions and tracked through all 48 blocks to measure the network&rsquo;s
				<em>selective</em> response.
			</p>
			{#if shock}
				<div class="mt-4 grid grid-cols-3 gap-4">
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold" style="color: {COLORS.late}">{shock.group_summary.pca_top.mean_damping_ratio.toFixed(2)}</div>
						<div class="mt-1 text-xs text-text-tertiary">top-PC damping (amplifying)</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold" style="color: {COLORS.early}">{shock.group_summary.pca_bottom.mean_damping_ratio.toFixed(2)}</div>
						<div class="mt-1 text-xs text-text-tertiary">bottom-PC damping (suppressed)</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-phase-interpret">{shock.top_bottom_ratio}x</div>
						<div class="mt-1 text-xs text-text-tertiary">prediction-shift gap</div>
					</div>
				</div>
				<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
					<strong>Key finding:</strong> the network does not treat all perturbations equally.
					Shocks along high-variance directions (top PCs, which align with factor-like signals) are
					<em>amplified</em> through depth (damping ratio {shock.group_summary.pca_top.mean_damping_ratio.toFixed(2)} &gt; 1),
					while shocks along low-variance directions (bottom PCs, noise-like) are <em>damped immediately</em>
					(ratio {shock.group_summary.pca_bottom.mean_damping_ratio.toFixed(2)} &lt; 1). The network&rsquo;s
					output is {shock.top_bottom_ratio}x more sensitive to factor-like perturbations than to noise.
					This pattern holds across all data subsets tested.
				</p>
			{:else}
				<p class="mt-3 text-sm italic text-text-tertiary">
					Data not available. Run <code>distillation/02_shock_response.py</code>.
				</p>
			{/if}
		</div>

		<!-- ── 03 LATENT OBSERVER ─────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">
				<span class="mr-2 font-mono text-sm text-text-tertiary">03</span>Latent Observer
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				Sections 01&ndash;02 describe what the network does. This section asks: what is the
				<em>simplest dynamical system</em> that reproduces that behavior? Two surrogate
				models were fitted &mdash; an autonomous latent ODE and an observer that corrects
				itself from full-state residuals &mdash; and evaluated on prediction accuracy
				and shock-response fidelity.
			</p>
			{#if observer}
				<div class="mt-4 grid grid-cols-3 gap-4">
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold" style="color: {COLORS.late}">{observer.best_auto_pred_mse.toFixed(4)}</div>
						<div class="mt-1 text-xs text-text-tertiary">autonomous pred MSE</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold" style="color: {COLORS.early}">{observer.best_obs_pred_mse.toFixed(4)}</div>
						<div class="mt-1 text-xs text-text-tertiary">observer pred MSE</div>
					</div>
					<div class="rounded-lg border border-border-subtle px-4 py-3 text-center">
						<div class="text-2xl font-bold text-phase-interpret">{observer.shock_fidelity.damping_improvement_pct}%</div>
						<div class="mt-1 text-xs text-text-tertiary">shock fidelity improvement</div>
					</div>
				</div>
				<p class="mt-4 text-[15px] leading-relaxed text-text-secondary">
					<strong>Key finding:</strong> the autonomous model approximates the trajectory but fails to
					reproduce the selective amplification behavior from Section 02. The observer surrogate
					reduces the shock-damping gap by {observer.shock_fidelity.damping_improvement_pct}%
					({observer.shock_fidelity.auto_mean_damping_gap.toFixed(4)} &rarr;
					{observer.shock_fidelity.obs_mean_damping_gap.toFixed(4)}).
					The best compact description of this network is not a low-rank autonomous ODE but
					<strong>a low-rank stable factor system with observer-like correction</strong> &mdash;
					closer to a Kalman filter than a standalone dynamical system.
				</p>
			{:else}
				<p class="mt-3 text-sm italic text-text-tertiary">
					Data not available. Run <code>distillation/03_latent_observer.py</code>.
				</p>
			{/if}
		</div>

		<!-- ── NARRATIVE ARC ──────────────────────────────────── -->
		{#if structure && shock && observer}
			<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
				<h3 class="mb-4 text-lg font-semibold text-text-primary">How the three analyses connect</h3>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					<div class="rounded-lg border border-border-subtle px-5 py-4">
						<h4 class="mb-2 text-base font-semibold text-text-primary">Structure &rarr; Shock</h4>
						<p class="text-[15px] leading-relaxed text-text-secondary">
							The Jacobian analysis reveals all-negative traces and {structure.sym_antisym.diffusion_pct}%
							diffusion &mdash; the network is contractive <em>on average</em>. But shock testing
							shows this contraction is <em>selective</em>: factor-aligned directions are amplified
							{shock.group_summary.pca_top.mean_damping_ratio.toFixed(1)}x while noise directions
							are suppressed. Average contractiveness masks directional selectivity.
						</p>
					</div>
					<div class="rounded-lg border border-border-subtle px-5 py-4">
						<h4 class="mb-2 text-base font-semibold text-text-primary">Shock &rarr; Observer</h4>
						<p class="text-[15px] leading-relaxed text-text-secondary">
							The {shock.top_bottom_ratio}x selectivity is the behavioral signature that
							distinguishes this network from a generic contractive map. An autonomous
							surrogate cannot reproduce it &mdash; it lacks the mechanism to treat
							different directions differently. The observer&rsquo;s residual correction
							provides exactly that mechanism, closing {observer.shock_fidelity.damping_improvement_pct}%
							of the fidelity gap.
						</p>
					</div>
					<div class="rounded-lg border border-border-subtle px-5 py-4">
						<h4 class="mb-2 text-base font-semibold text-text-primary">The full picture</h4>
						<p class="text-[15px] leading-relaxed text-text-secondary">
							The network implements a rank-{structure.factor_structure.effective_rank.toFixed(0)}
							factor model that selectively amplifies input signals aligned with a learned
							factor basis while damping orthogonal noise. It is not a generic smoother;
							it is a structured signal extractor. The best compact summary is an
							observer-corrected factor system, not an autonomous ODE.
						</p>
					</div>
				</div>
			</div>
		{/if}
	</div>
{/if}
