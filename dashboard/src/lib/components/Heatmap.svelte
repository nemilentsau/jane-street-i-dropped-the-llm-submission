<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { HeatmapChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, VisualMapComponent, GridComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([HeatmapChart, TooltipComponent, VisualMapComponent, GridComponent, CanvasRenderer]);

	let {
		data,
		title = '',
		width = 420,
		height = 420,
		xlabel = '',
		ylabel = '',
	}: {
		data: number[][];
		title?: string;
		width?: number;
		height?: number;
		xlabel?: string;
		ylabel?: string;
	} = $props();

	let options = $derived.by(() => {
		const flat: [number, number, number][] = [];
		let vmin = Infinity, vmax = -Infinity;
		for (let i = 0; i < data.length; i++) {
			for (let j = 0; j < data[i].length; j++) {
				const v = data[i][j];
				flat.push([j, i, v]);
				if (v < vmin) vmin = v;
				if (v > vmax) vmax = v;
			}
		}

		return {
			tooltip: {
				formatter: (p: any) => `(${p.value[1]}, ${p.value[0]}): ${p.value[2].toFixed(3)}`,
			},
			grid: {
				top: title ? 32 : 8,
				right: 60,
				bottom: xlabel ? 36 : 16,
				left: ylabel ? 44 : 16,
			},
			xAxis: {
				type: 'category' as const,
				data: Array.from({ length: data[0]?.length ?? 0 }, (_, i) => i),
				name: xlabel,
				nameLocation: 'middle' as const,
				nameGap: 24,
				nameTextStyle: { color: '#8690a2', fontSize: 10 },
				axisLabel: { show: false },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { show: false },
			},
			yAxis: {
				type: 'category' as const,
				data: Array.from({ length: data.length }, (_, i) => i),
				name: ylabel,
				nameLocation: 'middle' as const,
				nameGap: 32,
				nameTextStyle: { color: '#8690a2', fontSize: 10 },
				axisLabel: { show: false },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
				splitLine: { show: false },
				inverse: true,
			},
			visualMap: {
				min: vmin,
				max: vmax,
				calculable: false,
				orient: 'vertical' as const,
				right: 0,
				top: 'center' as const,
				itemHeight: 200,
				inRange: {
					color: ['#0d1117', '#1a5276', '#2dd4bf', '#fbbf24'],
				},
				textStyle: { color: '#8690a2', fontSize: 10 },
			},
			series: [{
				type: 'heatmap' as const,
				data: flat,
				emphasis: {
					itemStyle: { borderColor: '#eceff4', borderWidth: 1 },
				},
			}],
			...(title ? { title: { text: title, textStyle: { color: '#b0b8c8', fontSize: 12, fontWeight: 600 }, left: 0, top: 0 } } : {}),
			backgroundColor: 'transparent',
		};
	});
</script>

<div style="width: {width}px; height: {height}px;">
	<Chart {init} {options} theme="dark" />
</div>
