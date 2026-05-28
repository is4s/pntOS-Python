<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/channel_activity/channel_activity_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/channel_activity/channel_activity_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';
  import { useGroupsWithRegex } from '@/utils/useRegistry';
  import ChannelHealthIndicator from './channel_activity_components/ChannelHealthIndicator.vue';
  import DefaultChannelActivityCard from './channel_activity_components/DefaultChannelActivityCard.vue';

  export const metadata: WidgetMetadata = {
    title: 'Channel Activity',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'ChannelActivity',
    initialLayout: { h: 10, maxW: 1 }
  };
</script>

<script setup lang="ts">
  import { channelFromGroup, UI_CHANNELS_PREFIX } from '@/utils/useRegistry';
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';

  const props = defineProps<BaseWidgetData>();

  const groups = useGroupsWithRegex(`${UI_CHANNELS_PREFIX}.*`)


</script>

<template>
  <BaseWidget v-bind="props">
    <div class="top-bar-blue">
      <div class="top-bar-white"></div>
      <div class="color-code-bar">
        <div class="container">
          <ChannelHealthIndicator :t-since-last-message="0" />0-5 Seconds
        </div>
        <div class="container">
          <ChannelHealthIndicator :t-since-last-message="5" />5-60 Seconds
        </div>
        <div class="container">
          <ChannelHealthIndicator :t-since-last-message="60" /> 60+ Seconds
        </div>
      </div>
    </div>
    <div v-if="!groups.length">
      <div class="no-channels-message">No channels discovered yet.</div>
    </div>
    <div v-for="group of groups" :key="group" class="cards">
      <DefaultChannelActivityCard :channel="channelFromGroup(group)" />
    </div>

  </BaseWidget>
</template>

<style lang="css" scoped>
  .top-bar-blue {
    height: 20px;
    width: 100%;
    background: var(--federal-blue);
    color: var(--white);
    font-size: 9px;
  }

  .top-bar-white {
    background: var(--white-smoke);
    height: 1px;
    margin-left: 9px;
    margin-right: 9px;
  }

  .color-code-bar {
    height: 19px;
    display: flex;
    width: 100%;
    justify-content: space-between;
    align-content: center;
    align-items: center;
    padding-left: 14px;
    padding-right: 14px;
  }

  .container {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .no-channels-message {
    display: flex;
    justify-content: center;
    margin: 10px;
    color: #686868;
  }

  .cards {
    overflow-y: auto;
  }

</style>
