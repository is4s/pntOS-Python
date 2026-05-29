<template>
<div ref="mapEl" class="map"></div>
</template>

<script setup lang="ts">
import { useRegistry } from '@/utils/useRegistry';
import { SubscriptionMode } from '@/types';

import { onMounted, ref, watch } from "vue"
import * as L from "leaflet"
import "leaflet/dist/leaflet.css"

interface Point {
  lat: number
  lon: number
  cov: [number,number,number] | null
  source: string
}

interface Source {
  color: string,
  markers: L.CircleMarker[]
  ellipse: L.Polygon|null
  layer: L.LayerGroup
}

interface Header {
  vendor_id: number
  device_id: number
  context_id: number
  sequence_id: number
}
interface Timestamp {
  elapsed_nsec: number
}
type Vector9 =[number,number,number,number,number,number,number,number,number]
type Vector3 = [number,number,number]
type Vector4 = [number,number,number, number]
type Matrix3 = [Vector3, Vector3, Vector3]
type Matrix9 = [Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9,Vector9]
interface PositionMeasurement {
  header: Header
  time_of_validity: Timestamp
  reference_frame: number
  term1: number
  term2: number
  term3: number
  covariance: Matrix3
  error_model: number
  error_model_params: number[]
  integrity: []
}
interface PvaMeasurement {
  header: Header
  time_of_validity: Timestamp
  reference_frame: number
  p1: number
  p2: number
  p3: number
  v1: number
  v2: number
  v3: number
  quaternion: Vector4
  covariance: Matrix9
  error_model: number
  error_model_params: number[]
  integrity: []
}
interface PositionMessage {
  wrapped_message: PositionMeasurement
  source_identifier: string
}
interface PvaMessage {
  wrapped_message: PvaMeasurement
  source_identifier: string
}


const props = withDefaults(
  defineProps<{
    points?: Point[]
  }>(),
  {
    points: () => []
  }
)

const mapEl = ref<HTMLDivElement | null>(null)
let map: L.Map
let sources: Record<string, Source> = {}
let legend: L.Control | null = null
let legendDiv: HTMLDivElement | null = null
let centerSource: string | null = null

const SOL_GROUP = "ui/channel//solution/pntos/pva"
const TRUTH_GROUP = "ui/channel//sensor/ins-d/pva"
const UBLOX_GROUP = "ui/channel//sensor/ublox-ZED-F9T/position"
const pva = useRegistry<PvaMessage>(SOL_GROUP, "message", SubscriptionMode.LAST)
const truth_pva = useRegistry<PvaMessage>(TRUTH_GROUP, "message", SubscriptionMode.LAST)
const ublox_pos = useRegistry<PositionMessage>(UBLOX_GROUP, "message", SubscriptionMode.LAST)

function getPoint(msg: PvaMessage | PositionMessage): Point {
  let lat = null
  let lon = null
  if ('p1' in msg.wrapped_message){
    // PVA message
    lat = msg.wrapped_message.p1 * 180 / Math.PI
    lon = msg.wrapped_message.p2 * 180 / Math.PI
  }
  else{
    // Position message
    lat= msg.wrapped_message.term1 * 180 / Math.PI
    lon= msg.wrapped_message.term2 * 180 / Math.PI
  }

  return {
    'lat': lat,
    'lon': lon,
    'cov': [msg.wrapped_message.covariance[0][0], msg.wrapped_message.covariance[1][1], msg.wrapped_message.covariance[0][1]],
    'source': msg.source_identifier
  }
}

watch(pva, (new_pva) => {
  if (!new_pva) return
  let point: Point = getPoint(new_pva)
  addPoint(point)
})
watch(truth_pva, (new_pva) => {
  if (!new_pva) return
  let point: Point = getPoint(new_pva)
  addPoint(point)
})
watch(ublox_pos, (new_pos) => {
  if (!new_pos) return
  let point: Point = getPoint(new_pos)
  addPoint(point)
})

onMounted(() => {
  map = L.map(mapEl.value!, {
    preferCanvas: true,
    zoomControl: false // Hides the +/- symbols
  }).setView([40.0, -82.0], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 20,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map)

  map.scrollWheelZoom.disable()

  const container = map.getContainer()

  container.addEventListener("wheel", (e: WheelEvent) => {
    e.preventDefault()

    const delta = e.deltaY > 0 ? -1 : 1
    const newZoom = map.getZoom() + delta

    map.setZoom(newZoom, { animate: true })
  }, { passive: false })
  buildLegend()
})

const MAX_POINTS_PER_SOURCE = 50;

function renderLegend() {
  if (!legendDiv) return

  legendDiv.innerHTML = ""

  Object.entries(sources).forEach(([source_name, source]) => {
    const shown = map.hasLayer(source.layer)? "checked" : ""
    const centered = centerSource && centerSource === source_name ? "checked" : ""
    legendDiv!.innerHTML += `
      <div class="legend-row">
        <span class="legend-source">
          <span class="legend-dot" style="background:${source.color}"></span>
          <span class="legend-name">${source_name}</span>
        </span>
        <span class="legend-controls">
          <label>
            <input type="checkbox" data-source="${source_name}" ${shown}>
            Show
          </label>

          <label>
            <input type="radio" name="active-source" data-center="${source_name}" ${centered}>
            Center
          </label>
        </span
      </div>
      `
  })


  // checkbox toggle
  legendDiv.querySelectorAll("input[type='checkbox']").forEach(el=>{
    el.addEventListener("change", e=>{
      const src = (e.target as HTMLInputElement).dataset.source!
      const layer = sources[src]!.layer
      if ((e.target as HTMLInputElement).checked) layer?.addTo(map)
      else layer?.remove()
    })
  })

  // center button
  legendDiv.querySelectorAll("input[type='radio']").forEach(btn=>{
    btn.addEventListener("change", e=>{
      centerSource=(e.target as HTMLInputElement).dataset.center!
      const src_markers = sources[centerSource]!.markers
      const last_point = src_markers[src_markers.length - 1]!.getLatLng()
      map.panTo([last_point.lat, last_point.lng]);
    })
  })
}

function buildLegend() {
  if (!map) return
  if (legend) return  // already exists

  legend = (L as any).control({ position: "topright" })

  legend!.onAdd = () => {
    legendDiv = L.DomUtil.create("div","legend")
    L.DomEvent.disableClickPropagation(legendDiv)

    renderLegend()  // initial render
    return legendDiv
  }

  legend!.addTo(map)
}

function getNewColor() {
    const pool = ["red", "blue", "green", "orange", "purple", "cyan", "magenta", "brown"];
    const index = Object.keys(sources).length % pool.length
    return pool[index];
}

function get_ellipse_params(sx2: number, sy2: number, sxy: number): [number,number,number] {
  // eigenvalues
  let t = (sx2 + sy2) / 2
  let d = Math.sqrt(((sx2 - sy2) / 2) ** 2 + sxy**2)
  let l1 = t + d
  let l2 = t - d

  // Ellipse size
  let semi_major = Math.sqrt(l1)
  let semi_minor = Math.sqrt(l2)

  // Ellipse rotation
  let theta = 0.5 * Math.atan2(2 * sxy, sx2 - sy2) * (180 / Math.PI);

  return [semi_major, semi_minor, theta]
}

function createEllipse(lat:number,lng: number, ellipse_params: [number, number, number], options: L.PolylineOptions) {
    let semiMajor = ellipse_params[0]
    let semiMinor = ellipse_params[1]
    let rotation = ellipse_params[2]

    var points: L.LatLng[] = [];

    // Convert meters to lat/lng degrees (approximate)
    var latRadius = semiMinor / 111320;
    var lngRadius = semiMajor / (111320 * Math.cos(lat * Math.PI / 180));

    for (var i = 0; i < 360; i += 5) {
        var angle = i * Math.PI / 180;
        var rot = rotation * Math.PI / 180;

        // Ellipse math
        var x = lngRadius * Math.cos(angle);
        var y = latRadius * Math.sin(angle);

        // Rotate the point
        var rotatedLng = x * Math.cos(rot) - y * Math.sin(rot);
        var rotatedLat = x * Math.sin(rot) + y * Math.cos(rot);

        points.push(L.latLng(lat + rotatedLat, lng + rotatedLng));
    }
    return L.polygon(points, options);
}

function addPoint(p: Point) {
  if (!(p.source in sources)){
    sources[p.source] = {'color': getNewColor()!, 'markers': [], 'layer': L.layerGroup().addTo(map), ellipse: null}
    if (Object.keys(sources).length == 1){
      // center on first source that shows up
      centerSource = p.source
    }
    renderLegend()
  }

  let source = sources[p.source]!

  if (!map.hasLayer(source.layer!)){
    return
  }

  let color = source.color
  const marker = L.circleMarker([p.lat,p.lon], {
    radius:6,
    color,
    fillColor: color,
    fillOpacity:0.9
  }).addTo(source.layer)

  if (p.source == centerSource){
    map.panTo([p.lat, p.lon]);
  }

  source.markers.push(marker)
  if (source.markers.length > MAX_POINTS_PER_SOURCE) {
    const oldMarker = source.markers.shift();
    if (oldMarker){
      source.layer.removeLayer(oldMarker)
    }
  }

  if (p.cov) {
    if (source.ellipse) {
        source.ellipse.remove();
    }

    let ellipse_params = get_ellipse_params(p.cov[0],p.cov[1],p.cov[2])
    const ellipse = createEllipse(p.lat, p.lon, ellipse_params, {
        color: color,
        fill: false,
    }).addTo(map);

    source.ellipse = ellipse;
  }
}
</script>

<style>
    .map {
        height: calc(100vh - var(--header-height) - var(--footer-height));
        width: 100vw;
    }

    #controls {
        position: absolute;
        top: 10px;
        right: 10px;
        z-index: 1000;
        background: white;
        padding: 8px;
        border-radius: 4px;
        box-shadow: 0 0 5px rgba(0, 0, 0, 0.3);
        font-family: Arial, sans-serif;
        width: auto;
        max-width: none;
    }

    .legend {
      background: white;
      padding: 10px;
      border-radius: 6px;
      box-shadow: 0 0 6px rgba(0,0,0,0.3);
      font-size: 14px;
    }

    .legend-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 6px;
      margin-bottom: 4px;
    }

    .legend-source {
      display: flex;
      align-items: center;
      min-width: 180px;
    }

    .legend-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      margin-right: 8px;
      flex-shrink: 0;
    }

    .legend-name {
      white-space: nowrap;
    }

    .legend-controls {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .legend-controls label {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    .source-filter {
        margin-top: 10px;
        padding-top: 6px;
        border-top: 1px solid #ccc;
    }

    .source-filter label {
        display: inline-flex;
        align-items: center;
        white-space: nowrap;
        margin-bottom: 4px;
    }
</style>
