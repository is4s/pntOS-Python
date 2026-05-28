<script setup lang='ts'>
  import { type Page, pageMetadata } from './PageArea.vue';

  const pageMeta = pageMetadata()

  const props = defineProps({ page: Object as () => Page })

  function update() {
    pageMeta.update(props.page!)
  }

</script>


<template>
  <div @click="update" class="navbar-button default-font">{{ page!.label }}</div>
</template>

<style bound>
  .navbar-button {
    height: var(--header-height);
    line-height: 150%;
    padding-left: 30px;
    padding-right: 30px;

    /*background and border specifications*/
    color: var(--white-smoke);
    background: none;
    border: none;
    display: flex;
    align-content: center;
    justify-content: center;
    align-items: center;
    justify-items: center;
    text-decoration: none;
    transition: box-shadow 0.1s ease-out;
  }

  .navbar-button:link,
  .navbar-button:visited {
    text-decoration: none;
  }

  .navbar-button:hover {
    cursor: pointer;
    background: var(--white-smoke);
    color: var(--dark-violet);
    box-shadow: 0.3em 0.3em 1em rgb(0, 0, 0, 0.3);
  }

  .navbar-button:active {
    box-shadow: none;
  }
</style>
