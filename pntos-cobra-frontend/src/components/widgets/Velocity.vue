<!-- eslint-disable vue/multi-word-component-names -->
<script lang="ts">
import DarkIcon from '@/assets/branding/svgs/widgets/velocity/velocity_dark.svg'
import LightIcon from '@/assets/branding/svgs/widgets/velocity/velocity_light.svg'
import { type WidgetMetadata } from '@/components/WidgetGrid.vue'

export const metadata: WidgetMetadata = {
  title: 'Velocity',
  bannerStyle: 'blue',
  single: true,
  darkIcon: DarkIcon,
  lightIcon: LightIcon,
  type: 'Velocity',
}
</script>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import type { BaseWidgetData } from './BaseWidget.vue'
import { useRegistry } from '@/utils/useRegistry'
import BaseWidget from './BaseWidget.vue'
import { type PvaMessage } from '@/utils/dataStructures.ts'

const props = defineProps<BaseWidgetData>()

const GROUP = 'ui/channel//solution/pntos/pva'
const pva = useRegistry<PvaMessage>(GROUP, 'message')

const velocity = computed(() => {
  const msg = pva.value?.wrapped_message

  return {
    north: msg?.v1 ?? 0,
    east: msg?.v2 ?? 0,
    down: msg?.v3 ?? 0,
  }
})

const panelRef = ref<HTMLElement | null>(null)
const isVertical = ref(false)
let resizeObserver: ResizeObserver | null = null

function checkLayout(width?: number) {
  if (!panelRef.value && width === undefined) return
  const panelWidth = width ?? panelRef.value!.offsetWidth
  const boxWidth = 120
  const gap = 8
  isVertical.value = panelWidth < boxWidth * 3 + gap * 2
}
onMounted(() => {
  if (panelRef.value) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newWidth = entry.contentRect.width
        checkLayout(newWidth)
      }
    })
    resizeObserver.observe(panelRef.value)
  }
})

onBeforeUnmount(() => {
    resizeObserver?.disconnect()
})

function formatVelocity(value: number) {
  return value.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  })
}
</script>

<template>
  <BaseWidget v-bind="props">
    <div id="velocity-wrapper">
      <div id="velocity-panel" ref="panelRef">
        <div id="velocity-title">Velocity</div>
        <div id="velocity-values" :style="{ flexDirection: isVertical ? 'column' : 'row' }">
          <div class="velocity-box">
            <span class="label">North:</span>
            <span class="value">{{ formatVelocity(velocity.north) }} m/s</span>
          </div>

          <div class="velocity-box">
            <span class="label">East:</span>
            <span class="value">{{ formatVelocity(velocity.east) }} m/s</span>
          </div>

          <div class="velocity-box">
            <span class="label">Down:</span>
            <span class="value">{{ formatVelocity(velocity.down) }} m/s</span>
          </div>
        </div>
      </div>
    </div>
  </BaseWidget>
</template>

<style lang="css" scoped>
#velocity-wrapper {
  display: flex;
  justify-content: center;
  padding: 8px 8px;
}

#velocity-panel {
  background: whitesmoke;
  border: 6px solid white;
  border-radius: 8px;
  padding: 10px;
  width: 100%;
  font-size: 9px;
}

#velocity-title {
  text-align: left;
  font-weight: bold;
  color: black;
  margin-bottom: 8px;
}

#velocity-values {
  display: flex;
  flex-direction: row;
  gap: 8px;
}

.velocity-box {
  flex: 1;
  min-width: 0;

  background: white;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px;

  display: flex;
  justify-content: center;
  gap: 6px;
  text-align: center;
  color: gray;
}

.velocity-box .label {
  font-weight: bold;
}

.value {
  font-family: monospace;
}
</style>
