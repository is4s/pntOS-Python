import type {
  BatchUpdate,
  ChunkUpdate,
  CobraUiSocketInterface,
  RegistryValueType,
  ShadowRegistry,
  ShadowRegistryEntry,
  Snapshot,
  Write,
} from '@/types'
import { SubscriptionMode } from '@/types'
import { io } from 'socket.io-client'
import { v4 as newUUID } from 'uuid'
import {
  computed,
  effectScope,
  nextTick,
  onMounted,
  onUnmounted,
  readonly,
  ref,
  shallowReactive,
  watchEffect,
  type ComputedRef,
  type Ref,
} from 'vue'
import { SequenceBuffer } from './SequenceBuffer'

const socket: CobraUiSocketInterface = io()

const connectionState = ref<'connected' | 'connecting' | 'disconnected' | 'error'>('connecting')
const connectionError = ref<string | null>(null)

socket.on('connect_error', (error: Error) => {
  console.error('Socket connection error:', error.message)
  connectionState.value = 'error'
  connectionError.value = error.message
})

socket.on('connect_timeout', () => {
  console.warn('Socket connection timeout')
  connectionState.value = 'error'
  connectionError.value = 'Connection timeout'
})

socket.on('error', (error: Error) => {
  console.error('Socket error:', error.message)
  connectionError.value = error.message
})

socket.on('reconnect_attempt', (attemptNumber: number) => {
  console.log(`Reconnection attempt ${attemptNumber}`)
  connectionState.value = 'connecting'
})

socket.on('reconnect_failed', () => {
  console.error('Reconnection failed')
  connectionState.value = 'error'
  connectionError.value = 'Reconnection failed'
})

/* Essentially a Group -> Key -> Value Ref registry.
 * The value Ref would ideally be synced with the back-end value at that group-key in
 * the registry. Writes to the ref at this group-key in the shadow registry will be
 * communicated to the back-end as writes to the registry.
 */
const shadowRegistry: ShadowRegistry = shallowReactive(new Map())

// Flag to prevent feedback loops when backend applies updates
let isApplyingBackendUpdate = false

function ensureGroup(group: string): Map<string, ShadowRegistryEntry> {
  if (!shadowRegistry.has(group)) {
    shadowRegistry.set(group, shallowReactive(new Map()))
  }
  return shadowRegistry.get(group)!
}

const globalEffectScope = effectScope(true)

function ensureValue<T = RegistryValueType>(
  group: string,
  key: string,
): ShadowRegistryEntry<T | null> {
  const g = ensureGroup(group)
  if (!g.has(key)) {
    const newRef = ref<RegistryValueType | null>(null)
    const entry: ShadowRegistryEntry = {
      val: newRef,
      subscriptions: new Map(),
    }
    globalEffectScope.run(() => {
      watchEffect(() => {
        // Only add to write batch if this is a user-initiated change, not a backend
        // update
        if (entry.val.value !== null && !isApplyingBackendUpdate) {
          if (!writeBatch.has(group)) {
            writeBatch.set(group, new Map())
          }
          writeBatch.get(group)!.set(key, entry.val.value)
        }
      })
    })
    g.set(key, entry)
  }
  return g.get(key)! as ShadowRegistryEntry<T | null>
}

export function useRegistry<T = RegistryValueType>(
  group: string,
  key: string,
  mode: SubscriptionMode = SubscriptionMode.LAST,
): Ref<T | null> {
  const entry = ensureValue<T>(group, key)
  const subscription = { group: group, key: key, id: newUUID(), mode: mode }

  onMounted(() => {
    entry.subscriptions.set(subscription.id, subscription)
    socket.emit('subscribe', subscription)
  })
  onUnmounted(() => {
    entry.subscriptions.delete(subscription.id)
    socket.emit('unsubscribe', subscription)
  })
  return entry.val
}

let sendTimer: number | null = null

const connected = ref(false)

let writeSequenceId: number = 0
let writeBuff: Write[] = []
let writeBatch: Map<string, Map<string, RegistryValueType>> = new Map()

function sendUpdates(): Write[] {
  if (!writeBatch.size) {
    return []
  }
  const newSequenceId: number = writeSequenceId
  writeSequenceId += 1
  const newData = new Map(writeBatch)
  writeBatch = new Map()

  const dataObj: Record<string, Record<string, RegistryValueType>> = {}
  newData.forEach((innerMap, group) => {
    const groupObj: Record<string, RegistryValueType> = {}
    innerMap.forEach((value, key) => {
      groupObj[key] = value
    })
    dataObj[group] = groupObj
  })
  const newWrite: Write = { data: dataObj, sequence_id: newSequenceId }
  writeBuff.push(newWrite)
  if (connected.value) {
    const out = [...writeBuff]
    writeBuff = []
    return out
  } else {
    return []
  }
}

function resubscribe(): void {
  shadowRegistry.forEach((keyVal) => {
    keyVal.forEach((entry) => {
      entry.subscriptions.forEach((subscription) => {
        socket.emit('subscribe', subscription)
      })
    })
  })
}

function unsubscribe(): void {
  shadowRegistry.forEach((keyVal) => {
    keyVal.forEach((entry) => {
      entry.subscriptions.forEach((subscription) => {
        socket.emit('unsubscribe', subscription)
      })
    })
  })
}

socket.on('connect', () => {
  console.log('Socket connected')
  connectionState.value = 'connected'
  connectionError.value = null
  connected.value = true
  resubscribe()
  if (sendTimer === null) {
    sendTimer = setInterval(() => {
      sendUpdates().forEach((write) => {
        socket.emit('write', write)
      })
    }, 33)
  }
})

socket.on('disconnect', (reason: string) => {
  console.warn('Socket disconnected:', reason)
  connectionState.value = 'disconnected'
  connected.value = false
  unsubscribe()
  if (sendTimer) clearInterval(sendTimer)
  sendTimer = null
})

const batchBuffer = new SequenceBuffer<BatchUpdate>((batch: BatchUpdate) => batch.sequence_id)

function chunkUpdate(updates: ChunkUpdate): void {
  isApplyingBackendUpdate = true
  try {
    batchBuffer.addMultiple(updates.ordered_updates).forEach((update) => {
      Object.entries(update.keys).forEach(([key, value]) => {
        const entry = ensureValue(update.group, key)
        entry.val.value = value.val // TODO: use value metadata?
      })
    })
    Object.entries(updates.unordered_updates).forEach(([group, keyVal]) => {
      Object.entries(keyVal).forEach(([key, value]) => {
        const entry = ensureValue(group, key)
        entry.val.value = value.val // TODO: use value metadata?
      })
    })
  } finally {
    nextTick(() => {
      isApplyingBackendUpdate = false
    })
  }
}

function applySnapshot(snapshot: Snapshot): void {
  isApplyingBackendUpdate = true
  try {
    Object.entries(snapshot.data).forEach(([group, keyValue]) => {
      Object.entries(keyValue).forEach(([key, value]) => {
        const entry = ensureValue(group, key)
        entry.val.value = value
      })
    })
    // Set all group-key-vals not in snapshot to `null`
    shadowRegistry.forEach((keyValue, group) => {
      const snapshotGroup = snapshot.data[group]
      if (!snapshotGroup) {
        keyValue.forEach((entry) => {
          entry.val.value = null
        })
      } else {
        keyValue.forEach((entry, key) => {
          if (!(key in snapshotGroup)) {
            entry.val.value = null
          }
        })
      }
    })
  } finally {
    nextTick(() => {
      isApplyingBackendUpdate = false
    })
  }
}

socket.on('snapshot', (snapshot: Snapshot) => {
  applySnapshot(snapshot)
})

socket.on('chunkUpdate', (chunk: ChunkUpdate) => {
  chunkUpdate(chunk)
})

export function useGroups(): Ref<string[] | null> {
  const groups = useRegistry<string[]>('ui/metadata', 'groups', SubscriptionMode.LAST)
  return groups
}

export function useGroupsWithRegex(regex: string): ComputedRef<string[]> {
  const pattern = new RegExp(regex)
  const groups = useGroups()

  return computed(() => {
    if (!groups.value) return []
    return groups.value.filter((val) => pattern.test(val))
  })
}

export const UI_CHANNELS_PREFIX = 'ui/channel/'

export function channelFromGroup(group: string) {
  return group.replace(UI_CHANNELS_PREFIX, '')
}

export function useChannels(): ComputedRef<string[]> {
  const channel_groups = useGroupsWithRegex(UI_CHANNELS_PREFIX + '.*')

  return computed(() => {
    return channel_groups.value.map((group) => channelFromGroup(group))
  })
}

export function useConnectionState() {
  return {
    connectionState: readonly(connectionState),
    connectionError: readonly(connectionError),
  }
}
