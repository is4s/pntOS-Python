<script lang="ts">
  export interface BaseChannelActivityCardProps {
    channel: string;
  }
</script>

<script setup lang="ts">
  import LCMDetailsIcon from '@/assets/branding/svgs/widgets/channel_activity/lcm_details.svg';
  import PinToTopDarkIcon from '@/assets/branding/svgs/widgets/channel_activity/pin_to_top_dark.svg';
  import PinToTopLightIcon from '@/assets/branding/svgs/widgets/channel_activity/pin_to_top_light.svg';
  import { SubscriptionMode } from '@/types';
  import { UI_CHANNELS_PREFIX, useCurrentTime, useRegistry } from '@/utils/useRegistry';
  import { computed } from 'vue';
  import ChannelHealthIndicator from './ChannelHealthIndicator.vue';

  const props = defineProps<BaseChannelActivityCardProps>();

  const registryGroup = UI_CHANNELS_PREFIX + props.channel;
  const tLastMessage = useRegistry<number>(registryGroup, 't_last_message', SubscriptionMode.LAST);
  const tNow = useCurrentTime();
  const tSinceLastMessage = computed(() => ((tNow.value ?? 0) - (tLastMessage.value ?? 0)) / 1e9);
  const pinned = useRegistry<boolean>(registryGroup, 'pinned', SubscriptionMode.LAST)


</script>

<template>
  <div class="container">
    <div class="top-row">
      <div class="top-left">
        <ChannelHealthIndicator :t-since-last-message="tSinceLastMessage" />
        {{ channel }}
      </div>
      <div class="top-right">
        <img :src="LCMDetailsIcon" class="lcm-details" />
        LCM Relay Details
        <div class="separator"></div>
        <div v-if="pinned"><img :src="PinToTopDarkIcon"></div>
        <div v-else><img :src="PinToTopLightIcon" /></div>
        Pin to Top
      </div>
    </div>
    <slot></slot>
  </div>
</template>

<style lang="css" scoped>
  .container {
    display: flex;
    padding: 5px;
    margin: 9px;
    background: var(--white-smoke);
    font-size: 9px;
    gap: 5px;
    flex-direction: column;
  }

  .top-row {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    width: 100%;
    height: 13px;
  }

  .top-left {
    display: flex;
    flex-direction: row;
    gap: 3px;
    align-items: center;
    font-weight: 900;
  }

  .lcm-details {
    height: 8px;
    width: 8px
  }

  .separator {
    height: 12px;
    width: 1px;
    background: #DDDDDD;
  }

  .top-right {
    display: flex;
    flex-direction: row;
    gap: 3px;
    font-weight: 400;
    font-style: italic;
    color: #686868;
    align-items: center;
    align-content: center;
  }

  .content {
    width: 100%;
    height: 46px;
  }
</style>
