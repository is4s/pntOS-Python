<script lang="ts">
  export const HEALTHY_COLOR = 0x44A842
  export const SICKLY_COLOR = 0xCCA629
  export const DEADLY_COLOR = 0xC33436
</script>

<script setup lang="ts">
  import { computed, onMounted, onUnmounted, ref, watch } from 'vue';
  import { useChannelTimers } from './DefaultChannelActivityCard.vue';

  interface ChannelHealthIndicatorProps {
    value?: unknown
    staticColor?: number
    channel?: string
  }

  const props = defineProps<ChannelHealthIndicatorProps>()

  if (!props.staticColor && !props.channel) {
    throw new Error('ChannelHealthIndicator requires either channel or staticColor prop')
  }

  const SICKLY_THRESHOLD = 5
  const DEADLY_THRESHOLD = 60

  const color = ref<number>(props.staticColor ?? HEALTHY_COLOR)

  if (props.staticColor !== undefined) {
    watch(
      () => props.staticColor,
      (newColor) => {
        if (newColor !== undefined) {
          color.value = newColor
        }
      }
    )
  }

  if (props.channel) {
    const timerStore = useChannelTimers()
    let intervalId: number | null = null

    const state = timerStore.getCountdown(props.channel)
    color.value = state.color

    onMounted(() => {
      intervalId = window.setInterval(() => {
        if (!props.channel) return
        const state = timerStore.getCountdown(props.channel)
        const newRemaining = state.remaining - 0.1

        if (newRemaining <= 0) {
          if (state.color === HEALTHY_COLOR) {
            timerStore.setCountdown(props.channel, DEADLY_THRESHOLD - SICKLY_THRESHOLD, SICKLY_COLOR)
          } else if (state.color === SICKLY_COLOR) {
            timerStore.setCountdown(props.channel, 0, DEADLY_COLOR)
          }
        } else {
          timerStore.setCountdown(props.channel, newRemaining, state.color)
        }
        color.value = timerStore.getCountdown(props.channel).color
      }, 100)
    })

    onUnmounted(() => {
      if (intervalId !== null) {
        window.clearInterval(intervalId)
      }
    })

    watch(
      () => props.value,
      () => {
        if (props.channel) {
          timerStore.resetCountdown(props.channel)
          color.value = HEALTHY_COLOR
        }
      }
    )
  }

  const colorRender = computed(() => `#${color.value.toString(16).padStart(6, '0')}`)
</script>

<template>
  <div class="health-indicator" :style="`background: ${colorRender}`"></div>
</template>

<style lang="css" scoped>
  .health-indicator {
    width: 10px;
    height: 10px;
    border-radius: 100%;
    border: 1px solid var(--federal-blue);
  }
</style>
