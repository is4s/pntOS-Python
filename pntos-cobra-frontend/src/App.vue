<script setup lang="ts">
  import NavBar from './components/NavBar.vue';
  import PageArea from './components/PageArea.vue';

</script>

<template>
  <div class="app-container">
    <NavBar />
    <PageArea />
  </div>
</template>

<style scoped>
  .app-container {
    width: 100vw;
    min-height: 100vh;
    left: 0;
    top: 0;
    display: flex;
    flex-direction: column;
    margin: 0;
    overflow-y: scroll;
  }
</style>
