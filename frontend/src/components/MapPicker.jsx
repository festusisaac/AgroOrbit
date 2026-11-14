import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import 'maplibre-gl/dist/maplibre-gl.css'

setWorkerUrl(workerUrl)

const NIGERIA_CENTER = [8.68, 9.08]
const SATELLITE =
  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
const LABELS =
  'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'
const TERRAIN = 'https://tiles.mapterhorn.com/tilejson.json'

const MAP_STYLE = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: [SATELLITE],
      tileSize: 256,
      maxzoom: 19,
      attribution: 'Imagery © Esri, Maxar, Earthstar Geographics',
    },
    labels: {
      type: 'raster',
      tiles: [LABELS],
      tileSize: 256,
      maxzoom: 19,
      attribution: 'Labels © Esri',
    },
    terrain: {
      type: 'raster-dem',
      url: TERRAIN,
      tileSize: 256,
      attribution: 'Terrain © Mapterhorn',
    },
  },
  terrain: { source: 'terrain', exaggeration: 1.2 },
  sky: {},
  layers: [
    { id: 'satellite', type: 'raster', source: 'satellite' },
    {
      id: 'hillshade',
      type: 'hillshade',
      source: 'terrain',
      paint: { 'hillshade-shadow-color': '#3b2f1e', 'hillshade-exaggeration': 0.35 },
    },
    { id: 'labels', type: 'raster', source: 'labels', paint: { 'raster-opacity': 0.92 } },
  ],
}

export default function MapPicker({ lat, lon, onPick }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const markerAddedRef = useRef(false)
  const onPickRef = useRef(onPick)
  const [mapError, setMapError] = useState(false)
  onPickRef.current = onPick

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const hasPoint = typeof lat === 'number' && typeof lon === 'number'
    let map
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style: MAP_STYLE,
        center: hasPoint ? [lon, lat] : NIGERIA_CENTER,
        zoom: hasPoint ? 13 : 6,
        pitch: 0,
        bearing: 0,
        maxPitch: 85,
        attributionControl: { compact: true },
      })

      map.addControl(
        new maplibregl.NavigationControl({ visualizePitch: true, showCompass: true }),
        'top-right',
      )
      map.addControl(new maplibregl.GlobeControl(), 'top-right')
      map.addControl(
        new maplibregl.TerrainControl({ source: 'terrain', exaggeration: 1.2 }),
        'top-right',
      )

      const pin = document.createElement('div')
      pin.className = 'map-pin'
      pin.setAttribute('aria-hidden', 'true')
      const marker = new maplibregl.Marker({ element: pin, anchor: 'center' })
      if (hasPoint) {
        marker.setLngLat([lon, lat]).addTo(map)
        markerAddedRef.current = true
      }

      map.on('click', (event) => {
        const nextLon = Number(event.lngLat.lng.toFixed(4))
        const nextLat = Number(event.lngLat.lat.toFixed(4))
        marker.setLngLat([nextLon, nextLat])
        if (!markerAddedRef.current) {
          marker.addTo(map)
          markerAddedRef.current = true
        }
        onPickRef.current?.(nextLat, nextLon)
      })

      mapRef.current = map
      markerRef.current = marker
    } catch (err) {
      setMapError(true)
      try {
        map?.remove()
      } catch {
        /* ignore */
      }
      return
    }

    return () => {
      map.remove()
      mapRef.current = null
      markerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const map = mapRef.current
    const marker = markerRef.current
    if (!map || !marker) return
    if (typeof lat !== 'number' || typeof lon !== 'number') return
    marker.setLngLat([lon, lat])
    if (!markerAddedRef.current) {
      marker.addTo(map)
      markerAddedRef.current = true
    }
    map.flyTo({ center: [lon, lat], zoom: Math.max(map.getZoom(), 12), essential: true })
  }, [lat, lon])

  if (mapError) {
    return (
      <div className="map-frame">
        <div className="map map--gl map--fallback">
          <span>Map needs WebGL. Use a modern browser.</span>
        </div>
        <span className="map-legend">Pick a location above</span>
      </div>
    )
  }

  return (
    <div className="map-frame">
      <div ref={containerRef} className="map map--gl" role="application" aria-label="Interactive satellite map. Click to choose a field location." />
      <span className="map-legend">Tap the map to drop a pin</span>
    </div>
  )
}
