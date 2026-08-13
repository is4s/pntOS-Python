<script lang="ts">
  import DarkIcon from '@/assets/branding/svgs/widgets/ground_speed/ground_speed_dark.svg';
  import LightIcon from '@/assets/branding/svgs/widgets/ground_speed/ground_speed_light.svg';
  import { type WidgetMetadata } from '@/components/WidgetGrid.vue';
import { useRegistry } from '@/utils/useRegistry';

  export const metadata: WidgetMetadata = {
    title: 'Speed',
    bannerStyle: 'none',
    single: true,
    darkIcon: DarkIcon,
    lightIcon: LightIcon,
    type: 'Speed',
    initialLayout: {
      h: 8
    }
  };
</script>

<script setup lang="ts">
  import AirBackground from '@/assets/branding/svgs/widgets/ground_speed/air_background.svg';
  import Needle from '@/assets/branding/svgs/widgets/ground_speed/needle.svg';
  import GroundBackground from '@/assets/branding/svgs/widgets/ground_speed/ground_background.svg';
  import AirIconDark from '@/assets/branding/svgs/widgets/ground_speed/air_icon_dark.svg';
  import AirIconLight from '@/assets/branding/svgs/widgets/ground_speed/air_icon_light.svg';
  import GroundIconDark from '@/assets/branding/svgs/widgets/ground_speed/ground_icon_dark.svg';
  import GroundIconLight from '@/assets/branding/svgs/widgets/ground_speed/ground_icon_light.svg';
  import type { BaseWidgetData } from './BaseWidget.vue';
  import BaseWidget from './BaseWidget.vue';
  import { computed, ref } from 'vue';
  import { type PvaMessage } from '@/utils/dataStructures.ts';

  const props = defineProps<BaseWidgetData>();
  const GROUP = "ui/channel//solution/pntos/pva";
  const pva = useRegistry<PvaMessage>(GROUP, "message")
  
  type Mode = 'ground' | 'air';
  const mode = ref<Mode>('ground');

  const quat = computed(() => ((pva.value?.wrapped_message.quaternion)))

  const velocityNed = computed(() => {
    const pva_msg = pva.value?.wrapped_message;
    if (!pva_msg) return undefined;
    return [pva_msg.v1, pva_msg.v2] as [number, number];
  });

  // Compute speed
  const speed = computed(() => {
    const v = velocityNed.value;
    if (!v) return undefined;

    const [vN, vE] = v;
    const mphCoversion = 2.237; // m/s to mph

    return Math.sqrt(vN ** 2 + vE ** 2) * mphCoversion;
  });
  
  const airSpeed = computed(() => speed.value ?? 0);
  const groundSpeed = computed(() => speed.value ?? 0);

  const currentSpeed = computed(() => mode.value === 'air' ? airSpeed.value : groundSpeed.value);
  const currentLabel = computed(() => mode.value === 'air' ? 'Air Speed' : 'Ground Speed');

  // Each gauge sweeps a fixed arc. Tune these per gauge:
  // AIR:    0 to 700 mph maps to some degree range
  // GROUND: 0 to 120 mph maps to some degree range
  // The needle SVG points right at rest, and the gauge starts at bottom-left (0)
  // and ends at bottom-right (max), so the sweep is roughly 240 degrees total.
  // NEEDLE_OFFSET rotates the needle from its SVG rest angle to the 0 mark.

  const AIR_NEEDLE_OFFSET = -249;   // tune until needle sits on 0 mark
  const AIR_MAX_SPEED = 700;
  const AIR_SWEEP_DEG = 270;        // total degrees from 0 to 700

  const GROUND_NEEDLE_OFFSET = -249; // tune until needle sits on 0 mark
  const GROUND_MAX_SPEED = 120;
  const GROUND_SWEEP_DEG = 270;      // total degrees from 0 to 120

  const airNeedleDeg = computed(() => {
    const fraction = Math.min(airSpeed.value / AIR_MAX_SPEED, 1);
    return AIR_NEEDLE_OFFSET + fraction * AIR_SWEEP_DEG;
  });

  const groundNeedleDeg = computed(() => {
    const fraction = Math.min(groundSpeed.value / GROUND_MAX_SPEED, 1);
    return GROUND_NEEDLE_OFFSET + fraction * GROUND_SWEEP_DEG;
  });

  const currentNeedleDeg = computed(() =>
    mode.value === 'air' ? airNeedleDeg.value : groundNeedleDeg.value
  );
</script>

<template>
  <BaseWidget v-bind="props">
    <div class="top-bar">
      <div class="top-bar-content">
        <div class="top-bar-icons">
          <div class="mode-icon" :class="{ active: mode === 'air' }" @click="mode = 'air'">
            <img :src="mode === 'air' ? AirIconDark : AirIconLight" alt="Air Speed" />
          </div>
          <div class="mode-icon" :class="{ active: mode === 'ground' }" @click="mode = 'ground'">
            <img :src="mode === 'ground' ? GroundIconDark : GroundIconLight" alt="Ground Speed" />
          </div>
        </div>
      </div>
    </div>
    <div id="speed-container">
      <div id="speed-gauge-wrapper">
        <template v-if="mode === 'air'">
          <img :src="AirBackground" class="gauge-background" />
          <img
            :src="Needle"
            class="gauge-needle"
            :style="{ transform: `translate(-28%, -28%) rotate(${airNeedleDeg}deg)` }"
          />
        </template>
        <template v-if="mode === 'ground'">
          <img :src="GroundBackground" class="gauge-background" />
          <img
            :src="Needle"
            class="gauge-needle"
            :style="{ transform: `translate(-28%, -28%) rotate(${groundNeedleDeg}deg)` }"
          />
        </template>
      </div>
      <div id="speed-label">
        <span class="label-title">{{ currentLabel }}:</span> {{ currentSpeed.toFixed(1) }} mph
      </div>
    </div>
  </BaseWidget>
</template>

<style scoped>
  .top-bar {
    height: 20px;
    width: 100%;
    /* background: var(--federal-blue); */
    color: var(--white);
    font-size: 9px;
  }

  .top-bar-content {
    height: 19px;
    display: flex;
    align-items: center;
    padding-left: 8px;
    padding-right: 8px;
  }

  .top-bar-icons {
    display: flex;
    flex-direction: row;
    gap: 4px;
    align-items: center;
  }

  .mode-icon {
    width: 20px;
    height: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: pointer;
    border-radius: 50%;
    padding: 2px;
    box-sizing: border-box;
    transition: background 0.15s ease;
  }

  .mode-icon img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .mode-icon.active {
    background: var(--white-smoke);
  }

  #speed-container {
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

  #speed-gauge-wrapper {
    position: relative;
    width: min(100cqw, calc(100cqh - 40px));
    height: min(100cqw, calc(100cqh - 40px));
    flex-shrink: 0;
  }

  .gauge-background {
    position: absolute;
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .gauge-needle {
    position: absolute;

    /* 78.84 / 222 ≈ 35.5%,  38.25 / 222 ≈ 17.2% */
    width: 35.5%;
    height: 17.2%;

    top: 50%;
    left: 50%;

    /*
      Adjust these percentages to match where the white
      pivot circle sits within the needle SVG.
      Start at 50%/50% and tweak from there.
    */
    transform: translate(-28%, -28%);
    transform-origin: 28% 28%;
    transition: transform 0.1s ease-out;
  }

  #speed-label {
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
