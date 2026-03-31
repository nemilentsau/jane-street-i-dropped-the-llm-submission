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
		ylabel = '',
		logScale = false,
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
		ylabel?: string;
		logScale?: boolean;
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
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
			},
			legend: {
				data: [labelA, labelB],
				top: 0,
				right: 0,
				textStyle: { color: '#b0b8c8', fontSize: 11 },
				itemWidth: 12,
				itemHeight: 8,
			},
			grid: {
				top: title ? 44 : 28,
				right: 12,
				bottom: xlabel ? 52 : 24,
				left: ylabel ? 60 : 44,
			},
			xAxis: {
				type: 'category' as const,
				data: labels,
				name: xlabel,
				nameLocation: 'middle' as const,
				nameGap: 36,
				nameTextStyle: { color: '#b0b8c8', fontSize: 13, fontFamily: 'Instrument Sans' },
				axisLabel: {
					show: true,
					color: '#8690a2',
					fontSize: 10,
					interval: Math.max(1, Math.floor(bins / 6) - 1),
					rotate: 0,
				},
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: logScale ? ('log' as const) : ('value' as const),
				min: logScale ? 1 : undefined,
				name: ylabel,
				nameLocation: 'middle' as const,
				nameGap: ylabel ? 42 : 0,
				nameTextStyle: { color: '#b0b8c8', fontSize: 13, fontFamily: 'Instrument Sans' },
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
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
