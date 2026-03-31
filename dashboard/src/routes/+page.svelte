<script lang="ts">
	import { phases, tabs, type TabId } from '$lib/config/phases';
	import SummaryTab from '$lib/components/SummaryTab.svelte';
	import PairingTab from '$lib/components/PairingTab.svelte';
	import OrderingTab from '$lib/components/OrderingTab.svelte';
	import E2ETab from '$lib/components/E2ETab.svelte';
	import InterpretTab from '$lib/components/InterpretTab.svelte';

	let activeTab: TabId = $state('summary');
	let activeSubtabs: Record<string, string> = $state({
		pairing: 'overview',
		ordering: 'overview',
		e2e: 'overview',
		interpretability: 'overview',
	});

	let currentTab = $derived(tabs.find(t => t.id === activeTab)!);
	let currentSubtab = $derived(activeSubtabs[activeTab] ?? '');
	let tabKey = $derived(`${activeTab}-${currentSubtab}`);
	let phase = $derived(phases[activeTab]);
</script>

<div class="flex h-screen overflow-hidden">
	<!-- ─── SIDEBAR ─────────────────────────────────────────────── -->
	<aside class="flex w-56 shrink-0 flex-col border-r border-border-subtle bg-bg-surface">
		<div class="px-5 pt-5 pb-4">
			<h1 class="font-display text-xl font-bold tracking-tight text-text-primary">I Dropped the LLM</h1>
			<p class="mt-1 text-[13px] leading-snug text-text-tertiary">48-block residual network<br/>97 shuffled linear layers</p>
		</div>

		<nav class="flex flex-1 flex-col gap-0.5 px-2">
			{#each tabs as tab}
				<button
					class="nav-item flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left font-display text-base font-medium cursor-pointer
						{activeTab === tab.id
							? 'bg-bg-card-hover text-text-primary nav-item-active'
							: 'text-text-secondary hover:bg-bg-card hover:text-text-primary'}"
					onclick={() => { activeTab = tab.id; }}
				>
					<span class="text-sm {activeTab === tab.id ? phases[tab.id].textClass : 'opacity-40'}">{phases[tab.id].icon}</span>
					{tab.label}
					{#if tab.hasData}
						<span class="ml-auto h-1.5 w-1.5 rounded-full bg-accent-green opacity-60"></span>
					{/if}
				</button>
			{/each}
		</nav>

		<div class="border-t border-border-subtle px-4 py-3">
			<div class="flex items-center gap-2">
				<span class="pulse-dot inline-block h-2 w-2 rounded-full bg-accent-green"></span>
				<p class="text-[13px] leading-snug text-text-tertiary">
					Verified at <span class="font-mono text-accent-green">MSE 3.16e-14</span><br/>on all 10,000 rows
				</p>
			</div>
		</div>
	</aside>

	<!-- ─── MAIN CONTENT ───────────────────────────────────────── -->
	<main class="flex flex-1 flex-col overflow-y-auto bg-dot-grid">
		{#if activeTab === 'summary'}
			{#key tabKey}
				<SummaryTab />
			{/key}
		{:else}
			<div class="flex flex-1 flex-col">
				<!-- Tab header + subtabs -->
				<div class="border-b border-border-subtle bg-bg-surface px-8 pt-5 pb-0">
					<div class="mb-3">
						<h2 class="text-xl font-semibold text-text-primary">{currentTab.label}</h2>
						<p class="mt-0.5 text-[15px] text-text-secondary">{currentTab.desc}</p>
					</div>

					{#if currentTab.subtabs.length > 0}
						<nav class="flex gap-1">
							{#each currentTab.subtabs as sub}
								<button
									class="cursor-pointer whitespace-nowrap border-b-2 px-3.5 py-2 font-display text-sm font-medium transition-colors
										{currentSubtab === sub.id
											? `${phase.borderClass} text-text-primary`
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
					{#key tabKey}
					<div class="mx-auto max-w-[1100px]">
						{#if activeTab === 'pairing'}
							<PairingTab subtab={currentSubtab} />
						{:else if activeTab === 'ordering'}
							<OrderingTab subtab={currentSubtab} />
						{:else if activeTab === 'e2e'}
							<E2ETab subtab={currentSubtab} />
						{:else if activeTab === 'interpretability'}
							<InterpretTab subtab={currentSubtab} />
						{/if}
					</div>
					{/key}
				</div>
			</div>
		{/if}
	</main>
</div>
