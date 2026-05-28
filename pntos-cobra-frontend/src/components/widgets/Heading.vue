<!-- eslint-disable vue/multi-word-component-names -->
<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/heading/heading_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/heading/heading_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Heading',
    bannerStyle: 'none',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'Heading'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Heading widget!</div>
  </BaseWidget>
</template>
