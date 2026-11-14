import { LOCATIONS, CROPS, buildClimate, buildRecommend } from './mockData'

const BASE = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '')
const TIMEOUT_MS = 30000

export const hasBackend = Boolean(BASE)

export class ApiError extends Error {
  constructor(message, { status = null, cause = null } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.cause = cause
  }
}

async function request(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(options.headers || {}),
      },
    })
    if (!res.ok) {
      throw new ApiError(`The server responded with ${res.status}.`, { status: res.status })
    }
    return await res.json()
  } catch (err) {
    if (err instanceof ApiError) throw err
    if (err?.name === 'AbortError') {
      throw new ApiError('The server took too long to respond.', { cause: err })
    }
    throw new ApiError('Could not reach the AgroOrbit server.', { cause: err })
  } finally {
    clearTimeout(timer)
  }
}

const delay = (data, ms = 600) =>
  new Promise((resolve) => setTimeout(() => resolve(structuredClone(data)), ms))

export const liveApi = {
  getHealth: () => request('/health'),
  getLocations: () => request('/locations'),
  getCrops: () => request('/crops'),
  getClimate: (lat, lon) =>
    request(`/climate?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}`),
  postRecommend: (payload) =>
    request('/recommend', { method: 'POST', body: JSON.stringify(payload) }),
}

export const mockApi = {
  getHealth: () => delay({ status: 'ok' }, 200),
  getLocations: () => delay({ locations: LOCATIONS }, 250).then((r) => r.locations),
  getCrops: () => delay({ crops: CROPS }, 250).then((r) => r.crops),
  getClimate: (lat, lon) => delay(buildClimate(Number(lat), Number(lon)), 800),
  postRecommend: (payload) => delay(buildRecommend(payload), 900),
}

export const api = hasBackend ? liveApi : mockApi
