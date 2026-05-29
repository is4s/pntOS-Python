<script setup lang="ts">
  import SideBarHoverIcon from '@/assets/branding/svgs/pages/dashboard/sidebar_open_icon.svg';
  import WidgetGrid from '@/components/WidgetGrid.vue';
  import WidgetSideBar, { useDashboardSidebar } from '@/components/WidgetSideBar.vue';

  const store = useDashboardSidebar()

  const toggleSidebar = () => {
    store.collapsed = !store.collapsed
  }
</script>

<template>
  <div class="dashboard-container">
    <WidgetSideBar></WidgetSideBar>
    <div class="dashboard-center-container">
      <div class="dashboard-buttons">
        <div class="dashboard-buttons-left"> <img :src="SideBarHoverIcon" class="sidebar-hover"
               @mouseenter="toggleSidebar()" /></div>
        <div class="dashboard-buttons-right">
        </div>

      </div>

      <WidgetGrid></WidgetGrid>
    </div>

  </div>
</template>

<style lang="css" scoped>
  .dashboard-container {
    display: flex;
    flex-direction: row;
    z-index: 0;
    width: 100vw;
  }

  .dashboard-center-container {
    display: flex;
    flex-direction: column;
    width: 100vw;
  }

  .dashboard-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr;
    padding: 20px;
  }

  .dashboard-buttons-left {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 4px;
  }

  .dashboard-buttons-right {
    display: flex;
    flex-direction: row-reverse;
    align-items: center;
    gap: 4px;
  }

</style>
