import { computed, type ComputedRef, type Ref } from 'vue'
import { useRegistry } from './useRegistry'

const MessageTypeToShortName = new Map<string, string>([
  ['MeasurementPositionVelocityAttitude', 'PVA'],
  ['MeasurementPosition', 'Position'],
  ['MeasurementImu', 'IMU'],
  ['MeasurementBarometer', 'Baro'],
  ['MeasurementDirection3DToPoints', 'Dir3DToPoints'],
])

export function useShortenedMessage(messageType: Ref<string>): ComputedRef<string> {
  return computed(() => {
    if (MessageTypeToShortName.has(messageType.value))
      return MessageTypeToShortName.get(messageType.value)!
    return messageType.value.replace('Measurement', '')
  })
}

export function useRegistryMessageType(group: string, key: string): ComputedRef<string> {
  const type = useRegistry<string>(group, key)
  return useShortenedMessage(computed(() => type.value ?? 'Unknown'))
}
