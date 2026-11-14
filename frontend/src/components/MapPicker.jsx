import { useEffect, useRef } from 'react'
import L from 'leaflet'

const NIGERIA_CENTER = [9.08, 8.68]

export default function MapPicker({ lat, lon, onPick }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const onPickRef = useRef(onPick)
  onPickRef.current = onPick

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return

    const hasPoint = typeof lat === 'number' && typeof lon === 'number'
    const map = L.map(containerRef.current, {
      center: hasPoint ? [lat, lon] : NIGERIA_CENTER,
      zoom: hasPoint ? 8 : 6,
      zoomControl: true,
      attributionControl: true,
    })

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map)

    const marker = L.circleMarker(hasPoint ? [lat, lon] : NIGERIA_CENTER, {
      radius: 9,
      color: '#2c5c40',
      weight: 2,
      fillColor: '#387151',
      fillOpacity: 0.35,
    })
    if (hasPoint) marker.addTo(map)

    map.on('click', (event) => {
      const nextLat = Number(event.latlng.lat.toFixed(4))
      const nextLon = Number(event.latlng.lng.toFixed(4))
      marker.setLatLng([nextLat, nextLon])
      if (!map.hasLayer(marker)) marker.addTo(map)
      onPickRef.current?.(nextLat, nextLon)
    })

    mapRef.current = map
    markerRef.current = marker
    const settle = setTimeout(() => map.invalidateSize(), 120)

    return () => {
      clearTimeout(settle)
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
    marker.setLatLng([lat, lon])
    if (!map.hasLayer(marker)) marker.addTo(map)
    map.panTo([lat, lon], { animate: true })
  }, [lat, lon])

  return (
    <div className="map-frame">
      <div ref={containerRef} className="map" role="application" aria-label="Click the map to choose a field location" />
      <span className="map-legend">Tap the map to drop a pin</span>
    </div>
  )
}
