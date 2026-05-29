<script setup lang="ts">
  import { useWidgets } from '@/components/WidgetGrid.vue';
  import type { WidgetMetadata } from './WidgetGrid.vue';
  import { useWidgetActions } from '@/utils/useWidgetActions';

  const props = defineProps<WidgetMetadata>()

  const store = useWidgets()
  const { addWidget } = useWidgetActions()

  function maxWidgetInstances() {
    return props.single && store.numOfType(props.type) > 0
  }

  function add() {
    if (maxWidgetInstances()) return
    addWidget({ type: props.type })
  }
</script>

<template>
  <div class="container" :class="maxWidgetInstances() ? '' : 'container-not-maxed'" @click="add">
    <div v-if="!maxWidgetInstances()">
      <img :src="props.darkIcon" />
    </div>
    <div v-else>
      <img :src="props.lightIcon" />
    </div>
    {{ props.title }}
  </div>

</template>

<style lang="css" scoped>
  .container {
    width: 100%;
    border-radius: 4px;
    display: flex;
    align-content: center;
    align-items: center;
    gap: 6px;
    color: var(--white);
    background: var(--federal-blue);
    padding: 4px;
    transition: background 0.2s ease, color 0.2s ease;
  }

  .container-not-maxed {
    background: var(--platinum);
    color: var(--black);
  }

  .container-not-maxed:hover {
    cursor: pointer;
    filter: drop-shadow(0px 0px 1px var(--federal-blue))
  }

  .icon {
    fill: var(--federal-blue)
  }
</style>
