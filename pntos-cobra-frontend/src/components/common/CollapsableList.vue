<script setup lang="ts">
  import CollapsedIcon from '@/assets/branding/svgs/collapsed-list.svg';
  import ExpandedIcon from '@/assets/branding/svgs/expanded-list.svg';
  import { computed, type ComponentPublicInstance } from 'vue';

  declare type ListInfo = {
    listTitle: string,
    items: Array<string>,
    emptyMessage: string,
    collapsed: boolean,
    toggleCollapseCallback: () => void,
    maxH?: number,
  }
  const props = defineProps<ListInfo>()

  const icon = computed(() => props.collapsed ? CollapsedIcon : ExpandedIcon)

  function setItemRef(el: Element | ComponentPublicInstance | null) {
    if (!el || !(el instanceof Element)) return
    el.classList.add("enter")
  }

</script>

<template>
  <div class="cobra-ui-collapsible-list">
    <ul class="cobra-ui-list" :class="collapsed ? 'cobra-ui-list-collapsed' :
      ''" :style="maxH ? 'max-height: ' + String(maxH) + 'px;' : ''">
      <li class="cobra-ui-list-title-item">
        <div class="cobra-ui-list-title">{{ listTitle }}</div>
        <div class="cobra-ui-list-collapse-button clickable-button centered" @click="toggleCollapseCallback()">
          <img :src="icon" />
        </div>
      </li>
      <div v-if="!collapsed">
        <div v-if="items.length">
          <div v-for="item in items" :key="item" :ref="setItemRef">
            <li class="cobra-ui-list-item">{{ item }}</li>
          </div>
        </div>
        <div v-else>
          <li class="cobra-ui-list-no-list-items" :ref="setItemRef">{{ emptyMessage }}</li>
        </div>
      </div>
    </ul>
  </div>
</template>

<style lang="css" scoped>
  .cobra-ui-collapsible-list {
    background: var(--white-smoke);
    border-radius: 2px;
  }

  .cobra-ui-list-collapsed {
    padding-bottom: 0px !important;
  }

  .cobra-ui-list {
    margin: 0;
    list-style-type: none;
    padding-top: 0px;
    padding-left: 5px;
    padding-right: 5px;
    padding-bottom: 5px;
    gap: 3px;
    overflow-y: auto;
  }

  .cobra-ui-list-item {
    background: var(--white);
    border-radius: 2px;
    color: #686868;
    font-weight: 400;
    font-size: 9px;
    margin-bottom: 3px;
    height: 14px;
    padding-left: 2px;
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-content: center;
    overflow-x: auto;
  }


  .cobra-ui-list-no-list-items {
    color: #686868;
    font-weight: 400;
    font-size: 9px;
    height: 14px;
    padding-left: 2px;
    display: flex;
    flex-direction: row;
    justify-content: start;
    align-content: center;
  }

  .cobra-ui-list-title-item {
    font-weight: bold;
    color: var(--black);
    font-size: 10px;
    padding-left: 0px;
    padding-top: 2px;
    padding-bottom: 2px;
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
  }

  .cobra-ui-list-collapse-button {
    width: 12px;
    height: 12px;
    right: 2px;
    top: 2px;
  }


</style>
