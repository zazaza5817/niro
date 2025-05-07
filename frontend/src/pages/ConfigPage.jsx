import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import downloadIcon from '../assets/icons/download.svg'
import downloadConfIcon from '../assets/icons/download_conf.svg'
import './ConfigPage.css'

function ConfigPage({ theme }) {
  const containerRef = useRef(null)
  const navigate = useNavigate()
  const [configUrl, setConfigUrl] = useState(null)
  
  useEffect(() => {
    setupBackButton()
    
    fetchConfig()
  }, [theme])
  
  const setupBackButton = () => {
    const tg = window.Telegram?.WebApp
    
    if (tg) {
      tg.BackButton.show()
      tg.BackButton.onClick(() => {
        tg.HapticFeedback.impactOccurred('light')
        navigate('/')
        tg.MainButton.hide()
      })
    }
  }
  
  // Определение операционной системы пользователя
  const getOS = () => {
    const userAgent = window.navigator.userAgent
    
    if (/Win/i.test(userAgent) || /Windows NT/i.test(userAgent)) {
      return "Windows"
    }
    if (/android/i.test(userAgent)) {
      return "Android"
    }
    if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
      return "iOS"
    }
    if (/Mac/.test(userAgent)) {
      return "MacOS"
    }
    return "Unknown"
  }
  
  // Обработчик для кнопки установки приложения
  const handleInstallAppClick = () => {
    const os = getOS()
    const tg = window.Telegram?.WebApp
    
    if (tg) tg.HapticFeedback.impactOccurred('light')
    
    if (os === 'iOS' || os === 'MacOS') {
      window.open('https://apps.apple.com/us/app/streisand/id6450534064', '_blank')
    } else if (os === 'Android') {
      window.open('https://play.google.com/store/apps/details?id=app.hiddify.com', '_blank')
    } else if (os === 'Windows') {
      window.open('https://www.microsoft.com/store/productId/9PDFNL3QV2S5', '_blank')
    } else {
      showPopup('Неизвестная операционная система.')
    }
  }
  
  // Обработчик для кнопки установки конфигурации
  const handleInstallConfigClick = () => {
    const tg = window.Telegram?.WebApp
    if (tg) tg.HapticFeedback.impactOccurred('light')
    
    if (!configUrl) {
      showPopup('Необходимо приобрести подписку')
      return
    }
    
    const os = getOS()
    let formattedConfigUrl = configUrl
    
    if (os === 'Windows') {
      formattedConfigUrl = `https://nirovpn.com/redirect?config_url=${encodeURIComponent(configUrl)}`
    } else if (os === 'iOS' || os === 'MacOS') {
      formattedConfigUrl = `streisand://import/${configUrl}`
    } else if (os === 'Android') {
      formattedConfigUrl = `hiddify://import/${configUrl}`
    }
    
    window.open(formattedConfigUrl, '_blank')
  }
  
  // Показать всплывающее сообщение
  const showPopup = (message) => {
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.showAlert(message)
    } else {
      console.error('Telegram WebApp API is not available.')
      alert(message)
    }
  }
  
  // Получение URL конфигурации с сервера
  const fetchConfig = async () => {
    const tg = window.Telegram?.WebApp
    
    if (!tg) return
    
    try {
      const response = await fetch(`api/check_subscription?auth_data=${encodeURIComponent(tg.initData)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        throw new Error('Ошибка при получении данных')
      }
      
      const data = await response.json()
      
      if (data.config_url) {
        setConfigUrl(data.config_url)
      }
    } catch (error) {
      console.error('Ошибка получения конфигурации:', error)
    }
  }
  
  return (
    <div ref={containerRef}>
      <div className="info">
        <p>Чтобы начать использовать vpn необходимо:</p>
        <ol className="action-list">
          <li className="action-element">Установить приложение</li>
          <li className="action-element">Приобрести подписку</li>
          <li className="action-element">Установить конфигурацию</li>
        </ol>
      </div>
      
      <div className="buttons">
        <button className="button" onClick={handleInstallAppClick}>
          <span className="button-icon">
            <img src={downloadIcon} alt="download icon" />
          </span>
          Установить приложение
        </button>
        
        <button className="button" onClick={handleInstallConfigClick}>
          <span className="button-icon">
            <img src={downloadConfIcon} alt="download config icon" />
          </span>
          Установить конфигурацию
        </button>
      </div>
    </div>
  )
}

export default ConfigPage