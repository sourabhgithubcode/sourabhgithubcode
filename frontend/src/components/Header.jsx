import React from 'react'
import { Link } from 'react-router-dom'

function Header() {
  return (
    <header className="bg-white shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2">
            <h1 className="text-2xl font-bold text-blue-600">
              OPT/CPT Friendly Listings
            </h1>
          </Link>
          <nav className="flex space-x-4">
            <Link
              to="/"
              className="text-gray-600 hover:text-blue-600 transition"
            >
              Browse Jobs
            </Link>
          </nav>
        </div>
        <p className="mt-2 text-sm text-gray-600">
          Find volunteer opportunities and jobs that accept OPT and CPT visas for international students
        </p>
      </div>
    </header>
  )
}

export default Header
