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
    type: 'Heading',
    initialLayout: {
      h: 8
    }
  };
</script>

<script setup lang="ts">
  import CompassBackground from '@/assets/branding/svgs/widgets/heading/compass_background.svg';
  import CompassNeedle from '@/assets/branding/svgs/widgets/heading/compass_needle.svg';
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';
  import { useRegistry } from '@/utils/useRegistry';
  import { computed } from 'vue';
  import { type PvaMessage } from '@/utils/dataStructures.ts';

  const props = defineProps<BaseWidgetData>();
  const GROUP = "ui/channel//solution/pntos/pva";
  const pva = useRegistry<PvaMessage>(GROUP, "message")

  const quat = computed(() => ((pva.value?.wrapped_message.quaternion)))

  const heading = computed(() => {
    const q = quat.value;
    if (!q) return undefined;

    const [ w, x, y, z, ] = q;

    // Yaw (heading) from quaternion
    let yawRad = Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));

    let yawDeg = yawRad * (180 / Math.PI);
    if (yawDeg < 0) yawDeg += 360; // normalize to [0, 360)

    return yawDeg;
  });  
  const NEEDLE_OFFSET = -312; // to account for original SVG offset to zero
  const headingNeedle = computed(() => (heading.value ?? 0) + NEEDLE_OFFSET);

</script>

<template>
  <BaseWidget v-bind="props">
    <div id="heading-container">
      <div id="heading-compass-wrapper">
        <img :src="CompassBackground" id="heading-background" />
        <img :src="CompassNeedle" id="heading-needle" :style="{ transform: `translate(-85%, -85%) rotate(${headingNeedle}deg) !important` }"/>
      </div>
      <div id="heading-label"><span class="label-title">Heading:</span> {{ (heading ?? 0).toFixed(2) }} deg</div>    
    </div>
  </BaseWidget>
</template>

<style scoped>
  #heading-container {
    position: absolute;
    top: 27px;
    left: 0;
    width: 100%;
    height: calc(100% - 27px);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    container-type: size;
    gap: 8px;
    padding: 8px;
    box-sizing: border-box;
  }

  #heading-compass-wrapper {
    position: relative;
    /* Reserve ~24px for label + 16px for gaps/padding = 40px total */
    width: min(100cqw, calc(100cqh - 40px));
    height: min(100cqw, calc(100cqh - 40px));
    flex-shrink: 0;
  }

  #heading-background {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  #heading-needle {
    position: absolute;
    width: 36.9%;
    height: 34.2%;
    top: 50%;
    left: 50%;
    transform-origin: 85% 85%;
    transition: transform 0.1s ease-out;

  }

  #heading-label {
    color: var(--federal-blue);
    font-size: 16px;
    font-family: 'HK Grotesk';
    text-align: center;
    flex-shrink: 0;
    line-height: 16px;
  }

  .label-title {
    font-weight: 700;
  }
</style>
