import React from 'react'
import { Search } from 'lucide-react'

function SearchFilters({ filters, onFilterChange }) {
  const handleInputChange = (e) => {
    const { name, value } = e.target
    onFilterChange({ ...filters, [name]: value })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Keyword Search */}
          <div>
            <label htmlFor="keyword" className="block text-sm font-medium text-gray-700 mb-1">
              Keyword
            </label>
            <div className="relative">
              <input
                type="text"
                id="keyword"
                name="keyword"
                value={filters.keyword || ''}
                onChange={handleInputChange}
                placeholder="Search jobs, companies..."
                className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Location */}
          <div>
            <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
              Location
            </label>
            <input
              type="text"
              id="location"
              name="location"
              value={filters.location || ''}
              onChange={handleInputChange}
              placeholder="City, State, Country"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Work Mode */}
          <div>
            <label htmlFor="work_mode" className="block text-sm font-medium text-gray-700 mb-1">
              Work Mode
            </label>
            <select
              id="work_mode"
              name="work_mode"
              value={filters.work_mode || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="Remote">Remote</option>
              <option value="Hybrid">Hybrid</option>
              <option value="On-site">On-site</option>
            </select>
          </div>

          {/* Visa Category */}
          <div>
            <label htmlFor="visa_category" className="block text-sm font-medium text-gray-700 mb-1">
              Visa Friendliness
            </label>
            <select
              id="visa_category"
              name="visa_category"
              value={filters.visa_category || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="High">High</option>
              <option value="Mid">Mid</option>
              <option value="Low">Low</option>
              <option value="No history so far">No history so far</option>
            </select>
          </div>

          {/* Confidence Band */}
          <div>
            <label htmlFor="confidence_band" className="block text-sm font-medium text-gray-700 mb-1">
              Confidence
            </label>
            <select
              id="confidence_band"
              name="confidence_band"
              value={filters.confidence_band || ''}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All</option>
              <option value="High">High</option>
              <option value="Mid">Mid</option>
              <option value="Low">Low</option>
            </select>
          </div>

          {/* Sort By */}
          <div>
            <label htmlFor="sort_by" className="block text-sm font-medium text-gray-700 mb-1">
              Sort By
            </label>
            <select
              id="sort_by"
              name="sort_by"
              value={filters.sort_by || 'scraped_at_utc'}
              onChange={handleInputChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="scraped_at_utc">Most Recent</option>
              <option value="posted_date">Posted Date</option>
              <option value="confidence_score">Confidence Score</option>
            </select>
          </div>
        </div>
      </form>
    </div>
  )
}

export default SearchFilters
