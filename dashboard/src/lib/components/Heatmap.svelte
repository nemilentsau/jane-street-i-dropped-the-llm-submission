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
				formatter: (p: any) => {
					const v = p.value[2].toFixed(3);
					return `<span style="color:#8690a2">row</span> ${p.value[1]}, <span style="color:#8690a2">col</span> ${p.value[0]}<br/><strong style="font-size:13px">${v}</strong>`;
				},
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
			},
			grid: {
				top: title ? 36 : 8,
				right: 65,
				bottom: xlabel ? 40 : 16,
				left: ylabel ? 48 : 16,
			},
			xAxis: {
				type: 'category' as const,
				data: Array.from({ length: data[0]?.length ?? 0 }, (_, i) => i),
				name: xlabel,
				nameLocation: 'middle' as const,
				nameGap: 28,
				nameTextStyle: { color: '#b0b8c8', fontSize: 12, fontFamily: 'Instrument Sans' },
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
				nameGap: 36,
				nameTextStyle: { color: '#b0b8c8', fontSize: 12, fontFamily: 'Instrument Sans' },
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
				textStyle: { color: '#b0b8c8', fontSize: 11 },
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
