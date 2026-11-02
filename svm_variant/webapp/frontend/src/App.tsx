import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Classify from '@/pages/Classify'
import Gallery from '@/pages/Gallery'
import Results from '@/pages/Results'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="classify" element={<Classify />} />
          <Route path="results" element={<Results />} />
          <Route path="gallery" element={<Gallery />} />
          <Route path="*" element={<p className="py-10 text-center">Page not found.</p>} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
