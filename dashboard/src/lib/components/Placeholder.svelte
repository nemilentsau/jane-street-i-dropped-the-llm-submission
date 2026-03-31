<script lang="ts">
	import { phases, type PhaseId } from '$lib/config/phases';

	let {
		icon = '■',
		title,
		subtitle = '',
		phase,
		colspan = 1,
		delay = 0,
	}: {
		icon?: string;
		title: string;
		subtitle?: string;
		phase: PhaseId;
		colspan?: 1 | 2;
		delay?: number;
	} = $props();

	const p = $derived(phases[phase]);
</script>

<div
	class="flex min-h-[180px] flex-col items-center justify-center rounded-xl border border-dashed bg-bg-card p-8 text-center transition-colors hover:bg-bg-card-hover card-elevated fade-in-up {colspan === 2 ? 'col-span-2' : ''} {p.placeholderBorder} {p.placeholderHover}"
	style={delay ? `animation-delay: ${delay}s` : ''}
>
	<span class="mb-3 text-3xl {p.textClass} opacity-40">{icon}</span>
	<span class="text-sm font-semibold text-text-primary">{title}</span>
	{#if subtitle}
		<span class="mt-1 text-xs text-text-secondary">{subtitle}</span>
	{/if}
</div>
