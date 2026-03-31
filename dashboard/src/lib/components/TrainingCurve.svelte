<script lang="ts">
	import { Chart } from 'svelte-echarts';
	import { LineChart } from 'echarts/charts';
	import { init } from 'echarts/core';
	import { TooltipComponent, GridComponent, MarkLineComponent } from 'echarts/components';
	import { CanvasRenderer } from 'echarts/renderers';
	import { use } from 'echarts/core';

	use([LineChart, TooltipComponent, GridComponent, MarkLineComponent, CanvasRenderer]);

	let {
		data,
		baselineCorrect = 48,
		randomCorrect = 1,
		width = 560,
		height = 280,
	}: {
		data: { epoch: number; pairs_correct: number; snr: number }[];
		baselineCorrect?: number;
		randomCorrect?: number;
		width?: number;
		height?: number;
	} = $props();

	let options = $derived.by(() => {
		return {
			tooltip: {
				trigger: 'axis' as const,
				backgroundColor: '#1c2128',
				borderColor: '#363e4a',
				textStyle: { color: '#eceff4', fontSize: 12 },
				formatter: (params: unknown) => {
					const p = params as { dataIndex: number }[];
					const d = data[p[0].dataIndex];
					return `<span style="color:#8690a2">Epoch ${d.epoch}</span><br/>`
						+ `<strong style="color:#3dd68c">${d.pairs_correct}/48</strong> correct pairs<br/>`
						+ `<span style="color:#b0b8c8">SNR ${d.snr}x</span>`;
				},
			},
			grid: {
				top: 28,
				right: 12,
				bottom: 40,
				left: 48,
			},
			xAxis: {
				type: 'category' as const,
				data: data.map(d => `${d.epoch}`),
				name: 'Training epoch',
				nameLocation: 'middle' as const,
				nameGap: 26,
				nameTextStyle: { color: '#b0b8c8', fontSize: 12, fontFamily: 'Instrument Sans' },
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisTick: { alignWithLabel: true },
				axisLine: { lineStyle: { color: '#363e4a' } },
			},
			yAxis: {
				type: 'value' as const,
				min: 0,
				max: 48,
				interval: 12,
				name: 'Pairs correct (/48)',
				nameTextStyle: { color: '#b0b8c8', fontSize: 11, fontFamily: 'Instrument Sans', padding: [0, 0, 0, 40] },
				axisLabel: { color: '#b0b8c8', fontSize: 11 },
				axisLine: { show: false },
				splitLine: { lineStyle: { color: '#262d38' } },
			},
			series: [{
				type: 'line' as const,
				data: data.map(d => d.pairs_correct),
				smooth: false,
				symbol: 'circle',
				symbolSize: 8,
				lineStyle: { color: '#3dd68c', width: 2.5 },
				itemStyle: { color: '#3dd68c' },
				label: {
					show: true,
					position: 'top' as const,
					color: '#eceff4',
					fontSize: 11,
					fontFamily: 'JetBrains Mono, monospace',
					formatter: (p: unknown) => `${(p as { value: number }).value}`,
				},
				markLine: {
					silent: true,
					symbol: 'none' as const,
					lineStyle: { type: 'dashed' as const, width: 1.5 },
					data: [
						{
							yAxis: baselineCorrect,
							lineStyle: { color: '#6cb6ff' },
							label: {
								formatter: `original model (${baselineCorrect}/48)`,
								color: '#6cb6ff',
								fontSize: 10,
								fontFamily: 'JetBrains Mono, monospace',
								position: 'insideEndTop' as const,
								backgroundColor: 'rgba(13, 17, 23, 0.85)',
								padding: [2, 6] as [number, number],
								borderRadius: 3,
							},
						},
						{
							yAxis: randomCorrect,
							lineStyle: { color: '#ee7a7a' },
							label: {
								formatter: `random chance (~${randomCorrect}/48)`,
								color: '#ee7a7a',
								fontSize: 10,
								fontFamily: 'JetBrains Mono, monospace',
								position: 'insideEndTop' as const,
								backgroundColor: 'rgba(13, 17, 23, 0.85)',
								padding: [2, 6] as [number, number],
								borderRadius: 3,
							},
						},
					],
				},
			}],
			title: {
				text: 'Pairing signal emergence during training',
				textStyle: { color: '#b0b8c8', fontSize: 12, fontWeight: 600 },
				left: 0,
				top: 0,
			},
			backgroundColor: 'transparent',
		};
	});
</script>

<div style="width: {width}px; height: {height}px;">
	<Chart {init} {options} theme="dark" />
</div>
