import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

const API = 'http://localhost:8000'

export default function Maps() {
  const mapContainerRef = useRef(null)
  const mapInstanceRef  = useRef(null)
  const markerRef       = useRef(null)

  const [search, setSearch]   = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [info, setInfo]       = useState(null)
  const [error, setError]     = useState(null)

  /* ── Bootstrap Leaflet safely inside Electron ── */
  useEffect(() => {
    const container = mapContainerRef.current
    if (!container || mapInstanceRef.current) return

    // Inject Leaflet CSS once
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link')
      link.id   = 'leaflet-css'
      link.rel  = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)
    }

    const initMap = () => {
      if (mapInstanceRef.current || !window.L) return
      const L   = window.L
      const map = L.map(container, { center: [20, 0], zoom: 2, tap: false })

      // Attribution with pointer-events:none so clicking it does nothing
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap',
        maxZoom: 19,
      }).addTo(map)

      mapInstanceRef.current = map

      // Click anywhere → reverse geocode (no geo: links involved)
      map.on('click', async (e) => {
        const { lat, lng } = e.latlng
        placeMarker(lat, lng)
        try {
          const res  = await fetch(`${API}/maps/reverse?lat=${lat}&lon=${lng}`)
          const data = await res.json()
          setInfo(data.display_name)
        } catch { /* ignore */ }
      })
    }

    if (window.L) {
      initMap()
    } else {
      const script  = document.createElement('script')
      script.id     = 'leaflet-js'
      script.src    = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
      script.onload = initMap
      document.head.appendChild(script)
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
        markerRef.current      = null
      }
    }
  }, [])

  /* ── Place a marker and fly to it ── */
  const placeMarker = (lat, lon, zoom = 13) => {
    const map = mapInstanceRef.current
    if (!map || !window.L) return
    if (markerRef.current) markerRef.current.remove()
    markerRef.current = window.L.marker([lat, lon]).addTo(map)
    map.flyTo([lat, lon], zoom, { duration: 1 })
  }

  /* ── Search ── */
  const handleSearch = async (e) => {
    e.preventDefault()
    if (!search.trim()) return
    setLoading(true)
    setError(null)
    setResults([])
    try {
      const res  = await fetch(`${API}/maps/search?q=${encodeURIComponent(search)}`)
      const data = await res.json()
      if (!Array.isArray(data) || data.length === 0) setError('No results found')
      else setResults(data)
    } catch {
      setError('Search failed — is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const selectResult = (r) => {
    placeMarker(r.lat, r.lon, 13)
    setInfo(r.display_name)
    setResults([])
    setSearch(r.display_name.split(',').slice(0, 2).join(', '))
  }

  /* ── Block any <a> clicks inside the map div (stops Organic Maps) ── */
  const blockLinks = (e) => {
    if (e.target.closest('a')) {
      e.preventDefault()
      e.stopPropagation()
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center py-10 px-4">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold mb-6 text-cyan-400"
      >
        🗺️ Maps
      </motion.h1>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-2 mb-4 w-full max-w-2xl relative">
        <input
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
                     text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
          placeholder="Search a place…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setResults([]) }}
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 px-4 py-2 rounded-lg font-semibold transition"
        >
          {loading ? '…' : 'Search'}
        </button>

        {results.length > 0 && (
          <ul className="absolute top-full left-0 right-16 bg-gray-800 border border-gray-700
                         rounded-lg mt-1 z-50 overflow-hidden shadow-xl">
            {results.map((r, i) => (
              <li
                key={i}
                onClick={() => selectResult(r)}
                className="px-4 py-2 hover:bg-gray-700 cursor-pointer text-sm truncate
                           border-b border-gray-700 last:border-0"
              >
                {r.display_name}
              </li>
            ))}
          </ul>
        )}
      </form>

      {error && <p className="text-red-400 text-sm mb-3">{error}</p>}

      {info && (
        <motion.p
          key={info}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-gray-300 text-sm mb-3 text-center max-w-2xl truncate"
        >
          📍 {info}
        </motion.p>
      )}

      {/* onClick intercepts attribution link clicks before Electron sees them */}
      <div
        ref={mapContainerRef}
        onClick={blockLinks}
        className="w-full max-w-2xl rounded-2xl overflow-hidden shadow-xl"
        style={{ height: '450px' }}
      />

      <p className="text-gray-600 text-xs mt-3">
        Click anywhere on the map to identify a location. © OpenStreetMap contributors.
      </p>
    </div>
  )
}
