<script setup lang='ts'>
  import NavBarButton from './NavBarButton.vue';
  import { pages } from './PageArea.vue';
</script>

<template>
  <div class="navbar">
    <img src="@/assets/branding/Cobra_Logo-Standards_Horizontal-White-NoTagline_Vers1.png" alt="Cobra: powered by pntOS"
         class="navbar-logo" />
    <div class="navbar-page-buttons">
      <NavBarButton v-for="page in pages!" :key="page.label" :page />
    </div>
  </div>
</template>

<style bound>
  .navbar {
    min-width: 100vw;
    height: var(--header-height);
    top: 0;
    left: 0;
    background: linear-gradient(90deg, var(--dark-violet) 0%, var(--dark-violet-gradient) 100%);
    display: flex;
    position: absolute;
    justify-content: space-between;
    align-items: center;
  }

  .navbar-logo {
    width: 210px;
    height: 70%;
    margin-left: 30px;
    margin-right: 30px;
  }

  .navbar-page-buttons {
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-width: 350px;
    margin-left: 30px;
    height: 100%;
  }
</style>
