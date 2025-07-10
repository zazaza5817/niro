import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './RedirectPage.css'

function RedirectPage() {
  const location = useLocation()
  const [status, setStatus] = useState('Подготовка к открытию приложения...')
  const [error, setError] = useState(null)
  const [configUrl, setConfigUrl] = useState(null)
  const [deviceType, setDeviceType] = useState('')
  const [deepLinkUrl, setDeepLinkUrl] = useState('')
  const [isReady, setIsReady] = useState(false)
  
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search)
    const url = searchParams.get('config_url')
    
    if (url) {
      setConfigUrl(url)
      setStatus('Определение устройства...')
      
      setTimeout(() => {
        const userAgent = window.navigator.userAgent
        let externalUrl
        let device = ''
        
        if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
          externalUrl = `v2raytun://import/${url}`
          device = 'iOS'
        } else if (/android/i.test(userAgent)) {
          externalUrl = `hiddify://import/${url}`
          device = 'Android'
        } else if (/Win/i.test(userAgent) || /Windows NT/i.test(userAgent)) {
          externalUrl = `hiddify://import/${url}`
          device = 'Windows'
        } else if (/Mac/.test(userAgent)) {
          externalUrl = `v2raytun://import/${url}`
          device = 'macOS'
        } else {
          // Для неизвестных ОС (например, Linux) показываем только кнопку копирования
          device = 'Вашей ОС'
        }
        
        setDeviceType(device)
        setDeepLinkUrl(externalUrl)
        setStatus(`Готово для ${device}`)
        setIsReady(true)
        
        // Автоматически пытаемся открыть deep link только для поддерживаемых платформ
        if (externalUrl && (device === 'iOS' || device === 'Android' || device === 'macOS' || device === 'Windows')) {
          setTimeout(() => {
            openDeepLink(externalUrl, device)
          }, 1000)
        }
      }, 500)
    } else {
      setError('URL конфигурации не предоставлен')
    }
  }, [location])
  
  const openDeepLink = (url, device) => {
    setStatus(`Открытие приложения ${device}...`)
    
    // Простое перенаправление через window.location.href (как в вашем рабочем примере)
    try {
      window.location.href = url
      
      setTimeout(() => {
        setStatus('Если приложение не открылось, попробуйте еще раз')
      }, 3000)
    } catch (error) {
      console.error('Ошибка при открытии deep link:', error)
      setStatus('Ошибка при открытии приложения')
    }
  }
  
  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(configUrl)
      setStatus('Ссылка скопирована в буфер обмена!')
      setTimeout(() => {
        setStatus(`Готово для ${deviceType}`)
      }, 2000)
    } catch (err) {
      console.error('Ошибка копирования:', err)
      setStatus('Не удалось скопировать ссылку')
      setTimeout(() => {
        setStatus(`Готово для ${deviceType}`)
      }, 2000)
    }
  }
  
  return (
    <div className="redirect-container">
      <div className="redirect-gradient-overlay"></div>
      
      <div className="redirect-card">
        <img src="/icons/envelope.svg" className="redirect-logo" alt="VPN Config" />
        
        <h1 className="redirect-title">Добавление конфигурации VPN</h1>
        
        {error ? (
          <div className="redirect-error">
            {error}
          </div>
        ) : (
          <>
            
            <div className="redirect-status">
              {status}
              {!isReady && !error && <span className="redirect-loading"></span>}
            </div>
            
            {isReady && (
              <div className="redirect-buttons-container">
                {/* Кнопка открытия приложения только для поддерживаемых платформ */}
                {deepLinkUrl && (
                  <button 
                    onClick={() => openDeepLink(deepLinkUrl, deviceType)}
                    className="redirect-primary-button"
                  >
                    🚀 Открыть VPN приложение
                  </button>
                )}
                
                {/* Кнопка копирования только для неподдерживаемых ОС */}
                {!deepLinkUrl && (
                  <button 
                    onClick={copyToClipboard}
                    className="redirect-copy-button"
                  >
                    📋 Скопировать ссылку конфигурации
                  </button>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default RedirectPage