<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/roll_and_pitch/roll_and_pitch_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/roll_and_pitch/roll_and_pitch_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';
  import { useRegistry } from '@/utils/useRegistry';

  export const metadata: WidgetMetadata = {
    title: 'Roll & Pitch',
    bannerStyle: 'none',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'RollAndPitch',
    initialLayout: {
      h: 8
    }
  };
</script>

<script setup lang="ts">
  import BackgroundFrame from '@/assets/branding/svgs/widgets/roll_and_pitch/background_frame.svg';
  import PitchMeter from '@/assets/branding/svgs/widgets/roll_and_pitch/pitch_meter.svg';
  import RollPlane from '@/assets/branding/svgs/widgets/roll_and_pitch/roll_plane.svg';
  import Gradient from '@/assets/branding/svgs/widgets/roll_and_pitch/gradient.svg';
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';
  import { computed } from 'vue';
  import { type PvaMessage } from '@/utils/dataStructures.ts';

  const props = defineProps<BaseWidgetData>()
  const GROUP = "ui/channel//solution/pntos/pva";
  
  const pva = useRegistry<PvaMessage>(GROUP, "message")

  const quat = computed(() => ((pva.value?.wrapped_message.quaternion)))
  
  const roll = computed(() => {
    const q = quat.value;
    if (!q) return undefined;

    const [w, x, y, z] = q;

    let rollRad = Math.atan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y));
    let rollDeg = rollRad * (180 / Math.PI);
    return rollDeg
  })

  const pitch = computed(() => {
    const q = quat.value;
    if (!q) return undefined;

    const [w, x, y, z] = q;

    let pitchRad = Math.asin(Math.min(Math.max(2 * (w * y - x * z), -1.0), 1.0));
    let pitchDeg = pitchRad * (180 / Math.PI);

    return pitchDeg;
  })

  // Tune this scale factor to match how many pixels (as % of wrapper height)
  // correspond to one degree of pitch on the meter SVG.
  const PITCH_SCALE = 9.0;

  const pitchTranslate = computed(() => (pitch.value ?? 0) * PITCH_SCALE);

</script>

<template>
  <BaseWidget v-bind="props">
    <div id="roll-pitch-container">
      <div id="roll-pitch-wrapper">
        <img
          :src="RollPlane"
          id="roll-plane"
          :style="{ transform: `rotate(${roll}deg)` }"
        />
        <img
          :src="PitchMeter"
          id="pitch-meter"
          :style="{ transform: `translateY(${pitchTranslate}%)` }"
        />
        <img :src="Gradient" id="gradient" />
        <img :src="BackgroundFrame" id="background-frame" />
      </div>
      <div id="roll-pitch-label">
        <span class="label-title">Roll:</span> {{ (roll ?? 0).toFixed(1) }} deg
        <span class="label-divider"> | </span>
        <span class="label-title">Pitch:</span> {{ (pitch ?? 0).toFixed(1) }} deg
      </div>
    </div>
  </BaseWidget>
</template>

<style scoped>
  #roll-pitch-container {
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

  #roll-pitch-wrapper {
    position: relative;
    width: min(100cqw, calc(100cqh - 40px));
    height: min(100cqw, calc(100cqh - 40px));
    flex-shrink: 0;
    overflow: hidden;
    border-radius: 50%;
  }

  #background-frame {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: contain;
    pointer-events: none;
  }

  #pitch-meter {
    position: absolute;
    width: 28.2%;
    height: 57.8%;
    top: 50%;
    left: 50%;
    transform-origin: center center;
    margin-top: -28.9%;  /* half of height to center vertically */
    margin-left: -14.1%; /* half of width to center horizontally */
    transition: transform 0.1s ease-out;
  }

  #gradient {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: contain;
    /* z-index: 2; */
    pointer-events: none;
  }

  #roll-plane {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: contain;
    transform-origin: center center;
    transition: transform 0.1s ease-out;
  }

  #roll-pitch-label {
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

  .label-divider {
    margin: 0 6px;
    color: var(--federal-blue);
    opacity: 0.4;
  }
</style>

