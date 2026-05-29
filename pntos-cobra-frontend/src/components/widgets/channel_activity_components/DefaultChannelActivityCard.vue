<script lang="ts">
  import { defineStore } from 'pinia';
  import { ref } from 'vue';
  import { HEALTHY_COLOR } from './ChannelHealthIndicator.vue';

  export const useChannelTimers = defineStore('channelTimers', () => {
    const timers = ref<Record<string, number>>({})
    const countdowns = ref<Record<string, { remaining: number, color: number }>>({})

    function getTime(channel: string): number {
      return timers.value[channel] ?? 0
    }

    function setTime(channel: string, time: number) {
      timers.value[channel] = time
    }

    function reset(channel: string) {
      timers.value[channel] = 0
    }

    function getCountdown(channel: string) {
      return countdowns.value[channel] ?? { remaining: 5, color: HEALTHY_COLOR }
    }

    function setCountdown(channel: string, remaining: number, color: number) {
      countdowns.value[channel] = { remaining, color }
    }

    function resetCountdown(channel: string) {
      countdowns.value[channel] = { remaining: 5, color: HEALTHY_COLOR }
    }

    return {
      timers,
      countdowns,
      getTime,
      setTime,
      reset,
      getCountdown,
      setCountdown,
      resetCountdown
    }
  }, { persist: true })
</script>

<script setup lang="ts">
  import InfoIcon from '@/assets/branding/svgs/info.svg';
  import RadioSwitch from '@/components/common/RadioSwitch.vue';
  import { useRegistryMessageType } from '@/utils/messages';
  import { useRegistryWithUnits, useUnits } from '@/utils/units';
  import { UI_CHANNELS_PREFIX, useRegistry } from '@/utils/useRegistry';
  import { computed, onMounted, onUnmounted, watch } from 'vue';
  import BaseChannelActivityCard from './BaseChannelActivityCard.vue';

  interface Props {
    channel: string
  }

  const props = defineProps<Props>()

  const registryGroup = UI_CHANNELS_PREFIX + props.channel

  const enableMediator = useRegistry<boolean>(registryGroup, 'enabled_mediator')
  const enableSource = useRegistry<boolean>(registryGroup, 'enabled_source')
  const messageCount = useRegistry<number>(registryGroup, 'message_count')
  const { number: hzValue, rawNumber: rawHz, renderedUnit: hzUnit } = useRegistryWithUnits(registryGroup, 'rate', "Hz")
  const type = useRegistryMessageType(registryGroup, 'type')
  const { number: jitter, renderedUnit: jitterUnit } = useRegistryWithUnits(registryGroup, 'jitter', 's')
  const { number: bandwidth, renderedUnit: bandwidthUnit } = useRegistryWithUnits(registryGroup, 'bandwidth', 'Bps')
  const rateRaw = computed(() => (1 / rawHz.value))
  const { number: rateValue, renderedUnit: rateUnit } = useUnits(rateRaw, 's')

  const timerStore = useChannelTimers()
  const time = computed(() => timerStore.getTime(props.channel))

  let intervalId: number | null = null

  onMounted(() => {
    intervalId = window.setInterval(() => {
      timerStore.setTime(props.channel, time.value + 0.1)
    }, 100)
  })

  onUnmounted(() => {
    if (intervalId !== null) {
      window.clearInterval(intervalId)
    }
  })

  watch(messageCount, () => timerStore.reset(props.channel))

  function toggleMediator() {
    enableMediator.value = !enableMediator.value
  }

  function toggleSource() {
    enableSource.value = !enableSource.value
  }

</script>

<template>
  <BaseChannelActivityCard :channel="channel">
    <div class="grid-container">
      <div class="count misc-info">
        <div class="field-label">Message Count:</div>
        <div class="field-data">{{ messageCount ?? 0 }}</div>
      </div>
      <div class="period misc-info">
        <div class="field-label">1/Hz:</div>
        <div class="field-data">{{ rateValue.toFixed(1) }} {{ rateUnit }}</div>
      </div>
      <div class="type misc-info">
        <div class="field-label">Type:</div>
        <div class="field-data">{{ type ?? "unknown" }}</div>
      </div>
      <div class="rate misc-info">
        <div class="field-label">Message Rate:</div>
        <div class="field-data">{{ hzValue.toFixed(1) }} {{ hzUnit }}</div>
      </div>
      <div class="jitter misc-info">
        <div class="field-label">Jitter:</div>
        <div class="field-data">{{ jitter.toFixed(1) }} {{ jitterUnit }}</div>
      </div>
      <div class="disables"><img :src="InfoIcon" class="info-icon" />
        <div class="toggle">
          <RadioSwitch :val="enableSource ?? true" :callback="toggleSource" /> Source
        </div>
        <div class="toggle">
          <RadioSwitch :val="enableMediator ?? true" :callback="toggleMediator" /> Mediator
        </div>
      </div>
      <div class="received misc-info">
        <div class="field-label">Message Received:</div>
        <div class="field-data">{{
          time < 1 ? '<1' : time.toFixed(1) }} s</div>
      </div>

      <div class="bandwidth misc-info">
        <div class="field-label">Bandwidth:</div>
        <div class="field-data">{{ bandwidth.toFixed(1) }} {{ bandwidthUnit }}</div>
      </div>


    </div>
  </BaseChannelActivityCard>
</template>

<style lang="css" scoped>
  .grid-container {
    display: grid;
    grid-template-columns: 1fr 1fr 87px;
    grid-template-rows: repeat(3, 14px);
    gap: 2px;
    width: 100%;
    color: #686868;
  }

  .info-icon {
    height: 7px;
    width: 7px;
    position: absolute;
    top: 3px;
    right: 3px;
  }

  .misc-info {
    background: var(--white);
    border-radius: 2px;
    padding-left: 3px;
    position: relative;
    display: flex;
    height: 14px;
    gap: 3px;
    overflow: hidden;
  }

  .field-label {
    font-weight: 900;
  }

  .field-data {
    font-weight: 400;
  }

  .disables {
    grid-row: span 2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: var(--white);
    border-radius: 2px;
  }

  .toggle {
    font-weight: 900;
    display: flex;
    align-items: center;
    gap: 7px;
    margin-left: 9px;
  }

</style>
