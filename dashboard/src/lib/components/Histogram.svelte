<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer]);

	let {
		seriesA,
		seriesB,
		labelA = 'A',
		labelB = 'B',
		colorA = '#3dd68c',
		colorB = '#ee7a7a',
		title = '',
		xlabel = '',
		bins = 40,
		width = 480,
		height = 240,
	}: {
		seriesA: number[];
		seriesB: number[];
		labelA?: string;
		labelB?: string;
		colorA?: string;
		colorB?: string;
		title?: string;
		xlabel?: string;
		bins?: number;
		width?: number;
		height?: number;
	} = $props();

	let options = $derived.by(() => {
		const all = [...seriesA, ...seriesB];
		const lo = Math.min(...all);
		const hi = Math.max(...all);
		const range = hi - lo || 1;
		const binW = range / bins;

		function binify(values: number[]): number[] {
			const counts = new Array(bins).fill(0);
			for (const v of values) {
				const idx = Math.min(Math.floor((v - lo) / binW), bins - 1);
				counts[idx]++;
			}
			return counts;
		}

		const binsA = binify(seriesA);
		const binsB = binify(seriesB);
		const labels = Array.from({ length: bins }, (_, i) => (lo + (i + 0.5) * binW).toFixed(1));

		return {
			tooltip: {
				trigger: 'axis' as const,
				axisPointer: { type: 'shadow' as const },
			},
			legend: {
				data: [labelA, labelB],
				top: 0,
				right: 0,
				textStyle: { color: '#b0b8c8', fontSize: 10 },
			},
			grid: {
				top: title ? 44 : 28,
				right: 12,
				bottom: xlabel ? 36 : 16,
				left: 40,
			},
			xAxis: {
				type: 'category' as const,
				data: labels,
				name: xlabel,
				nameLocation: 'middle' as const,
				nameGap: 24,
				nameTextStyle: { color: '#8690a2', fontSize: 10 },
				axisLabel: { show: false },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#8690a2', fontSize: 10 },
				axisLine: { show: false },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			series: [
				{
					name: labelB,
					type: 'bar' as const,
					data: binsB,
					itemStyle: { color: colorB, opacity: 0.5 },
					barGap: '-100%',
				},
				{
					name: labelA,
					type: 'bar' as const,
					data: binsA,
					itemStyle: { color: colorA, opacity: 0.7 },
				},
			],
			...(title ? { title: { text: title, textStyle: { color: '#b0b8c8', fontSize: 12, fontWeight: 600 }, left: 0, top: 0 } } : {}),
			backgroundColor: 'transparent',
		};
	});
</script>

<div style="width: {width}px; height: {height}px;">
	<Chart {init} {options} theme="dark" />
</div>
