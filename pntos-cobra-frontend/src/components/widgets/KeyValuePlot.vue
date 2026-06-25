<script lang="ts">
// TODO: maybe need unique icons, but these look like a line plot so they work for now
import DarkIcon from '@/assets/branding/svgs/widgets/lcm_spy/lcm_spy_dark.svg';
import LightIcon from '@/assets/branding/svgs/widgets/lcm_spy/lcm_spy_light.svg';
import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

export const metadata: WidgetMetadata = {
  title: 'Key-Value Plot',
  bannerStyle: 'blue',
  single: true,
  darkIcon: DarkIcon,
  lightIcon: LightIcon,
  type: 'KeyValuePlot'
}
</script>

<script setup lang="ts">
import type { BaseWidgetData } from './BaseWidget.vue';
import BaseWidget from './BaseWidget.vue';
import { useRegistry, useGroupsWithRegex, useNumericalKeysFromGroup } from '@/utils/useRegistry';
import type { Ref } from 'vue'
import { ref, watch, computed, type WatchHandle } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { defineStore, storeToRefs } from 'pinia'
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

const useKeyValuePlotStore = defineStore('key-value-plot', () => {
  // grab all groups except ui/metadata and ui/frontend and config/*
  const groups = useGroupsWithRegex('^(?!ui/metadata|ui/frontend|config/.*)')
  const group = ref<string | null>(null)

  const keys = computed(() => {
    if (!group.value) return []
    return useNumericalKeysFromGroup(group.value).value
  })
  const key = ref<string | null>(null)

  const data = ref<[number, number][]>([])

  return { groups, group, keys, key, data }
})

const props = defineProps<BaseWidgetData>()

const store = useKeyValuePlotStore()
const { groups, group, key, keys, data } = storeToRefs(store)

const MAX_POINTS = 30
let x = 0
let value_ref: Ref<number | null> | null = null
let value_watch: WatchHandle | null = null

watch([group, key], ([new_group, new_key]) => {
  data.value.length = 0
  value_watch?.()
  if (!new_group || !new_key) {
    return
  }

  value_ref = useRegistry<number>(new_group, new_key, true)


  value_watch = watch(value_ref, (y) => {
    data.value.push([x, y!])
    x++
    if (data.value.length > MAX_POINTS) {
      data.value.shift()
    }
  },
    { immediate: true })
})


const option = computed(() => ({
  title: {
    text: 'Key-Value Plot',
    left: 'center'
  },
  xAxis: {
    name: 'Sample',
    nameLocation: 'middle',
    nameGap: 20,
    type: 'value',
    axisLabel: {
      showMinLabel: false,
      showMaxLabel: false,
    },
    min: (value: any) => value.min - (value.max - value.min) * 0.05, // add 5% padding between line and edge of plot
    max: (value: any) => value.max + (value.max - value.min) * 0.05,
  },
  yAxis: {
    name: 'Value',
    nameLocation: 'middle',
    nameGap: 35,
    nameRotate: 90,
    type: 'value',
  },
  series: {
    type: 'line',
    data: data.value,
    showSymbol: false,
    lineStyle: {
      color: 'blue',
    }
  }
}))
</script>

<template>
  <BaseWidget v-bind="props">
    <div class="content-container">
      <v-chart :option="option" autoresize />

      <div class="input-container">
        <div class="dropdown-container">
          <label id="group-label" for="group-select">Group:</label>
          <select id="group-select" v-model="group">
            <option value="" disabled>Select Group</option>
            <option v-for="group in groups">
              {{ group }}
            </option>
          </select>
        </div>

        <div class="dropdown-container">
          <label id="key-label" for="key-select">Key:</label>
          <select id="key-select" v-model="key">
            <option value="" disabled>Select Key</option>
            <option v-for="key in keys">
              {{ key }}
            </option>
          </select>
        </div>
      </div>

    </div>
    <template #minimized-content>
      <div>Key Value Plot</div>
    </template>
  </BaseWidget>
</template>

<style scoped>
.content-container {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  padding: 20px;
  max-width: 100%;
  /* overflow: hidden; */
}

.input-container {
  flex-wrap: wrap;
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 20px;
}

.dropdown-container {
  display: flex;
  flex-direction: row;
  max-width: 100%;
  gap: 20px;
}
</style>
