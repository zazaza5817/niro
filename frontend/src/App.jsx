import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import IndexPage from './pages/IndexPage'
import ConfigPage from './pages/ConfigPage'
import PlansPage from './pages/PlansPage'
import RedirectPage from './pages/RedirectPage'
import './App.css'

function App() {
  const [theme, setTheme] = useState(null)

  useEffect(() => {
    // Проверяем, доступен ли Telegram Web App
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp
      
      if (tg.themeParams) {
        setTheme(tg.themeParams)
      }
      
      tg.ready()
    }
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/" element={<IndexPage theme={theme} />} />
        <Route path="/config" element={<ConfigPage theme={theme} />} />
        <Route path="/plans" element={<PlansPage theme={theme} />} />
        <Route path="/redirect" element={<RedirectPage />} />
      </Routes>
    </Router>
  )
}

export default App
