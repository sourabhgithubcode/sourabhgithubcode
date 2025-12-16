import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const listingsApi = {
  getListings: async (filters = {}) => {
    const params = new URLSearchParams()

    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value)
      }
    })

    const response = await apiClient.get(`/listings?${params.toString()}`)
    return response.data
  },

  getListingById: async (id) => {
    const response = await apiClient.get(`/listings/${id}`)
    return response.data
  },
}

export const adminApi = {
  triggerScrape: async (data) => {
    const response = await apiClient.post('/admin/scrape', data)
    return response.data
  },

  triggerAssessment: async (data) => {
    const response = await apiClient.post('/admin/assess', data)
    return response.data
  },

  overrideAssessment: async (listingId, data) => {
    const response = await apiClient.post(`/admin/override/${listingId}`, data)
    return response.data
  },
}

export default apiClient
