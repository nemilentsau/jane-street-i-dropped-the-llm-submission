<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { BarChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([BarChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	let {
		margins,
		title = '',
		width = 480,
		height = 220,
	}: {
		margins: number[];
		title?: string;
		width?: number;
		height?: number;
	} = $props();

	let options = $derived.by(() => {
		const minMargin = Math.min(...margins);

		return {
			tooltip: {
				trigger: 'axis' as const,
				axisPointer: { type: 'shadow' as const },
				formatter: (p: any) => `Pair ${p[0].dataIndex}: margin = ${p[0].value.toFixed(3)}`,
			},
			grid: {
				top: title ? 36 : 16,
				right: 12,
				bottom: 28,
				left: 44,
			},
			xAxis: {
				type: 'category' as const,
				data: margins.map((_, i) => i),
				name: 'Pairs (sorted by margin)',
				nameLocation: 'middle' as const,
				nameGap: 16,
				nameTextStyle: { color: '#8690a2', fontSize: 10 },
				axisLabel: { show: false },
				axisTick: { show: false },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: 'value' as const,
				axisLabel: { color: '#8690a2', fontSize: 10, formatter: (v: number) => v.toFixed(1) },
				axisLine: { show: false },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			series: [{
				type: 'bar' as const,
				data: margins.map(m => ({
					value: m,
					itemStyle: { color: m >= 0 ? '#3dd68c' : '#ee7a7a', opacity: 0.75 },
				})),
				barMaxWidth: 12,
				markLine: {
					silent: true,
					symbol: 'none',
					lineStyle: { color: '#f0b429', type: 'dashed' as const, width: 1 },
					data: [
						{
							yAxis: minMargin,
							label: {
								formatter: `min = ${minMargin.toFixed(2)}`,
								color: '#f0b429',
								fontSize: 10,
								fontFamily: 'var(--font-mono)',
							},
						},
					],
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
