<script lang="ts">
  import type { GridStackWidget } from "gridstack";
  import type { WidgetMetadata } from "../WidgetGrid.vue";

  export interface BaseWidgetData extends WidgetMetadata {
    minimized: boolean,
    id: string,
    layout: GridStackWidget
    nonMinimizedHeight?: number
    onClose?: (remove: () => void) => void
  }
</script>

<script setup lang="ts">

  // Widget Button Icons
  import ExitDarkBackgroundIcon from "@/assets/branding/svgs/widgets/ExitDarkBackground.svg";
  import ExitLightBackgroundIcon from "@/assets/branding/svgs/widgets/ExitLightBackground.svg";
  import MaximizeDarkBackgroundIcon from "@/assets/branding/svgs/widgets/MaximizeDarkBackground.svg";
  import MaximizeLightBackgroundIcon from "@/assets/branding/svgs/widgets/MaximizeLightBackground.svg";
  import MinimizeDarkBackgroundIcon from "@/assets/branding/svgs/widgets/MinimizeDarkBackground.svg";
  import MinimizeLightBackgroundIcon from "@/assets/branding/svgs/widgets/MinimizeLightBackground.svg";
  import { useGrid, useWidgets } from "@/components/WidgetGrid.vue";
  import { onMounted } from "vue";


  const props = defineProps<BaseWidgetData>()

  const style = {
    minimizeButton: props.bannerStyle === 'none' ? MinimizeLightBackgroundIcon : MinimizeDarkBackgroundIcon,
    maximizeButton: props.bannerStyle === 'none' ? MaximizeLightBackgroundIcon : MaximizeDarkBackgroundIcon,
    exitButton: props.bannerStyle === 'none' ? ExitLightBackgroundIcon : ExitDarkBackgroundIcon,
  }

  const store = useWidgets()
  const gridStore = useGrid()

  function toggleMinimize() {
    store.toggleMinimize(props.id)
    const widget = store.get(props.id)
    if (!widget) return
    if (gridStore.grid) {
      gridStore.grid.batchUpdate(true)
      gridStore.grid.update(`#${props.id}`, widget.layout)
      gridStore.grid.batchUpdate(false)
    }
  }

  function removeWidget() {
    gridStore.grid?.removeWidget(`grid-stack-item[gs-id=${props.id}]`)
    store.delete(props.id)
  }
  function handleExit() {
    if (props.onClose) {
      props.onClose(removeWidget)
    }
    else {
      removeWidget()
    }
  }

  onMounted(() => {
    if (!store.has(props.id)) {
      store.set(props)
    }
  })

</script>

<template>
  <div class="widget-container" :class="minimized ? 'no-overflow' : ''">
    <div class="widget-buttons-container" :class="minimized ? 'widget-buttons-minimized-hover' : ''">
      <div class="widget-button" @click="toggleMinimize">
        <img :src="minimized ? style['minimizeButton'] : style['maximizeButton']" />
      </div>
      <div class="widget-button" @click="handleExit">
        <img :src="style['exitButton']" />
      </div>
    </div>
    <div v-if="bannerStyle === 'blue'">
      <div class="widget-title-blue">{{ title }}</div>
    </div>
    <div v-if="!minimized">
      <slot></slot>
    </div>
    <div v-else-if="bannerStyle === 'none'">
      <slot name="minimized-content"></slot>
    </div>
  </div>
</template>

<style lang="css" scoped>
  .widget-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .no-overflow {
    overflow-y: None;
  }

  .widget-buttons-container {
    position: absolute;
    width: 45px;
    height: 20px;
    right: 4px;
    top: 4px;
    display: flex;
    flex-direction: row;
    justify-content: start;
    justify-items: center;
    align-items: center;
    align-content: center;
    gap: 5px;
    transition: width 0.1s ease;
  }

  .widget-container:hover>.widget-buttons-minimized-hover {
    width: calc(45px + 20px) !important;
  }

  .widget-button {
    width: 20px;
    height: 20px;
    display: flex;
    justify-content: center;
    align-content: center;
    align-items: center;
    justify-items: center;
    transition: filter 100ms ease-out
  }

  .widget-button:hover {
    cursor: pointer;
    filter: brightness(95%)
  }

  .widget-button:active {
    filter: brightness(70%)
  }

  .widget-title-blue {
    height: 27px;
    width: 100%;
    background: var(--federal-blue);
    color: var(--white);
    font-weight: 900;
    font-size: 14px;
    padding-left: 9px;
    display: flex;
    align-items: center;

  }
</style>
