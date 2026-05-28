<script lang="ts">
  import { defineStore } from 'pinia';

  export const useLandAir = defineStore('land-air', {
    state: () => {
      return {
        land: true,
      }
    },
    persist: true,
  })
</script>

<script setup lang="ts">
  import AirDarkIcon from '@/assets/branding/svgs/pages/dashboard/air_icon_dark.svg';
  import AirLightIcon from '@/assets/branding/svgs/pages/dashboard/air_icon_light.svg';
  import LandDarkIcon from '@/assets/branding/svgs/pages/dashboard/land_icon_dark.svg';
  import LandLightIcon from '@/assets/branding/svgs/pages/dashboard/land_icon_light.svg';

  type LandAirProps = {
    style: 'wide' | 'small',
    direction: 'row' | 'column',
  }

  defineProps<LandAirProps>()

  const store = useLandAir()

  function toAir() {
    if (!store.land) return
    store.land = false
  }

  function toLand() {
    if (store.land) return
    store.land = true
  }
</script>

<template>
  <div class="air-land-container" :class="'air-land-' + direction">
    <div class="air-land-button" @click="toAir()"
         :class="[store.land ? 'air-land-light' : 'air-land-dark', 'air-land-' + style]">
      <div v-if="!store.land" class="air-land-icon">
        <img :src="AirLightIcon" />
      </div>
      <div v-else class="air-land-icon">
        <img :src="AirDarkIcon" />
      </div>
      <div v-if="style! === 'wide'">
        <div class="air-land-caption">
          <text>Air</text>
        </div>
      </div>
    </div>
    <div class="air-land-button" @click="toLand()"
         :class="[store.land ? 'air-land-dark' : 'air-land-light', 'air-land-' + style]">
      <div v-if="store.land" class="air-land-icon">
        <img :src="LandLightIcon" />
      </div>
      <div v-else class="air-land-icon">
        <img :src="LandDarkIcon" />
      </div>
      <div v-if="style! === 'wide'">
        <div class="air-land-caption">
          <text>Ground</text>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="css" scoped>
  .air-land-container {
    display: flex;
    gap: 4px;
    font-size: 14px;
  }

  .air-land-row {
    flex-direction: row;
  }

  .air-land-column {
    flex-direction: column;
  }

  .air-land-button {
    height: 20px;
    transition: background 0.1s ease, color 0.2s ease;
    border-radius: 100px;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: center;
  }

  .air-land-dark {
    background: var(--federal-blue);
    color: var(--white);
  }

  .air-land-light {
    background: var(--platinum);
    color: var(--federal-blue);
  }

  .air-land-light:hover {
    cursor: pointer;
    filter: drop-shadow(0px 0px 1px var(--federal-blue))
  }

  .air-land-wide {
    width: 93px;
  }

  .air-land-icon {
    width: 20px;
    height: 20px;
    display: flex;
    justify-content: center;
    align-items: center;
    justify-content: center;
  }

  .air-land-caption {
    width: 73px;
    display: flex;
    justify-content: center;
    align-items: center;
    justify-items: center;
    align-content: center;
  }

  .air-land-small {
    width: 20px;
  }
</style>
