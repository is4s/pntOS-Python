<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/lat_lon_err/lat_lon_err_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/lat_lon_err/lat_lon_err_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';

  export const metadata: WidgetMetadata = {
    title: 'Lat Lon Error',
    bannerStyle: 'blue',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'LatLonErr'
  }
</script>

<script setup lang="ts">
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';


  const props = defineProps<BaseWidgetData>()

</script>

<template>
  <BaseWidget v-bind="props">
    <div>I am a Lat Lon Err widget!</div>
  </BaseWidget>
</template>
