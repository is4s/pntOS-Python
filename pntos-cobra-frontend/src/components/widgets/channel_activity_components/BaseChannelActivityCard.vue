<script setup lang="ts">

  import LCMDetailsIcon from '@/assets/branding/svgs/widgets/channel_activity/lcm_details.svg';
  import PinToTopDarkIcon from '@/assets/branding/svgs/widgets/channel_activity/pin_to_top_dark.svg';
  import PinToTopLightIcon from '@/assets/branding/svgs/widgets/channel_activity/pin_to_top_light.svg';
  import HoverButton from '@/components/common/HoverButton.vue';
  import { SubscriptionMode } from '@/types';
  import { UI_CHANNELS_PREFIX, useRegistry } from '@/utils/useRegistry';
  import { useWidgetActions } from '@/utils/useWidgetActions';
  import { useChannelActivityStore } from '../ChannelActivity.vue';
  import ChannelHealthIndicator from './ChannelHealthIndicator.vue';

  interface Props {
    channel: string
  }

  const props = defineProps<Props>()

  const pinnedStore = useChannelActivityStore()

  const registryGroup = UI_CHANNELS_PREFIX + props.channel
  const pinned = useRegistry<boolean>(registryGroup, 'pinned', SubscriptionMode.LAST)
  const messageCount = useRegistry<number>(registryGroup, 'message_count', SubscriptionMode.LAST)
  const { addWidget } = useWidgetActions()

  function onPinClick() {
    console.log("Pinned! ", props.channel)
    pinned.value = !pinned.value
    if (pinned.value) {
      pinnedStore.addToPinned(props.channel)
    } else {
      pinnedStore.removeFromPinned(props.channel)
    }
  }

  function onLcmClick() {
    addWidget({ type: "LcmSpy" })
  }

</script>

<template>
  <div class="container">
    <div class="top-row">
      <div class="top-left">
        <ChannelHealthIndicator :channel="channel" :value="messageCount" />
        {{ channel }}
      </div>
      <div class="top-right">
        <HoverButton @click=onLcmClick>
          <div class="top-right">
            <img :src="LCMDetailsIcon" class="lcm-details" />
            LCM Relay Details
          </div>
        </HoverButton>
        <div class="separator"></div>
        <HoverButton @click=onPinClick>
          <div class="top-right">
            <div v-if="pinned"><img :src="PinToTopDarkIcon"></div>
            <div v-else><img :src="PinToTopLightIcon" /></div>
            Pin to Top
          </div>
        </HoverButton>
      </div>
    </div>
    <slot></slot>
  </div>
</template>

<style lang="css" scoped>
  .container {
    display: flex;
    padding: 5px;
    margin-left: 9px;
    margin-right: 9px;
    margin-top: 9px;
    margin-bottom: 0;
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
    margin-left: 3px;
    margin-right: 3px;
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

  .lcm-button-container {
    display: flex;
    height: 13px;
    flex-direction: row;
  }

  .content {
    width: 100%;
    height: 46px;
  }
</style>
