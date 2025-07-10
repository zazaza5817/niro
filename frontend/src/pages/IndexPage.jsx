import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import envelopeIcon from '../assets/icons/envelope.svg'
import settingsIcon from '../assets/icons/settings.svg'
import starIcon from '../assets/icons/star.svg'
import chatIcon from '../assets/icons/chat.svg'
import { UserInfoSkeleton } from '../components/Skeletons'
import '../index.css'

function IndexPage({ theme, forceShowSkeleton = false }) {
  const cachedData = localStorage.getItem('subscriptionData')
  const cachedTime = localStorage.getItem('subscriptionDataTime')
  const now = Date.now()
  const cacheExpiry = 5 * 60 * 1000 
  
  const hasCachedData = cachedData && cachedTime && (now - parseInt(cachedTime) < cacheExpiry)
  
  const [userName, setUserName] = useState(null)
  const [subscriptionStatus, setSubscriptionStatus] = useState(hasCachedData ? JSON.parse(cachedData).display_text : null)
  const [loading, setLoading] = useState(!hasCachedData) 
  const containerRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    initUser()
  }, [theme])

  const initUser = () => {
    const tg = window.Telegram?.WebApp
    
    if (tg) {
      tg.BackButton.hide()
      
      const name = tg.initDataUnsafe.user?.first_name || 'Unknown User'
      setUserName(`Привет, ${name}!`)
      
      fetchSubscriptionData()
    }
  }

  const fetchSubscriptionData = async () => {
    const tg = window.Telegram?.WebApp
    
    if (!tg) return
    
    try {
      const response = await fetch('api/users/check_subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          auth_data: tg.initData
        })
      })
      
      if (!response.ok) {
        throw new Error('Ошибка при получении данных подписки')
      }
      
      const data = await response.json()
      
      localStorage.setItem('subscriptionData', JSON.stringify(data))
      localStorage.setItem('subscriptionDataTime', Date.now().toString())
      
      setSubscriptionStatus(data.display_text)
      setLoading(false)
    } catch (error) {
      console.error('Error:', error)
      
      if (!hasCachedData) {
        setSubscriptionStatus('Ошибка')
      }
      
      setLoading(false)
    }
  }

  const handleConfigClick = () => {
    const tg = window.Telegram?.WebApp
    if (tg) tg.HapticFeedback.impactOccurred('light')
    navigate('/config')
  }

  const handlePlansClick = () => {
    const tg = window.Telegram?.WebApp
    if (tg) tg.HapticFeedback.impactOccurred('light')
    navigate('/plans')
  }

  const handleSupportClick = () => {
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.HapticFeedback.impactOccurred('light')
      tg.openTelegramLink('https://t.me/nirovpn')
    }
  }

  return (
    <div ref={containerRef}>
      <div className="info" id="user-info" style={{ minHeight: '140px' }}>
        <h2>
          <img src={envelopeIcon} alt="icon" />
          <span style={{ color: 'white' }}>niro vpn</span>
        </h2>
        
        <div className="user-content" style={{ minHeight: '80px', display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: 0 }}>
          {(loading || forceShowSkeleton) ? (
            <UserInfoSkeleton />
          ) : (
            <div style={{ minHeight: '70px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <p id="user-name" style={{ textAlign: 'center', margin: '0 0 12px 0', fontSize: '16px', height: '18px' }}>{userName}</p>
              <p id="subscription-status" style={{ 
                textAlign: 'center',
                whiteSpace: 'pre-line',
                margin: '0 auto',
                display: 'block',
                fontSize: '16px',
                maxWidth: '80%',
                height: '40px'
              }}>{subscriptionStatus}</p>
            </div>
          )}
        </div>
      </div>

      <div className="buttons">
        <button className="button" onClick={handleConfigClick}>
          <span className="button-icon">
            <img src={settingsIcon} alt="settings" />
          </span>
          Настроить соединение
        </button>

        <button className="button" onClick={handlePlansClick}>
          <span className="button-icon">
            <img src={starIcon} alt="star" />
          </span>
          Приобрести подписку
        </button>

        <button className="button" onClick={handleSupportClick}>
          <span className="button-icon">
            <img src={chatIcon} alt="chat" />
          </span>
          Поддержка
        </button>
      </div>
    </div>
  )
}

export default IndexPage