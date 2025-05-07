import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

function RedirectPage() {
  const location = useLocation()
  
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const configUrl = searchParams.get('config_url')
    
    if (configUrl) {
      const userAgent = window.navigator.userAgent
      let externalUrl
      
      if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
        externalUrl = `streisand://import/${configUrl}`
      } else if (/android/i.test(userAgent)) {
        externalUrl = `hiddify://import/${configUrl}`
      } else if (/Win/i.test(userAgent) || /Windows NT/i.test(userAgent)) {
        externalUrl = `https://nirovpn.com/redirect?config_url=${encodeURIComponent(configUrl)}`
      } else if (/Mac/.test(userAgent)) {
        externalUrl = `streisand://import/${configUrl}`
      } else {
        alert('Неизвестная операционная система')
        return
      }
      
      window.location.href = externalUrl
    } else {
      console.error('URL конфигурации не предоставлен')
    }
  }, [location])
  
  return (
    <div className="redirect-container">
      <h1>Добавление конфигурации</h1>
      <p>Нажмите "Далее" в диалоговом окне, чтобы открыть приложение VPN и добавить конфигурацию.</p>
    </div>
  )
}

export default RedirectPage