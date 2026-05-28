import { Socket } from 'socket.io-client'
import type { Ref } from 'vue'

type UUID4 = string

export enum SubscriptionMode {
  ALL = 'all',
  LAST = 'last',
}

/**
 * Registry value types that can be deserialized from frontend
 */
export type RegistryValueType = string | string[] | number | boolean | number[] // TODO: support messages in some fashion

export interface Subscription {
  id: UUID4
  group: string
  key: string
  mode: SubscriptionMode
}
export interface KeyUpdate {
  val: RegistryValueType
  subscription_ids: UUID4[]
  sequence_id: number
}

export interface BatchUpdate {
  sequence_id: number
  group: string
  keys: Record<string, KeyUpdate>
}

export interface ChunkUpdate {
  ordered_updates: BatchUpdate[]
  unordered_updates: Record<string, Record<string, KeyUpdate>>
}

export interface Snapshot {
  data: Record<string, Record<string, RegistryValueType>>
}

export interface Write {
  data: Record<string, Record<string, RegistryValueType>>
  sequence_id: number
}

export interface ShadowRegistryEntry<T = RegistryValueType> {
  val: Ref<T | null>
  subscriptions: Map<UUID4, Subscription>
}

export type ShadowRegistry = Map<string, Map<string, ShadowRegistryEntry>>

interface ServerToClientEvents {
  chunkUpdate: (chunk: ChunkUpdate) => void
  snapshot: (snapshot: Snapshot) => void
  connect_error: (error: Error) => void
  connect_timeout: () => void
  error: (error: Error) => void
  reconnect_attempt: (attemptNumber: number) => void
  reconnect_failed: () => void
}

interface ClientToServerEvents {
  subscribe: (subscription: Subscription) => void
  unsubscribe: (subscription: Subscription) => void
  write: (batch: Write) => void
}

export type CobraUiSocketInterface = Socket<ServerToClientEvents, ClientToServerEvents>
