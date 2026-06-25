<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/lat_lon_err/lat_lon_err_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/lat_lon_err/lat_lon_err_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Position Error',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'NedErr'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';
  import type { CallbackDataParams } from 'echarts/types/dist/shared'
  import { useRegistry } from '@/utils/useRegistry';
  import { ref, watch, computed } from 'vue'
  import { type PvaMessage } from '@/utils/dataStructures.ts';
  import VChart from 'vue-echarts'
  import { use } from 'echarts/core'
  import { CanvasRenderer } from 'echarts/renderers'
  import { LineChart } from 'echarts/charts'
  import {
    GridComponent,
    TooltipComponent,
    LegendComponent,
  } from 'echarts/components'

  use([
    CanvasRenderer,
    LineChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
  ])

  const props = defineProps<BaseWidgetData>()

  const SOL_GROUP = "ui/channel//solution/pntos/pva"
  const TRUTH_GROUP = "ui/channel//sensor/ins-d/pva"
  const pva = useRegistry<PvaMessage>(SOL_GROUP, "message")
  const truth_pva = useRegistry<PvaMessage>(TRUTH_GROUP, "message")

  const MAX_POINTS = 30
  let t0 = 0
  type DataPoint = [number, number]
  interface AxisData {
    error: DataPoint[]
    sigma: DataPoint[]
    negSigma: DataPoint[]
  }
  const ned = ref<AxisData[]>([
    { error: [], sigma: [], negSigma: [] },
    { error: [], sigma: [], negSigma: [] },
    { error: [], sigma: [], negSigma: [] }
  ])
  const earth_radius = 6378137
  const NSEC_IN_SEC = 1_000_000_000

  watch(pva, (cur_pva) => {
    if (cur_pva == null || truth_pva.value == null) {
      return
    }

    if (t0 == 0) {
      t0 = cur_pva.wrapped_message.time_of_validity.elapsed_nsec / NSEC_IN_SEC
      console.log("Base time", cur_pva.wrapped_message.time_of_validity.elapsed_nsec)
      console.log("T0", t0)
    }
    let cur_msg = cur_pva.wrapped_message
    let truth_msg = truth_pva.value.wrapped_message

    let cur_pos: [number, number, number] = [cur_msg.p1, cur_msg.p2, cur_msg.p3]
    let truth_pos: [number, number, number] = [truth_msg.p1, truth_msg.p2, truth_msg.p3]

    let cur_pos_err: [number, number, number] = [cur_pos[0] - truth_pos[0], cur_pos[1] - truth_pos[1], cur_pos[2] - truth_pos[2]]

    // Truth PVA will be ahead of filter solution since filter solution is a couple seconds behind
    // real time. Assume constant velocity over this interval to compute truth PVA at filter solution
    // time
    let cur_time_s = cur_msg.time_of_validity.elapsed_nsec / NSEC_IN_SEC
    let true_time_s = truth_msg.time_of_validity.elapsed_nsec / NSEC_IN_SEC

    let dt = true_time_s - cur_time_s
    let north_corr = truth_msg.v1 * dt
    let east_corr = truth_msg.v2 * dt
    let down_corr = truth_msg.v3 * dt

    let north_err = (earth_radius * cur_pos_err[0] * Math.PI / 180) + north_corr
    let east_err = (earth_radius * Math.cos(truth_pos[0] * Math.PI / 180) * cur_pos_err[1] * Math.PI / 180) + east_corr
    let down_err = cur_pos_err[2] + down_corr

    let t = cur_time_s - t0
    let nsig = Math.sqrt(cur_msg.covariance[0][0])
    let esig = Math.sqrt(cur_msg.covariance[1][1])
    let dsig = Math.sqrt(cur_msg.covariance[2][2])

    const errors = [north_err, east_err, down_err]
    const sigmas = [nsig, esig, dsig]
    for (let i = 0; i < 3; i++) {
      ned.value[i]?.error.push([t, errors[i]!])
      ned.value[i]?.sigma.push([t, sigmas[i]!])
      ned.value[i]?.negSigma.push([t, -sigmas[i]!])
    }

    if (ned.value[0]!.error.length > MAX_POINTS) {
      for (let i = 0; i < 3; i++) {
        ned.value[i]?.error.shift()
        ned.value[i]?.sigma.shift()
        ned.value[i]?.negSigma.shift()
      }
    }
  })
  const yLabels = ['North', 'East', 'Down']

  const option = computed(() => ({
    title: {
      text: 'Position Error',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: CallbackDataParams[]) => {
        let [t, error] = params[0]!.value as [number, number]
        let [, sigma] = params[1]!.value as [number, number]
        return `
        Time: ${t.toFixed(2)} s<br/>
        Error: ${error.toFixed(2)} m<br/>
        Sigma: ${sigma.toFixed(2)} m
      `
      }
    },
    legend: {
      top: 10,
      data: ['Error'],
    },
    grid: [
      { left: '3%', right: '4%', top: '8%', height: '24%', containLabel: true },
      { left: '3%', right: '4%', top: '38%', height: '24%', containLabel: true },
      { left: '3%', right: '4%', top: '68%', height: '24%', containLabel: true }
    ],
    xAxis: Array(3).fill(0).map((_, i) => ({
      gridIndex: i,
      name: i === 2 ? 'Time (s)' : '',
      nameLocation: 'middle',
      nameGap: 20,
      type: 'value',
      min: () => {
        const earliest = ned.value[0]!.error.at(0)?.[0] ?? 0
        return Math.max(-1, earliest - 1)
      },
      max: (value: any) => {
        const latest = ned.value[0]!.error.at(-1)?.[0] ?? 0
        return Math.max(30, latest + 1)
      },
      axisLine: { onZero: false },
      axisLabel: {
        show: true,
        formatter: (v: number) => v.toFixed(1) // round to 1 decimal
      },
      axisTick: { show: true }
    })),
    yAxis: Array(3).fill(0).map((_, i) => ({
      gridIndex: i,
      name: yLabels[i],
      nameLocation: 'middle',
      nameGap: 35,
      nameRotate: 90,
      type: 'value',
      axisLabel: {
        formatter: (v: number) => v.toFixed(1) // round to 1 decimal
      },
    })),
    series: Array(3).fill(0).map((_, i) => ({
      type: 'line',
      xAxisIndex: i,
      yAxisIndex: i,
      data: ned.value[i]!.error,
      showSymbol: false,
      lineStyle: {
        color: 'blue',
      }
    })).concat(
      Array(3).fill(0).map((_, i) => ({
        type: 'line',
        xAxisIndex: i,
        yAxisIndex: i,
        data: ned.value[i]!.sigma,
        showSymbol: false,
        lineStyle: {
          type: 'dashed',
          color: 'black',
        }
      }))
    ).concat(
      Array(3).fill(0).map((_, i) => ({
        type: 'line',
        xAxisIndex: i,
        yAxisIndex: i,
        data: ned.value[i]!.negSigma,
        showSymbol: false,
        lineStyle: {
          type: 'dashed',
          color: 'black',
        }
      }))
    ),
  }))
</script>

<template>
  <BaseWidget v-bind="props">
    <v-chart :option="option" autoresize class="echarts" />
    <template #minimized-content>
      <div>Altitude Plot</div>
    </template>
  </BaseWidget>
</template>

<style scoped>
  .echarts {
    height: 400px;
    width: 100%;
  }
</style>
