<script setup lang="ts">
  interface ChannelHealthIndicatorProps {
    tSinceLastMessage: number
  }

  defineProps<ChannelHealthIndicatorProps>()

  const HEALTHY_COLOR = 0x44A842
  const SICKLY_COLOR = 0xCCA629
  const DEADLY_COLOR = 0xC33436
  const HEALTH_THRESHOLD = 0 // sec
  const SICKLY_THRESHOLD = 5 // sec
  const DEADLY_THRESHOLD = 60 // sec

  function updateColor(tSinceLastMessage: number) {
    if (tSinceLastMessage >= DEADLY_THRESHOLD) {
      return `#${DEADLY_COLOR.toString(16).padStart(6, '0')}`
    }

    let color1, color2, t

    if (tSinceLastMessage <= SICKLY_THRESHOLD) {
      color1 = HEALTHY_COLOR
      color2 = SICKLY_COLOR
      t = (tSinceLastMessage - HEALTH_THRESHOLD) / (SICKLY_THRESHOLD - HEALTH_THRESHOLD)
    } else {
      color1 = SICKLY_COLOR
      color2 = DEADLY_COLOR
      t = (tSinceLastMessage - SICKLY_THRESHOLD) / (DEADLY_THRESHOLD - SICKLY_THRESHOLD)
    }

    t = Math.max(0, Math.min(1, t))

    const r1 = (color1 >> 16) & 0xFF
    const g1 = (color1 >> 8) & 0xFF
    const b1 = color1 & 0xFF

    const r2 = (color2 >> 16) & 0xFF
    const g2 = (color2 >> 8) & 0xFF
    const b2 = color2 & 0xFF

    const r = Math.round(r1 + (r2 - r1) * t)
    const g = Math.round(g1 + (g2 - g1) * t)
    const b = Math.round(b1 + (b2 - b1) * t)

    const out = (r << 16) | (g << 8) | b
    return `#${out.toString(16).padStart(6, '0')}`
  }
</script>

<template>
  <div class="health-indicator" :style="`background: ${updateColor(tSinceLastMessage)}`"></div>
</template>

<style lang="css" scoped>
  .health-indicator {
    width: 10px;
    height: 10px;
    border-radius: 100%;
    border: 1px solid var(--federal-blue);
  }
</style>
