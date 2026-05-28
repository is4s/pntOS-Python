<!-- eslint-disable vue/multi-word-component-names -->
<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/velocity/velocity_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/velocity/velocity_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Velocity',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'Velocity'
  }
</script>
<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Velocity widget!</div>
  </BaseWidget>
</template>
