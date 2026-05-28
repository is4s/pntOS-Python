<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/ground_speed/ground_speed_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/ground_speed/ground_speed_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Ground Speed',
    bannerStyle: 'none',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'GroundSpeed'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Ground Speed widget!</div>
    <template #minimized-content>
      <div>Minimized view of Ground Speed widget!</div>
    </template>
  </BaseWidget>
</template>
