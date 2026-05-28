<script lang="ts">
  import { defineStore } from "pinia"
  import type { Component } from 'vue'
  import { markRaw } from "vue"

  export const useGrid = defineStore('grid', {
    persist: {
      pick: ['gridState'],
    },
    state: () => ({
      gridState: null as null | GridStackOptions,
      grid: null as null | GridStack
    }),
    actions: {
      register(grid: GridStack) {
        this.grid = markRaw(grid)
      }
    }

  })

  export const useWidgets = defineStore('main-widget-grid', {
    state: () => ({
      widgets: new Map<string, BaseWidgetData>(),
      newWidgets: new Array<string>(),
      // grid: null as GridStack | null,
      // gridSelector: null as string | null,
    }),

    actions: {
      set(widget: BaseWidgetData) {
        if (!this.has(widget.id)) this.newWidgets.push(widget.id)
        this.widgets.set(widget.id, widget)
      },
      delete(id: string) {
        this.widgets.delete(id)
        // if (this.grid){
        //   this.grid.removeWidget(`.grid-stack-item[gs-id="${id}"]`)
        //   this.widgets.delete(id)
        // }
      },
      update(id: string, patch: Partial<BaseWidgetData>) {
        const w = this.widgets.get(id)
        if (w) {
          Object.assign(w, patch)
          this.widgets.set(id, w)
        }
      },
      get(id: string) {
        return this.widgets.get(id)
      },
      has(id: string) {
        return this.widgets.has(id)
      },
      clear() {
        this.widgets = new Map<string, BaseWidgetData>()
      },
      toggleMinimize(id: string) {
        const widget = this.get(id)
        if (!widget) return
        widget.minimized = !widget.minimized
        if (widget.minimized) {
          widget.nonMinimizedHeight = widget.layout.h
          widget.layout.h = 1
        } else {
          widget.layout.h = widget.nonMinimizedHeight
        }
      },
      getNewWidgets() {
        if (!this.newWidgets.length) return
        const out = new Array<BaseWidgetData>
        for (const id of this.newWidgets) {
          const widget = this.get(id)
          if (!widget) return
          out.push(widget)
        }
        this.newWidgets = new Array<string>()
        return out
      },
      numOfType(type: keyof typeof widgetRegistry) {
        let count = 0
        this.widgets.forEach((w) => { if (w.type === type) count++ })
        return count
      }
      // registerGrid(grid: GridStack, selector: string) {
      //   this.grid = markRaw(grid)
      //   this.gridSelector = selector
      // },
      // getGrid() {
      //   return this.grid?.save()
      // }
    },
    persist: {
      serializer: {
        serialize: (state) => {
          const out = JSON.stringify({
            widgets: Object.fromEntries(state.widgets),
          })
          return out
        },
        deserialize: (raw) => {
          const parsed = JSON.parse(raw)
          return {
            widgets: new Map(Object.entries(parsed.widgets)),
          }
        }
      },
    }

  })


  export type BannerStyle = "blue" | "none"

  export const MINIMIZED_WIDGET_HEIGHT = 28
  export const CELL_GAP = 19
  export const DEFAULT_WIDGET_HEIGHT = 5

  export interface WidgetMetadata {
    lightIcon: string
    darkIcon: string
    title: string
    single: boolean
    type: keyof typeof widgetRegistry
    bannerStyle: BannerStyle
    initialLayout?: GridStackWidget
  }

  // Type for widget module exports
  interface WidgetModule {
    default: Component
    metadata?: WidgetMetadata
  }

  const widgetModules = import.meta.glob('../components/widgets/*.vue', {
    eager: true
  })

  function getComponentName(path: string): string {
    const match = path.match(/\/widgets\/([^/]+)\.vue$/)
    return match && !(match[1] === undefined) ? match[1] : ''
  }


  type WidgetRegistryType = Record<string, Component>

  export const widgetRegistry: WidgetRegistryType = {}
  export const activeWidgetTypes: Array<WidgetMetadata> = []

  const excludePatterns = ['BaseWidget']

  for (const [path, module] of Object.entries(widgetModules)) {
    const componentName = getComponentName(path)

    if (!componentName || excludePatterns.includes(componentName)) {
      continue
    }

    const widgetModule = module as WidgetModule
    const component = widgetModule.default
    const metadata = widgetModule.metadata
    if (!metadata) {
      if (import.meta.env.DEV) {
        console.warn(
          `Widget "${componentName}" is missing metadata export.`,
          `Add a metadata export to define widget properties.`
        )
      }
      continue
    }
    widgetRegistry[componentName] = component
    activeWidgetTypes.push(metadata)
  }

  activeWidgetTypes.sort((a, b) => a.title.localeCompare(b.title))

  // Export type helpers for type safety
  export type WidgetType = keyof typeof widgetRegistry
</script>

<script setup lang="ts">
  import { GridStack, type Breakpoint, type GridStackNode, type GridStackOptions, type GridStackWidget } from 'gridstack'
  import 'gridstack/dist/gridstack.css'
  import { onBeforeUnmount, onMounted, ref, type ComponentPublicInstance } from 'vue'

  import { type BaseWidgetData } from '@/components/widgets/BaseWidget.vue'

  const gridStore = useGrid()
  const widgetStore = useWidgets()


  const cellWidth = 335; //px
  const cellHeight = MINIMIZED_WIDGET_HEIGHT; //px
  const cellGap = CELL_GAP; //px
  const maxColumns = 12;

  const gridRef = ref<HTMLElement | null>(null)
  let grid: GridStack | null = null

  // Ensures that the minimum width of a widget corresponds to the figma widget width
  const breakpoints = [] as Array<Breakpoint>;
  for (let i = 2; i <= maxColumns; i++) {
    breakpoints.push({ w: i * (cellWidth + 2 * cellGap), c: i - 1 });
  }

  function addWidget(widget: BaseWidgetData) {
    if (!gridStore.grid) return
    const el = document.getElementById(widget.id)
    if (!el) return
    gridStore.grid!.makeWidget(el)
  }

  function makeGrid() {
    grid = GridStack.init(
      {
        cellHeight: (cellHeight + 2 * cellGap),
        columnOpts: {
          breakpoints: breakpoints,
        },
        float: false,
        // animate: false,
        column: "auto",
        margin: cellGap + "px",
      },
      gridRef.value!
    )
    gridStore.register(grid)
    for (const widget of widgetStore.widgets.values()) {
      addWidget(widget)
    }

    grid.on('change', (event: Event, nodes: GridStackNode[]) => {
      for (const node of nodes) {
        if (widgetStore.has(node.id!)) {
          const gsWidget: GridStackWidget = {
            autoPosition: node.autoPosition,
            content: node.content,
            h: node.h,
            id: node.id,
            lazyLoad: node.lazyLoad,
            locked: node.locked,
            maxH: node.maxH,
            maxW: node.maxW,
            minH: node.minH,
            minW: node.minW,
            noMove: node.noMove,
            noResize: node.noResize,
            resizeToContentParent: node.resizeToContentParent,
            sizeToContent: node.sizeToContent,
            subGridOpts: node.subGridOpts,
            w: node.w,
            x: node.x,
            y: node.y,
          }
          widgetStore.update(node.id!, { layout: gsWidget })
        }
      }
    })
  }

  onMounted(() => {
    makeGrid()
  })

  function checkForUpdates(el: Element | ComponentPublicInstance | null) {
    if (!(el instanceof Element)) return
    const widget = widgetStore.get(el.id)
    if (!widget) return
    addWidget(widget)
  }

  function widgetToAttrs(widget: GridStackWidget) {
    const attrs: Record<string, string> = {}

    for (const [key, value] of Object.entries(widget)) {
      if (value === undefined || value === null) continue

      // Convert camelCase → dash-case
      const dashed = key.replace(/([A-Z])/g, '-$1').toLowerCase()

      attrs[`gs-${dashed}`] = value
    }

    return attrs
  }

  onBeforeUnmount(() => {
    if (!gridStore.grid) return
    const gridState = gridStore.grid.save(false, true, undefined, gridStore.grid.getColumn()) as GridStackOptions
    if (gridState.children) {
      for (const widget of gridState.children) {
        if (!widget.id) {
          continue
        }
        if (widgetStore.has(widget.id)) {
          widgetStore.update(widget.id, { layout: widget })
        }
      }
    }
    grid?.destroy(false)
    gridStore.grid = null
  })
</script>

<template>
  <div class="grid-stack widget-grid" ref="gridRef">
    <div v-for="item in widgetStore.widgets.values()" :id="item.id" :key="item.id" v-bind="widgetToAttrs(item.layout)"
         :gs-id="item.id" class="grid-stack-item" :ref="checkForUpdates">
      <div class="grid-stack-item-content">
        <component :is="widgetRegistry[item.type]" v-bind="item" :id="item.id" />
      </div>
    </div>
  </div>
</template>

<style lang="css" scoped>
  .widget-grid {
    height: 100%;
    width: 100%;
  }

  .grid-stack-item-content {
    background: var(--white);
    border-radius: 10px;
    box-shadow: 4px 4px 4px 0px rgba(0, 0, 0, 0.05);
  }
</style>
