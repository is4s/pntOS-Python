<script lang="ts">
  import { defineStore } from 'pinia';

  export const useDashboardSidebar = defineStore('dashboard-sidebar', {
    state: () => {
      return {
        collapsed: false,
      }
    },
    persist: true,
  })
</script>

<script setup lang="ts">
  import { activeWidgetTypes } from '@/components/WidgetGrid.vue';
  import { onBeforeUnmount, onMounted, ref } from 'vue';
  import SideBarButton from './SideBarButton.vue';

  const store = useDashboardSidebar()
  const root = ref<HTMLElement | null>(null)

  function handleClickOutside(e: MouseEvent) {
    if (root.value && !root.value.contains(e.target as Node) && !store.collapsed) {
      store.collapsed = !store.collapsed
    }
  }
  function mouseLeave() {
    store.collapsed = true
  }

  onMounted(() => {
    document.addEventListener('click', handleClickOutside)
  })

  onBeforeUnmount(() => {
    document.removeEventListener('click', handleClickOutside)
  })
</script>

<template>
  <aside class="widget-sidebar" :class="{ collapsed: store.collapsed }" ref="root" @mouseleave="mouseLeave()">
    <div class="sidebar-label">Add Widgets</div>
    <div class="sidebar-grid">
      <div v-for="info in activeWidgetTypes" :key="info.title">
        <SideBarButton v-bind="info" />
      </div>
    </div>
  </aside>
</template>

<style lang="css" bound>
  .widget-sidebar {
    top: 0;
    left: 0;
    min-height: calc(100vh - var(--header-height) - var(--footer-height));
    width: 199px;
    box-shadow: 4px 0px 4px 4px rgba(0, 0, 0, 0.05);
    transition: 300ms ease-out;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
    position: absolute;
    z-index: 10;
    background-color: var(--white-smoke);
    padding: 14px;
  }

  .collapsed {
    left: -199px;
    box-shadow: none;
  }

  .sidebar-label {
    font-weight: 900;
    font-size: 16px;
    margin-bottom: 13px;
    margin-left: 2px;
  }

  .sidebar-grid {
    display: flex;
    flex-direction: column;
    height: 22px;
    width: 100%;
    gap: 7px;
    font-size: 9px;
  }
</style>
