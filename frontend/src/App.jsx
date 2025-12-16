import React from 'react'
import { Routes, Route } from 'react-router-dom'
import ListingsPage from './pages/ListingsPage'
import ListingDetailPage from './pages/ListingDetailPage'
import Header from './components/Header'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <Routes>
        <Route path="/" element={<ListingsPage />} />
        <Route path="/listings/:id" element={<ListingDetailPage />} />
      </Routes>
    </div>
  )
}

export default App
