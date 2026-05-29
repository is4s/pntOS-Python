<script setup lang="ts">
  interface Props {
    dark?: boolean
  }
  defineProps<Props>()
  const emit = defineEmits(['click'])
</script>

<template>
  <div :class="['hover-button', dark ? 'dark' : 'light']" @click="emit('click')">
    <slot></slot>
  </div>
</template>

<style lang="css" scoped>
  .hover-button {
    position: relative;
    z-index: 0;
    cursor: pointer;
  }


  .hover-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -3px;
    right: -3px;
    bottom: 0;
    border-radius: 10px;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: -1;
  }

  .hover-button:hover::before {
    opacity: 1;
  }

  .dark::before {
    background: var(--hover-violet-dark);
  }

  .light::before {
    background: var(--hover-violet-light);
  }
</style>
