<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/roll_and_pitch/roll_and_pitch_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/roll_and_pitch/roll_and_pitch_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Roll & Pitch',
    bannerStyle: 'none',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'RollAndPitch'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Roll And Pitch widget!</div>
  </BaseWidget>
</template>
