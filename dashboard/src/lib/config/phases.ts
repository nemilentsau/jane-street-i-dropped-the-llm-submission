export const phases = {
	summary:          { icon: '◆', borderClass: 'border-accent-green',     textClass: 'text-accent-green',     glowClass: 'glow-green',  placeholderBorder: 'border-accent-green/30',      placeholderHover: 'hover:border-accent-green/50'     },
	pairing:          { icon: '▦', borderClass: 'border-phase-pairing',    textClass: 'text-phase-pairing',    glowClass: 'glow-green',  placeholderBorder: 'border-phase-pairing/30',     placeholderHover: 'hover:border-phase-pairing/50'    },
	ordering:         { icon: '▲', borderClass: 'border-phase-ordering',   textClass: 'text-phase-ordering',   glowClass: 'glow-blue',   placeholderBorder: 'border-phase-ordering/30',    placeholderHover: 'hover:border-phase-ordering/50'   },
	e2e:              { icon: '▶', borderClass: 'border-phase-e2e',        textClass: 'text-phase-e2e',        glowClass: 'glow-amber',  placeholderBorder: 'border-phase-e2e/30',         placeholderHover: 'hover:border-phase-e2e/50'        },
	interpretability: { icon: '●', borderClass: 'border-phase-interpret',  textClass: 'text-phase-interpret',  glowClass: 'glow-purple', placeholderBorder: 'border-phase-interpret/30',   placeholderHover: 'hover:border-phase-interpret/50'  },
} as const;

export type PhaseId = keyof typeof phases;

export const tabs = [
	{
		id: 'summary' as const,
		label: 'Summary',
		desc: 'Reassembling a shuffled 48-block residual network from 97 linear layers',
		subtabs: [] as { id: string; label: string }[],
		hasData: true,
	},
	{
		id: 'pairing' as const,
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
		hasData: true,
	},
	{
		id: 'ordering' as const,
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
		hasData: true,
	},
	{
		id: 'e2e' as const,
		label: 'End-to-End',
		desc: 'Full pipeline demonstrations — pairing + ordering + polish',
		subtabs: [
			{ id: 'overview', label: 'Overview' },
			{ id: '01-fastest', label: '01 Fastest Solve' },
			{ id: '02-all-pairing', label: '02 All Pairing Methods' },
			{ id: '03-all-ordering', label: '03 All Ordering Methods' },
			{ id: '04-full-grid', label: '04 Full Grid' },
		],
		hasData: false,
	},
	{
		id: 'interpretability' as const,
		label: 'Interpretability',
		desc: 'What the recovered network actually does',
		subtabs: [
			{ id: 'overview', label: 'Overview' },
			{ id: '01-structure', label: '01 Network Structure' },
			{ id: '02-shock', label: '02 Shock Response' },
			{ id: '03-observer', label: '03 Latent Observer' },
		],
		hasData: false,
	},
] as const;

export type TabId = (typeof tabs)[number]['id'];
