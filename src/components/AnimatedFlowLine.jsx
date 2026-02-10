import { useEffect, useRef } from 'react'
import { useMap } from 'react-leaflet'
import L from 'leaflet'

/**
 * Animated flow line component for showing traffic congestion spread
 * Draws an animated dashed line from one point to another
 */
const AnimatedFlowLine = ({
  from,
  to,
  color = '#ef4444',
  weight = 3,
  probability = 1,
  animationSpeed = 20,
  dashArray = '10, 10'
}) => {
  const map = useMap()
  const polylineRef = useRef(null)
  const animationRef = useRef(null)
  const offsetRef = useRef(0)

  useEffect(() => {
    if (!from || !to || !map) return

    // Create the polyline
    const polyline = L.polyline(
      [[from.lat, from.lon], [to.lat, to.lon]],
      {
        color: color,
        weight: weight * probability,
        opacity: 0.6 + (probability * 0.4),
        dashArray: dashArray,
        lineCap: 'round',
        lineJoin: 'round'
      }
    ).addTo(map)

    polylineRef.current = polyline

    // Animate the dash offset
    const animate = () => {
      offsetRef.current = (offsetRef.current + 1) % 20
      if (polylineRef.current) {
        polylineRef.current.setStyle({
          dashOffset: -offsetRef.current
        })
      }
      animationRef.current = requestAnimationFrame(animate)
    }

    // Start animation with delay based on speed
    const intervalId = setInterval(() => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      animate()
    }, animationSpeed)

    // Cleanup
    return () => {
      clearInterval(intervalId)
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      if (polylineRef.current) {
        map.removeLayer(polylineRef.current)
      }
    }
  }, [from, to, color, weight, probability, animationSpeed, dashArray, map])

  return null
}

/**
 * Animated arrow line - shows direction with moving arrow pattern
 */
export const AnimatedArrowLine = ({
  from,
  to,
  color = '#ef4444',
  weight = 4,
  probability = 1,
  fromName = '',
  toName = ''
}) => {
  const map = useMap()
  const elementsRef = useRef([])
  const animationRef = useRef(null)

  useEffect(() => {
    if (!from || !to || !map) return

    // Clear previous elements
    elementsRef.current.forEach(el => map.removeLayer(el))
    elementsRef.current = []

    // Calculate line properties
    const opacity = 0.4 + (probability * 0.5)
    const lineWeight = Math.max(2, weight * probability)

    // Create base line (static background)
    const baseLine = L.polyline(
      [[from.lat, from.lon], [to.lat, to.lon]],
      {
        color: color,
        weight: lineWeight,
        opacity: opacity * 0.3,
        lineCap: 'round'
      }
    ).addTo(map)
    elementsRef.current.push(baseLine)

    // Create animated dashed line on top
    const animatedLine = L.polyline(
      [[from.lat, from.lon], [to.lat, to.lon]],
      {
        color: color,
        weight: lineWeight - 1,
        opacity: opacity,
        dashArray: '8, 12',
        lineCap: 'round'
      }
    ).addTo(map)
    elementsRef.current.push(animatedLine)

    // Add popup with flow info
    const midLat = (from.lat + to.lat) / 2
    const midLon = (from.lon + to.lon) / 2

    animatedLine.bindPopup(`
      <div style="min-width: 150px;">
        <strong style="color: ${color};">Traffic Flow</strong><br/>
        <span style="font-size: 12px;">
          ${fromName || 'Source'} → ${toName || 'Destination'}<br/>
          <strong>Impact: ${(probability * 100).toFixed(0)}%</strong>
        </span>
      </div>
    `)

    // Animation
    let offset = 0
    const animate = () => {
      offset = (offset + 0.5) % 20
      animatedLine.setStyle({ dashOffset: -offset })
      animationRef.current = requestAnimationFrame(animate)
    }
    animate()

    // Create arrow markers along the line
    const arrowCount = Math.max(1, Math.floor(
      map.distance([from.lat, from.lon], [to.lat, to.lon]) / 500
    ))

    for (let i = 1; i <= arrowCount; i++) {
      const t = i / (arrowCount + 1)
      const lat = from.lat + (to.lat - from.lat) * t
      const lon = from.lon + (to.lon - from.lon) * t

      // Calculate angle for arrow
      const angle = Math.atan2(to.lon - from.lon, to.lat - from.lat) * 180 / Math.PI

      const arrowIcon = L.divIcon({
        className: 'flow-arrow',
        html: `<div style="
          transform: rotate(${angle}deg);
          color: ${color};
          font-size: 16px;
          opacity: ${opacity};
          text-shadow: 0 0 3px white;
        ">▲</div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      })

      const arrowMarker = L.marker([lat, lon], { icon: arrowIcon }).addTo(map)
      elementsRef.current.push(arrowMarker)
    }

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      elementsRef.current.forEach(el => {
        if (map.hasLayer(el)) {
          map.removeLayer(el)
        }
      })
      elementsRef.current = []
    }
  }, [from, to, color, weight, probability, fromName, toName, map])

  return null
}

/**
 * Pulsing connection line - creates a pulse effect from source to destination
 */
export const PulsingFlowLine = ({
  from,
  to,
  color = '#ef4444',
  probability = 1,
  fromName = '',
  toName = ''
}) => {
  const map = useMap()
  const elementsRef = useRef([])
  const pulseMarkersRef = useRef([])
  const animationRef = useRef(null)

  useEffect(() => {
    if (!from || !to || !map) return

    // Clear previous elements
    elementsRef.current.forEach(el => map.removeLayer(el))
    pulseMarkersRef.current.forEach(el => map.removeLayer(el))
    elementsRef.current = []
    pulseMarkersRef.current = []

    const opacity = 0.3 + (probability * 0.5)
    const weight = 2 + (probability * 3)

    // Create the base line
    const line = L.polyline(
      [[from.lat, from.lon], [to.lat, to.lon]],
      {
        color: color,
        weight: weight,
        opacity: opacity,
        lineCap: 'round'
      }
    ).addTo(map)
    elementsRef.current.push(line)

    // Add popup
    line.bindPopup(`
      <div style="min-width: 150px;">
        <strong style="color: ${color};">Congestion Spread</strong><br/>
        <span style="font-size: 12px;">
          From: ${fromName || 'Road A'}<br/>
          To: ${toName || 'Road B'}<br/>
          <strong>Probability: ${(probability * 100).toFixed(0)}%</strong>
        </span>
      </div>
    `)

    // Create pulse markers
    const numPulses = 3
    const pulses = []

    for (let i = 0; i < numPulses; i++) {
      const pulseIcon = L.divIcon({
        className: 'pulse-marker',
        html: `<div class="pulse-dot" style="
          width: 10px;
          height: 10px;
          background: ${color};
          border-radius: 50%;
          box-shadow: 0 0 10px ${color};
        "></div>`,
        iconSize: [10, 10],
        iconAnchor: [5, 5]
      })

      const marker = L.marker([from.lat, from.lon], {
        icon: pulseIcon,
        interactive: false
      }).addTo(map)

      pulses.push({ marker, progress: i / numPulses })
      pulseMarkersRef.current.push(marker)
    }

    // Animate pulses along the line
    let lastTime = 0
    const speed = 0.001 * (1 + probability) // Faster for higher probability

    const animate = (timestamp) => {
      const delta = timestamp - lastTime
      lastTime = timestamp

      pulses.forEach(pulse => {
        pulse.progress += speed * delta / 16
        if (pulse.progress > 1) pulse.progress = 0

        const lat = from.lat + (to.lat - from.lat) * pulse.progress
        const lon = from.lon + (to.lon - from.lon) * pulse.progress
        pulse.marker.setLatLng([lat, lon])
      })

      animationRef.current = requestAnimationFrame(animate)
    }

    animationRef.current = requestAnimationFrame(animate)

    // Cleanup
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
      elementsRef.current.forEach(el => {
        if (map.hasLayer(el)) map.removeLayer(el)
      })
      pulseMarkersRef.current.forEach(el => {
        if (map.hasLayer(el)) map.removeLayer(el)
      })
      elementsRef.current = []
      pulseMarkersRef.current = []
    }
  }, [from, to, color, probability, fromName, toName, map])

  return null
}

export default AnimatedFlowLine
