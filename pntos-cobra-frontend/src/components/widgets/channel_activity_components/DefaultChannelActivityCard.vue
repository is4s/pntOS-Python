<script setup lang="ts">
  import InfoIcon from '@/assets/branding/svgs/info.svg';
  import RadioSwitch from '@/components/common/RadioSwitch.vue';
  import { SubscriptionMode } from '@/types';
  import { UI_CHANNELS_PREFIX, useCurrentTime, useRegistry } from '@/utils/useRegistry';
  import { computed } from 'vue';
  import type { BaseChannelActivityCardProps } from './BaseChannelActivityCard.vue';
  import BaseChannelActivityCard from './BaseChannelActivityCard.vue';

  const props = defineProps<BaseChannelActivityCardProps>();

  const registryGroup = UI_CHANNELS_PREFIX + props.channel;

  const enableMediator = useRegistry<boolean>(registryGroup, 'enabled_mediator', SubscriptionMode.LAST);
  const enableSource = useRegistry<boolean>(registryGroup, 'enabled_source', SubscriptionMode.LAST);
  const messageCount = useRegistry<number>(registryGroup, 'message_count', SubscriptionMode.LAST);
  const rate = useRegistry<number>(registryGroup, 'rate', SubscriptionMode.LAST);
  const type = useRegistry<string>(registryGroup, 'type', SubscriptionMode.LAST);
  const jitter = useRegistry<number>(registryGroup, 'jitter', SubscriptionMode.LAST);
  const tLastMessage = useRegistry<number>(registryGroup, 't_last_message', SubscriptionMode.LAST);
  const tNow = useCurrentTime();
  const tSinceLastMessage = computed(() => ((tNow.value ?? 0) - (tLastMessage.value ?? 0)) / 1e9);
  const bandwidth = useRegistry<number>(registryGroup, 'bandwidth', SubscriptionMode.LAST);

  function toggleMediator() {
    enableMediator.value = !enableMediator.value;
  }

  function toggleSource() {
    enableSource.value = !enableSource.value;
  }

</script>

<template>
  <BaseChannelActivityCard v-bind="props">
    <div class="grid-container">
      <div class="count misc-info">
        <div class="field-label">Message Count:</div>
        <div class="field-data">{{ messageCount ?? 0 }}</div>
      </div>
      <div class="period misc-info">
        <div class="field-label">1/Hz:</div>
        <div class="field-data">{{ ((rate ?? 0) > 0 ? 1000 / rate! : 0).toPrecision(2) }} ms</div>
      </div>
      <div class="type misc-info">
        <div class="field-label">Type:</div>
        <div class="field-data">{{ type ?? "unknown" }}</div>
      </div>
      <div class="rate misc-info">
        <div class="field-label">Message Rate:</div>
        <div class="field-data">{{ (rate ?? 0.0).toString() }} Hz</div>
      </div>
      <div class="jitter misc-info">
        <div class="field-label">Jitter:</div>
        <div class="field-data">{{ ((jitter ?? 0) * 1e9).toString() }} ns</div>
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
          tSinceLastMessage < 1 ? '<1' : tSinceLastMessage.toFixed(1) }} s</div>
      </div>

      <div class="bandwidth misc-info">
        <div class="field-label">Bandwidth:</div>
        <div class="field-data">{{ ((bandwidth ?? 0) / 1000).toFixed(2) }} kbps</div>
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
    overflow-x: auto;
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
