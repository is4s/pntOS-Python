<script lang="ts">
  import DashboardView from '@/views/DashboardView.vue';
  import RegistryInspectorView from '@/views/RegistryInspectorView.vue';
  import VisualizerView from '@/views/VisualizerView.vue';
  import { defineStore } from 'pinia';

  export interface Page {
    to: string,
    label: string,
    componentId: keyof typeof pageRegistry,
  }

  export const pageRegistry = {
    DashboardView,
    RegistryInspectorView,
    VisualizerView
  }

  export const pages: Array<Page> = [
    { to: "/dashboard", label: "Dashboard", componentId: "DashboardView" },
    { to: "/registry_inspector", label: "Registry Inspector", componentId: "RegistryInspectorView" },
    { to: "/visualizer", label: "Map View", componentId: "VisualizerView" }
  ]

  export const pageMetadata = defineStore('pageMetadata', {
    state: () => {
      return {
        page:
          { to: "/dashboard", label: "Dashboard", componentId: "DashboardView" } as Page
      }
    },
    actions: {
      update(cur: Page) {
        this.page = cur
      },
      get() {
        return this.page
      }
    },
    persist: true,
  })
</script>

<script setup lang="ts">
  import BottomNavBar from './BottomNavBar.vue';

  const pageMeta = pageMetadata()
</script>


<template>
  <div class="page-container">
    <div class="content">
      <component :is="pageRegistry[pageMeta.page.componentId]" />
    </div>
    <BottomNavBar />
  </div>
</template>

<style scoped>
  .page-container {
    min-height: calc(100vh - var(--header-height));
    width: 100vw;
    top: var(--header-height);
    left: 0;
    background: var(--white-smoke);
    position: absolute;
    display: flex;
    flex-direction: column;
    color: var(--black);
  }

  .content {
    min-height: calc(100vh - var(--header-height) - var(--footer-height));
  }
</style>
