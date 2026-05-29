import { useIntervalFn } from '@vueuse/core'
import { ref, type Ref } from 'vue'

export interface Timer {
  time: Ref<number>
  reset: () => void
}
export function useTimer(updateInterval: number = 0.1): Timer {
  const time = ref<number>(0)
  const { pause, resume } = useIntervalFn(() => {
    if (time.value === null) time.value = 0
    time.value += updateInterval
  }, updateInterval * 1000)
  function reset() {
    time.value = 0
    pause()
    resume()
  }
  return { time, reset }
}
