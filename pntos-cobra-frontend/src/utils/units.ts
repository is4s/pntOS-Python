import { SubscriptionMode } from '@/types'
import { computed, type ComputedRef, ref, type Ref, watch } from 'vue'
import { useRegistry } from './useRegistry'

/**
 * A reactive representation of a number for arbitrary units. For example, if
 * ``rawNumber=12_345``, ``rawUnit='Hz'``, and ``decimals=2``, then ``number=12.34``
 * and ``unit='KHz'``
 */
export interface NumberWithUnitRef<T extends number | number | null = number> {
  number: ComputedRef<number>
  renderedUnit: ComputedRef<string>
  unit: ComputedRef<UnitPrefix>
  rawUnit: string
  rawNumber: Ref<T>
}

export type UnitPrefix = 'T' | 'B' | 'M' | 'K' | '' | 'm' | 'u' | 'n' | 'p'
export type UnitScale =
  | 1_000_000_000_000
  | 1_000_000_000
  | 1_000_000
  | 1_000
  | 1
  | 0.001
  | 0.000_001
  | 0.000_000_001
  | 0.000_000_000_001

const UnitScaleToUnitPrefix = new Map<UnitScale, UnitPrefix>([
  [1_000_000_000_000, 'T'],
  [1_000_000_000, 'B'],
  [1_000_000, 'M'],
  [1_000, 'K'],
  [1, ''],
  [0.001, 'm'],
  [0.000_001, 'u'],
  [0.000_000_001, 'n'],
  [0.000_000_000_001, 'p'],
])

export const InverseUnitPrefix = new Map<UnitPrefix, UnitPrefix>([
  ['p', 'T'],
  ['n', 'B'],
  ['u', 'M'],
  ['m', 'K'],
  ['', ''],
  ['K', 'm'],
  ['M', 'u'],
  ['B', 'n'],
  ['T', 'p'],
])

const IncreasingScale = new Map<UnitScale, UnitScale>([
  [0.000_000_000_001, 0.000_000_001],
  [0.000_000_001, 0.000_001],
  [0.000_001, 0.001],
  [0.001, 1],
  [1, 1_000],
  [1_000, 1_000_000],
  [1_000_000, 1_000_000_000],
  [1_000_000_000, 1_000_000_000_000],
])

const DecreasingScale = new Map<UnitScale, UnitScale>([
  [0.000_000_001, 0.000_000_000_001],
  [0.000_001, 0.000_000_001],
  [0.001, 0.000_001],
  [1, 0.001],
  [1_000, 1],
  [1_000_000, 1_000],
  [1_000_000_000, 1_000_000],
  [1_000_000_000_000, 1_000_000_000],
])

export interface NumberWithUnit {
  moddedNumber: number
  unitPrefix: UnitPrefix
}

export function getScale(n: number): UnitScale {
  const absN = Math.abs(n)
  if (absN === 0) return 1
  let scale: UnitScale
  if (absN >= 1) {
    scale =
      absN < 1_000
        ? 1
        : absN < 1_000_000
          ? 1_000
          : absN < 1_000_000_000
            ? 1_000_000
            : absN < 1_000_000_000_000
              ? 1_000_000_000
              : 1_000_000_000_000
  } else {
    scale =
      absN >= 0.001
        ? 1
        : absN >= 0.000_001
          ? 0.001
          : absN >= 0.000_000_001
            ? 0.000_001
            : absN >= 0.000_000_000_001
              ? 0.000_000_001
              : 0.000_000_000_001
  }
  return scale
}

export function useUnits(val: Ref<number>, unit: string): NumberWithUnitRef<number>
export function useUnits(val: Ref<number | null>, unit: string): NumberWithUnitRef<number | null>
export function useUnits(
  val: Ref<number | null>,
  unit: string,
  defaultVal: number,
): NumberWithUnitRef<number>
export function useUnits<T extends number | number | null>(
  val: Ref<T>,
  unit: string,
  defaultVal: number = 0,
): NumberWithUnitRef<T> {
  const scale = ref<UnitScale>(getScale(val.value ?? 0))

  watch(val, (newVal) => {
    if (newVal === null) return
    if (newVal === 0) {
      scale.value = 1
      return
    }
    let out = newVal / scale.value
    if (out >= 1_000) {
      let next = IncreasingScale.get(scale.value)
      while (out >= 1_000 && next !== undefined) {
        scale.value = next
        out = newVal / scale.value
        next = IncreasingScale.get(scale.value)
      }
    } else if (out < 1) {
      let next = DecreasingScale.get(scale.value)
      while (out < 1 && next !== undefined) {
        scale.value = next
        out = newVal / scale.value
        next = DecreasingScale.get(scale.value)
      }
    }
  })

  const numberRef = computed(() => (val.value === null ? defaultVal : val.value) / scale.value)
  const unitRef = computed(() => UnitScaleToUnitPrefix.get(scale.value)!)
  const renderedUnitRef = computed(() => unitRef.value + unit)

  return {
    number: numberRef,
    renderedUnit: renderedUnitRef,
    unit: unitRef,
    rawNumber: val,
    rawUnit: unit,
  }
}

export function useRegistryWithUnits(
  group: string,
  key: string,
  unitSuffix: string = '',
  defaultVal: number = 0,
): NumberWithUnitRef<number> {
  const value = useRegistry<number>(group, key, SubscriptionMode.LAST)
  return useUnits(value, unitSuffix, defaultVal)
}
