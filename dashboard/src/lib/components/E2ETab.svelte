<script lang="ts">
	import E2EOverview from './E2EOverview.svelte';

	let { subtab }: { subtab: string } = $props();
</script>

{#if subtab === 'overview'}
	<E2EOverview />
{:else}
	<div class="flex items-center justify-center py-20 text-text-tertiary">
		Unknown subtab: {subtab}
	</div>
{/if}
