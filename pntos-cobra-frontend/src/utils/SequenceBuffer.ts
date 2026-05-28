export class SequenceBuffer<T> {
  private nextId: number
  private key: (item: T) => number
  private pending: Map<number, T>

  constructor(key: (item: T) => number) {
    this.nextId = 0
    this.key = key
    this.pending = new Map()
  }

  add(item: T): T[] {
    this.pending.set(this.key(item), item)
    const out: T[] = []
    while (this.pending.has(this.nextId)) {
      out.push(this.pending.get(this.nextId)!)
      this.pending.delete(this.nextId)
      this.nextId += 1
    }
    return out
  }

  addMultiple(items: T[]): T[] {
    items.forEach((item) => {
      this.pending.set(this.key(item), item)
    })
    const out: T[] = []
    while (this.pending.has(this.nextId)) {
      out.push(this.pending.get(this.nextId)!)
      this.pending.delete(this.nextId)
      this.nextId += 1
    }
    return out
  }
}
