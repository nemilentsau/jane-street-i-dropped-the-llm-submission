<script lang="ts">
	interface G01Data {
		model: string;
		n_layers: number;
		test1_qk_ratio: number;
		test1_hungarian_correct: number;
		test1_hungarian_total: number;
		test1_missed_layers: number[];
		test3_late_middle_ratio: number;
		test4_ratio: number;
	}

	interface G02Fingerprint {
		ratio: number;
		hungarian: number;
		total: number;
	}

	interface G02Data {
		model: string;
		n_layers: number;
		n_attn_layers: number;
		n_delta_layers: number;
		test1_fingerprint: Record<string, G02Fingerprint>;
		test3_late_middle_ratio: number;
		test4_spectral_ratio: number;
	}

	let g01: G01Data | null = $state(null);
	let g02: G02Data | null = $state(null);
	let loaded = $state(false);

	async function loadAll() {
		const [r1, r2] = await Promise.all([
			fetch('/data/generalization_g01_qwen3.json'),
			fetch('/data/generalization_g02_qwen35.json'),
		]);
		if (r1.ok) g01 = await r1.json();
		if (r2.ok) g02 = await r2.json();
		loaded = true;
	}
	loadAll();

	const COLORS = {
		puzzle: '#3dd68c',
		qwen3: '#6cb6ff',
		qwen35: '#d2a8ff',
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
				Beyond the puzzle: do these techniques generalize?
			</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				The pairing fingerprint and phase-structure analyses developed for this 48-block
				residual network rely on a specific mechanism: <strong>co-training fingerprints</strong>
				left by shared gradient flow through bilinear couplings. These experiments test whether
				that mechanism transfers to other architectures. Two preliminary experiments on
				billion-parameter language models show a mixed answer: strong in some couplings, weak
				or absent in others.
			</p>
		</div>

		<!-- ── COMPARISON TABLE ────────────────────────────────── -->
		{#if g01 && g02}
			<div class="rounded-xl border border-border-subtle bg-bg-card p-5 card-elevated">
				<h3 class="mb-1 text-lg font-semibold text-text-primary">Three architectures, mixed-strength fingerprints</h3>
				<p class="mb-4 text-sm text-text-tertiary">
					The Frobenius inner product <code class="text-xs">|tr(W&#x2090;&#x1d40; W&#x2091;)|</code>
					was computed for every pair of projection matrices, then the Hungarian algorithm
					attempted to recover correct layer pairings from shuffled weights alone. The puzzle
					is exact, Qwen3 attention is strong but incomplete, and Qwen3.5 splits cleanly by
					coupling type.
				</p>
				<div class="overflow-x-auto">
					<table class="w-full text-left text-[15px]">
						<thead>
							<tr class="border-b border-border-subtle">
								<th class="pb-3 pr-4 text-xs font-semibold uppercase tracking-wider text-text-tertiary">Property</th>
								<th class="pb-3 pr-4 text-center text-xs font-semibold uppercase tracking-wider" style="color: {COLORS.puzzle}">Puzzle (48-block ResNet)</th>
								<th class="pb-3 pr-4 text-center text-xs font-semibold uppercase tracking-wider" style="color: {COLORS.qwen3}">{g01.model}</th>
								<th class="pb-3 text-center text-xs font-semibold uppercase tracking-wider" style="color: {COLORS.qwen35}">{g02.model}</th>
							</tr>
						</thead>
						<tbody>
							<tr class="border-b border-border-subtle/50 bg-bg-inset/30">
								<td class="py-3 pr-4 text-sm text-text-secondary">Architecture</td>
								<td class="py-3 pr-4 text-center text-sm text-text-secondary">48-block residual</td>
								<td class="py-3 pr-4 text-center text-sm text-text-secondary">{g01.n_layers}L transformer</td>
								<td class="py-3 text-center text-sm text-text-secondary">{g02.n_layers}L hybrid (DeltaNet + attn)</td>
							</tr>
							<tr class="border-b border-border-subtle/50">
								<td class="py-3 pr-4 text-sm text-text-secondary">Bilinear coupling</td>
								<td class="py-3 pr-4 text-center text-sm text-text-secondary">W_out &middot; W_inp</td>
								<td class="py-3 pr-4 text-center text-sm text-text-secondary">Q &middot; K</td>
								<td class="py-3 text-center text-sm text-text-secondary">Q &middot; K, alpha &middot; beta</td>
							</tr>
							<tr class="border-b border-border-subtle/50 bg-bg-inset/30">
								<td class="py-3 pr-4 text-sm text-text-secondary">Fingerprint SNR</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.puzzle}">23x</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.qwen3}">{g01.test1_qk_ratio}x</td>
								<td class="py-3 text-center font-mono text-sm" style="color: {COLORS.qwen35}">
									{g02.test1_fingerprint.attn_qk.ratio.toFixed(1)}x / {g02.test1_fingerprint.delta_ab.ratio.toFixed(1)}x
								</td>
							</tr>
							<tr class="border-b border-border-subtle/50">
								<td class="py-3 pr-4 text-sm text-text-secondary">Shuffle &amp; recover</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.puzzle}">48/48 (100%)</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.qwen3}">{g01.test1_hungarian_correct}/{g01.test1_hungarian_total} ({(g01.test1_hungarian_correct / g01.test1_hungarian_total * 100).toFixed(0)}%)</td>
								<td class="py-3 text-center font-mono text-sm" style="color: {COLORS.qwen35}">
									{g02.test1_fingerprint.attn_qk.hungarian}/{g02.test1_fingerprint.attn_qk.total},
									{g02.test1_fingerprint.delta_ab.hungarian}/{g02.test1_fingerprint.delta_ab.total}
								</td>
							</tr>
							<tr class="border-b border-border-subtle/50 bg-bg-inset/30">
								<td class="py-3 pr-4 text-sm text-text-secondary">Phase structure (late/mid)</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.puzzle}">2.6x</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.qwen3}">{g01.test3_late_middle_ratio}x</td>
								<td class="py-3 text-center font-mono text-sm" style="color: {COLORS.qwen35}">{g02.test3_late_middle_ratio}x</td>
							</tr>
							<tr class="border-b border-border-subtle/50">
								<td class="py-3 pr-4 text-sm text-text-secondary">Spectral concentration</td>
								<td class="py-3 pr-4 text-center text-sm text-text-tertiary">&mdash;</td>
								<td class="py-3 pr-4 text-center font-mono text-sm" style="color: {COLORS.qwen3}">{g01.test4_ratio}x vs random</td>
								<td class="py-3 text-center font-mono text-sm" style="color: {COLORS.qwen35}">{g02.test4_spectral_ratio}x vs random</td>
							</tr>
							<tr>
								<td class="py-3 pr-4 text-sm text-text-secondary">MLP fingerprint</td>
								<td class="py-3 pr-4 text-center text-sm text-text-tertiary">N/A</td>
								<td class="py-3 pr-4 text-center text-sm text-text-tertiary">none (0/28)</td>
								<td class="py-3 text-center text-sm text-text-tertiary">none (0/24)</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		{/if}

		<!-- ── KEY FINDINGS ───────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-4 text-lg font-semibold text-text-primary">What generalizes and what does not</h3>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
				<div class="rounded-lg border border-accent-green/30 px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-accent-green">Generalizes</h4>
					<ul class="space-y-2 text-[15px] leading-relaxed text-text-secondary">
						<li>
							<strong>Co-training fingerprint, sometimes.</strong> The Frobenius inner product
							works exactly on the puzzle, exactly on Qwen3.5 DeltaNet alpha-beta, and strongly
							but not perfectly on Qwen3 attention (24/28). Tight bilinear couplings can leave
							recoverable fingerprints in weight space.
						</li>
						<li>
							<strong>Phase structure.</strong> Late layers make larger corrections than middle
							layers across all three architectures. The pattern is architectural, not task-specific.
						</li>
						<li>
							<strong>Spectral concentration.</strong> Trained weights have 2.75&ndash;3.26x more
							top-singular-value concentration than random matrices of the same shape.
						</li>
					</ul>
				</div>
				<div class="rounded-lg border border-border-subtle px-5 py-4">
					<h4 class="mb-2 text-base font-semibold text-text-tertiary">Does not generalize</h4>
					<ul class="space-y-2 text-[15px] leading-relaxed text-text-secondary">
						<li>
							<strong>Effective rank collapse.</strong> The puzzle network collapses from rank 47
							to 9 through depth. LLMs maintain near-full rank (~800&ndash;1300) because they
							serve diverse tasks requiring broad representational capacity.
						</li>
						<li>
							<strong>MLP fingerprint.</strong> Gate-down and up-down MLP projection pairs show
							no detectable co-training fingerprint (ratio &asymp; 1x). The elementwise multiplication
							coupling in MLPs is too diffuse to create the coordinated weight structure.
						</li>
					</ul>
				</div>
			</div>
		</div>

		<!-- ── NOVEL FINDING ──────────────────────────────────── -->
		{#if g02}
			<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
				<h3 class="mb-3 text-lg font-semibold text-text-primary">Novel: DeltaNet fingerprint</h3>
				<p class="text-[15px] leading-relaxed text-text-secondary">
					Qwen3.5-2B uses a hybrid architecture alternating Gated DeltaNet (linear attention)
					with standard softmax attention in a repeating pattern. The alpha and beta projections
					in DeltaNet interact through the state update rule &mdash; a bilinear coupling analogous
					to Q-K in standard attention. This produces a {g02.test1_fingerprint.delta_ab.ratio.toFixed(1)}x
					fingerprint SNR and <strong>{g02.test1_fingerprint.delta_ab.hungarian}/{g02.test1_fingerprint.delta_ab.total}
					perfect recovery</strong> from shuffled weights. This fingerprint was not known before
					and could not have been predicted without testing &mdash; the DeltaNet coupling is
					structurally different from the attention dot product.
				</p>
			</div>
		{/if}

		<!-- ── TEASER ─────────────────────────────────────────── -->
		<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
			<h3 class="mb-3 text-lg font-semibold text-text-primary">What comes next</h3>
			<p class="text-[15px] leading-relaxed text-text-secondary">
				These are preliminary experiments on two models. A systematic study would test
				the fingerprint across model families (LLaMA, Mistral, GPT-style), scales
				(125M to 70B+), and training regimes (pre-training, fine-tuning, distillation).
				The {g01 ? g01.test1_missed_layers.length : 4} missed layers in Qwen3 are also
				interesting &mdash; "weak-fingerprint" layers may be more generic or interchangeable,
				which could inform layer pruning and model merging strategies.
			</p>
			<p class="mt-3 text-[15px] leading-relaxed text-text-secondary">
				The current evidence supports a narrower working hypothesis: <strong>some architectures
				with tight bilinear projection couplings exhibit recoverable co-training fingerprints in
				their weight matrices.</strong> Coupling type appears to matter; bilinear structure alone
				is not sufficient.
			</p>
		</div>

	</div>
{/if}
