import React from 'react'
import { Link } from 'react-router-dom'
import { MapPin, Briefcase, Calendar, ExternalLink } from 'lucide-react'

function ListingCard({ listing }) {
  const getVisaCategoryColor = (category) => {
    switch (category) {
      case 'High':
        return 'bg-green-100 text-green-800'
      case 'Mid':
        return 'bg-blue-100 text-blue-800'
      case 'Low':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getConfidenceBadge = (band, score) => {
    const colorClass = getVisaCategoryColor(band)
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${colorClass}`}>
        {band} {score ? `(${score}%)` : ''}
      </span>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm hover:shadow-md transition p-6">
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <Link
            to={`/listings/${listing.id}`}
            className="text-xl font-semibold text-gray-900 hover:text-blue-600"
          >
            {listing.title}
          </Link>
          <p className="text-gray-600 mt-1">{listing.company_name}</p>
        </div>
        {listing.visa_category && (
          <div className="ml-4">
            {getConfidenceBadge(
              listing.confidence_band,
              listing.confidence_score_0_100
            )}
          </div>
        )}
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex items-center text-sm text-gray-600">
          <MapPin className="h-4 w-4 mr-2" />
          <span>{listing.location || 'Unknown'}</span>
        </div>
        <div className="flex items-center text-sm text-gray-600">
          <Briefcase className="h-4 w-4 mr-2" />
          <span>{listing.work_mode || 'Unknown'} • {listing.employment_type || 'Unknown'}</span>
        </div>
        <div className="flex items-center text-sm text-gray-600">
          <Calendar className="h-4 w-4 mr-2" />
          <span>Posted: {listing.posted_date || 'Unknown'}</span>
        </div>
      </div>

      {listing.reasons_short && (
        <div className="mb-4">
          <p className="text-sm text-gray-700 italic">
            "{listing.reasons_short}"
          </p>
        </div>
      )}

      {listing.description_text && (
        <p className="text-sm text-gray-600 mb-4 line-clamp-3">
          {listing.description_text.substring(0, 200)}...
        </p>
      )}

      <div className="flex space-x-3">
        <Link
          to={`/listings/${listing.id}`}
          className="flex-1 text-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
        >
          View Details
        </Link>
        <a
          href={listing.apply_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition"
        >
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>
    </div>
  )
}

export default ListingCard
