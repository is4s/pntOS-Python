import { useWidgets, activeWidgetTypes, DEFAULT_WIDGET_HEIGHT, type WidgetType } from '@/components/WidgetGrid.vue'
import type { BaseWidgetData } from '@/components/widgets/BaseWidget.vue'
import type { GridStackWidget } from 'gridstack'

interface AddWidgetOptions {
  type: WidgetType
  title?: string
  bannerStyle?: 'blue' | 'none'
  darkIcon?: string
  lightIcon?: string
  single?: boolean
  initialLayout?: GridStackWidget
  minimized?: boolean
  layout?: GridStackWidget
}

export function useWidgetActions() {
  const store = useWidgets()

  function addWidget(options: AddWidgetOptions): string | null {
    const metadata = activeWidgetTypes.find(m => m.type === options.type)
    if (!metadata) {
      console.error(`Widget type "${options.type}" not found in registry`)
      return null
    }

    const isSingle = options.single ?? metadata.single
    if (isSingle && store.numOfType(options.type) > 0) {
      console.warn(`Widget type "${options.type}" is single-instance and already exists`)
      return null
    }

    const id = "widget-" + String(Math.round(Math.random() * 1000000))

    const widget: BaseWidgetData = {
      id,
      type: options.type,
      title: options.title ?? metadata.title,
      bannerStyle: options.bannerStyle ?? metadata.bannerStyle,
      darkIcon: options.darkIcon ?? metadata.darkIcon,
      lightIcon: options.lightIcon ?? metadata.lightIcon,
      single: isSingle,
      initialLayout: options.initialLayout ?? metadata.initialLayout,
      minimized: options.minimized ?? false,
      layout: options.layout ?? options.initialLayout ?? metadata.initialLayout ?? { h: DEFAULT_WIDGET_HEIGHT }
    }

    store.set(widget)

    return id
  }

  return {
    addWidget
  }
}
