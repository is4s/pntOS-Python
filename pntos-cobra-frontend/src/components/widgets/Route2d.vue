<!-- eslint-disable vue/multi-word-component-names -->
<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/route_2d/route_2d_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/route_2d/route_2d_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Route 2D',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'Route2d'
  }
</script>
<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Route 2d widget!</div>
  </BaseWidget>
</template>
