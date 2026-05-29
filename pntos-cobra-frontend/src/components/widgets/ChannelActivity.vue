<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/channel_activity/channel_activity_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/channel_activity/channel_activity_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';
  import { useChannels } from '@/utils/useRegistry';
  import { defineStore } from 'pinia';
  import { computed } from 'vue';
  import ChannelHealthIndicator, { DEADLY_COLOR, HEALTHY_COLOR, SICKLY_COLOR } from './channel_activity_components/ChannelHealthIndicator.vue';
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

  export const useChannelActivityStore = defineStore('channel-activity-widget', {
    state: () => ({
      pinnedChannels: [] as string[],
    }),

    actions: {
      isPinned(channel: string): boolean {
        return this.pinnedChannels.includes(channel)
      },
      addToPinned(channel: string): void {
        if (!this.isPinned(channel)) {
          this.pinnedChannels.push(channel)
        }
      },
      removeFromPinned(channel: string): void {
        this.pinnedChannels = this.pinnedChannels.filter((c) => c !== channel)
      },
    },
    persist: true,
  })

</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';

  const props = defineProps<BaseWidgetData>();

  const channels = useChannels()

  const store = useChannelActivityStore()

  const pinnedChannels = computed(() => channels.value.filter((c) => store.isPinned(c)))
  const notPinnedChannels = computed(() => channels.value.filter((c) => !store.isPinned(c)))


</script>

<template>
  <BaseWidget v-bind="props">
    <div class="content-container">
      <div class="top-bar-blue">
        <div class="top-bar-white"></div>
        <div class="color-code-bar">
          <div class="container">
            <ChannelHealthIndicator :static-color="HEALTHY_COLOR" />0-5 Seconds
          </div>
          <div class="container">
            <ChannelHealthIndicator :static-color="SICKLY_COLOR" />5-60 Seconds
          </div>
          <div class="container">
            <ChannelHealthIndicator :static-color="DEADLY_COLOR" /> 60+ Seconds
          </div>
        </div>
      </div>
      <div class="card-area">
        <div v-if="!channels.length">
          <div class="no-channels-message">No channels discovered yet.</div>
        </div>
        <div v-for="channel of pinnedChannels" :key="channel" class="card">
          <DefaultChannelActivityCard :channel="channel" />
        </div>
        <div v-for="channel of notPinnedChannels" :key="channel" class="card">
          <DefaultChannelActivityCard :channel="channel" />
        </div>
      </div>
    </div>
  </BaseWidget>
</template>

<style lang="css" scoped>
  .content-container {
    position: absolute;
    top: 27px;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    flex-direction: column;
  }

  .top-bar-blue {
    flex: 0 0 auto;
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

  .card-area {
    flex: 1 1 0;
    min-height: 0;
    overflow-y: auto;
  }

</style>
