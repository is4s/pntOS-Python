<script setup lang="ts">
  interface RadioSwitchProps {
    val: boolean
    callback: (event: PointerEvent) => void
  }

  defineProps<RadioSwitchProps>()
</script>

<template>
  <div class="background" :class="val ? 'background-true' : ''" @click="callback">
    <div class="foreground" :class="val ? 'foreground-true' : ''"></div>
  </div>
</template>

<style lang="css" scoped>
  .background {
    width: 20px;
    height: 9px;
    border-radius: 4px;
    background: var(--platinum);
    transition: background 0.1s ease-out;
    cursor: pointer;
    position: relative;
  }

  .background-true {
    background: var(--federal-blue) !important;
  }

  .foreground {
    width: 7px;
    height: 7px;
    background: var(--white);
    border-radius: 100%;
    position: absolute;
    top: 1px;
    left: 1px;
    transition: left 0.1s ease-out;
  }

  .foreground:active {
    background: var(--white-smoke);
  }

  .foreground-true {
    left: 12px;
  }
</style>
