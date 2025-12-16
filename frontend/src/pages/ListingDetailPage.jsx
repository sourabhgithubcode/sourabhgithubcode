import React, { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { listingsApi } from '../api/client'
import {
  MapPin,
  Briefcase,
  Calendar,
  ExternalLink,
  ArrowLeft,
  ChevronDown,
  ChevronUp,
  AlertCircle,
} from 'lucide-react'

function ListingDetailPage() {
  const { id } = useParams()
  const [showFullReasoning, setShowFullReasoning] = useState(false)

  const { data: listing, isLoading, error } = useQuery({
    queryKey: ['listing', id],
    queryFn: () => listingsApi.getListingById(id),
  })

  const getVisaCategoryColor = (category) => {
    switch (category) {
      case 'High':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'Mid':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'Low':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-600 border-r-transparent"></div>
          <p className="mt-4 text-gray-600">Loading listing details...</p>
        </div>
      </div>
    )
  }

  if (error || !listing) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          <p className="font-medium">Error loading listing</p>
          <p className="text-sm mt-1">{error?.message || 'Listing not found'}</p>
        </div>
      </div>
    )
  }

  const assessment = listing.visa_assessment

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back button */}
      <Link
        to="/"
        className="inline-flex items-center text-gray-600 hover:text-blue-600 mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back to listings
      </Link>

      <div className="bg-white rounded-lg shadow-sm p-8">
        {/* Header */}
        <div className="border-b pb-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {listing.title}
          </h1>
          <h2 className="text-xl text-gray-700 mb-4">{listing.company_name}</h2>

          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <div className="flex items-center">
              <MapPin className="h-4 w-4 mr-2" />
              <span>{listing.location || 'Unknown'}</span>
            </div>
            <div className="flex items-center">
              <Briefcase className="h-4 w-4 mr-2" />
              <span>
                {listing.work_mode || 'Unknown'} • {listing.employment_type || 'Unknown'}
              </span>
            </div>
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2" />
              <span>Posted: {listing.posted_date || 'Unknown'}</span>
            </div>
          </div>
        </div>

        {/* Visa Assessment */}
        {assessment && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Visa Friendliness Assessment
            </h3>

            <div
              className={`border-2 rounded-lg p-6 ${getVisaCategoryColor(
                assessment.visa_category
              )}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="text-2xl font-bold">
                    {assessment.visa_category}
                  </span>
                  <span className="ml-3 text-lg">
                    Confidence: {assessment.confidence_score_0_100}%
                  </span>
                </div>
                <span className="px-3 py-1 bg-white rounded-full text-sm font-medium">
                  {assessment.confidence_band} Confidence
                </span>
              </div>

              <div className="bg-white bg-opacity-70 rounded-lg p-4 mb-4">
                <p className="text-gray-800 italic">"{assessment.reasons_short}"</p>
              </div>

              <button
                onClick={() => setShowFullReasoning(!showFullReasoning)}
                className="flex items-center text-sm font-medium hover:underline"
              >
                {showFullReasoning ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-1" />
                    Hide detailed reasoning
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-1" />
                    Show detailed reasoning
                  </>
                )}
              </button>

              {showFullReasoning && (
                <div className="mt-4 bg-white bg-opacity-70 rounded-lg p-4">
                  <h4 className="font-semibold mb-2">Detailed Reasoning:</h4>
                  <p className="text-gray-800 whitespace-pre-line">
                    {assessment.reasons_long}
                  </p>

                  {assessment.evidence_links_json &&
                    assessment.evidence_links_json.length > 0 && (
                      <div className="mt-4">
                        <h4 className="font-semibold mb-2">Evidence Sources:</h4>
                        <ul className="space-y-2">
                          {assessment.evidence_links_json.map((evidence, idx) => (
                            <li key={idx} className="text-sm">
                              <a
                                href={evidence.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-600 hover:underline flex items-center"
                              >
                                <ExternalLink className="h-3 w-3 mr-1" />
                                {evidence.title || evidence.url}
                              </a>
                              {evidence.excerpt && (
                                <p className="text-gray-600 ml-4 mt-1">
                                  {evidence.excerpt}
                                </p>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                  <div className="mt-4 text-xs text-gray-600">
                    <p>Model: {assessment.model_version}</p>
                    <p>Assessed: {new Date(assessment.assessed_at_utc).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Description */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">
            Job Description
          </h3>
          <div className="prose max-w-none text-gray-700">
            {listing.description_text || 'No description available'}
          </div>
        </div>

        {/* Requirements */}
        {listing.requirements_text && (
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              Requirements
            </h3>
            <div className="prose max-w-none text-gray-700">
              {listing.requirements_text}
            </div>
          </div>
        )}

        {/* Additional Info */}
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          {listing.salary_text && listing.salary_text !== 'Unknown' && (
            <div>
              <span className="font-medium">Compensation:</span>{' '}
              {listing.salary_text}
            </div>
          )}
          <div>
            <span className="font-medium">Source:</span> {listing.source}
          </div>
        </div>

        {/* Data Quality Flags */}
        {listing.data_quality_flags && listing.data_quality_flags.length > 0 && (
          <div className="mb-8 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-yellow-600 mr-2 mt-0.5" />
              <div>
                <p className="font-medium text-yellow-800">Data Quality Notes:</p>
                <ul className="text-sm text-yellow-700 mt-1 list-disc list-inside">
                  {listing.data_quality_flags.map((flag, idx) => (
                    <li key={idx}>{flag.replace(/_/g, ' ')}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Apply Button */}
        <div className="pt-6 border-t">
          <a
            href={listing.apply_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition"
          >
            Apply Now
            <ExternalLink className="h-4 w-4 ml-2" />
          </a>
        </div>
      </div>
    </div>
  )
}

export default ListingDetailPage
