<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/lcm_spy/lcm_spy_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/lcm_spy/lcm_spy_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'LCM Spy',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'LcmSpy'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Lcm Spy widget!</div>
  </BaseWidget>
</template>
