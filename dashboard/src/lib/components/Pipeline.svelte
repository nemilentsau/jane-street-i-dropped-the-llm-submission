<script lang="ts">
	const stages: { icon: string; label: string; value: string; borderClass: string; bgClass: string; textClass: string }[] = [
		{ icon: '?',  label: '97 Shuffled\nLayers', value: '',         borderClass: 'border-border-medium', bgClass: 'bg-bg-inset',        textClass: 'text-text-tertiary' },
		{ icon: '▦',  label: 'Pairing',             value: '48/48',    borderClass: 'border-phase-pairing/30', bgClass: 'bg-phase-pairing/5', textClass: 'text-phase-pairing' },
		{ icon: '▲',  label: 'Ordering',             value: '77/97 raw', borderClass: 'border-phase-ordering/30', bgClass: 'bg-phase-ordering/5', textClass: 'text-phase-ordering' },
		{ icon: '▶',  label: 'Polish',               value: '97/97',    borderClass: 'border-phase-e2e/30', bgClass: 'bg-phase-e2e/5',     textClass: 'text-phase-e2e' },
		{ icon: '✓', label: 'Verified',             value: 'MSE 3e-14', borderClass: 'border-accent-green/40', bgClass: 'bg-accent-green/10', textClass: 'text-accent-green' },
	];
</script>

<div class="rounded-xl border border-border-subtle bg-bg-card px-6 py-5 card-elevated">
	<h3 class="mb-4 text-[11px] font-semibold uppercase tracking-wider text-text-tertiary">Recovery Pipeline</h3>
	<div class="flex items-center gap-0">
		{#each stages as stage, i}
			{#if i > 0}
				<div class="flex-1 flex items-center justify-center px-1" style="margin-bottom: 24px;">
					<div class="h-px flex-1 bg-border-medium"></div>
					<span class="px-1 text-[10px] text-text-tertiary">&#9654;</span>
					<div class="h-px flex-1 bg-border-medium"></div>
				</div>
			{/if}
			<div class="flex flex-col items-center text-center">
				<div class="flex h-12 w-12 items-center justify-center rounded-lg border {stage.borderClass} {stage.bgClass}">
					<span class="text-lg {stage.textClass}">{stage.icon}</span>
				</div>
				<span class="mt-2 text-[10px] font-semibold {stage.textClass}">
					{#each stage.label.split('\n') as line, j}
						{#if j > 0}<br/>{/if}{line}
					{/each}
				</span>
				{#if stage.value}
					<span class="text-[10px] font-mono {i === stages.length - 1 ? stage.textClass : 'text-text-tertiary'}">{stage.value}</span>
				{/if}
			</div>
		{/each}
	</div>
</div>
