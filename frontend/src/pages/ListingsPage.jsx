import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listingsApi } from '../api/client'
import SearchFilters from '../components/SearchFilters'
import ListingCard from '../components/ListingCard'

function ListingsPage() {
  const [filters, setFilters] = useState({
    keyword: '',
    location: '',
    work_mode: '',
    visa_category: '',
    confidence_band: '',
    sort_by: 'scraped_at_utc',
    sort_order: 'desc',
    limit: 50,
    offset: 0,
  })

  const { data, isLoading, error } = useQuery({
    queryKey: ['listings', filters],
    queryFn: () => listingsApi.getListings(filters),
  })

  const handleFilterChange = (newFilters) => {
    setFilters({ ...newFilters, offset: 0 })
  }

  const handleLoadMore = () => {
    setFilters({ ...filters, offset: filters.offset + filters.limit })
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <SearchFilters filters={filters} onFilterChange={handleFilterChange} />

      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading listings...</p>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          <p className="font-medium">Error loading listings</p>
          <p className="text-sm mt-1">{error.message}</p>
        </div>
      )}

      {data && (
        <>
          <div className="mb-6 flex justify-between items-center">
            <p className="text-gray-600">
              Showing {data.results?.length || 0} of {data.total || 0} listings
            </p>
          </div>

          {data.results && data.results.length > 0 ? (
            <div className="space-y-4">
              {data.results.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-white rounded-lg shadow-sm">
              <p className="text-gray-600 text-lg">No listings found</p>
              <p className="text-gray-500 text-sm mt-2">
                Try adjusting your filters or check back later
              </p>
            </div>
          )}

          {data.results && data.results.length < data.total && (
            <div className="mt-8 text-center">
              <button
                onClick={handleLoadMore}
                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
              >
                Load More
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default ListingsPage
