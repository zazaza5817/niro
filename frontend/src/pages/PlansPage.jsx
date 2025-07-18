import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import starLargeIcon from '../assets/icons/StarLarge.svg'
import { PlansSkeleton } from '../components/Skeletons'
import './PlansPage.css'

function PlansPage({ theme, forceShowSkeleton = false }) {
  const cachedPlans = localStorage.getItem('plansData')
  const cachedTime = localStorage.getItem('plansDataTime')
  const now = Date.now()
  const cacheExpiry = 5 * 60 * 1000 // 5 минут
  
  let initialPlans = []
  let hasCachedPlans = false
  
  if (cachedPlans && cachedTime && (now - parseInt(cachedTime) < cacheExpiry)) {
    try {
      const parsedPlans = JSON.parse(cachedPlans)
      if (Array.isArray(parsedPlans) && parsedPlans.length > 0) {
        initialPlans = parsedPlans
        hasCachedPlans = true
      }
    } catch (e) {
      console.error('Error parsing cached plans:', e)
    }
  }
  
  const [plans, setPlans] = useState(initialPlans)
  const [loading, setLoading] = useState(!hasCachedPlans)
  const containerRef = useRef(null)
  const navigate = useNavigate()
  
  useEffect(() => {
    setupBackButton()
    
    getPlans()
  }, [theme])
  
  // Настройка кнопки "Назад"
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
  
  const getPlans = async () => {
    try {
      const tg = window.Telegram?.WebApp
      const user = tg?.initDataUnsafe?.user
      const userTgId = user?.id
      
      // Добавляем user_tg_id в query параметры если доступен
      let url = 'api/payments/get_plans'
      if (userTgId) {
        url += `?user_tg_id=${userTgId}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error('Ошибка при получении планов')
      }
      
      const data = await response.json()
      
      localStorage.setItem('plansData', JSON.stringify(data))
      localStorage.setItem('plansDataTime', Date.now().toString())
      
      setPlans(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching plans:', error)
      
      if (!hasCachedPlans) {
        setPlans([])
      }
      setLoading(false)
    }
  }
  
  const sendPlanSelection = async (planKey) => {
    const tg = window.Telegram?.WebApp
    
    if (!tg) return
    
    try {
      const response = await fetch('api/payments/select_plan', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          selected_plan: planKey,
          auth_data: tg.initData
        })
      })
      
      if (!response.ok) {
        throw new Error('Ошибка при выборе плана')
      }
      
      const data = await response.json()
      console.log(data)
      
      tg.HapticFeedback.impactOccurred('light')
      tg.close()
    } catch (error) {
      console.error('Error selecting plan:', error)
    }
  }
  
  // Рендеринг списка планов
  const renderPlans = () => {
    if (loading || forceShowSkeleton) {
      return <PlansSkeleton />
    }
    
    if (plans.length === 0) {
      return <div>Нет доступных планов</div>
    }
    
    return plans.map((plan, index) => (
      <button 
        key={index} 
        className="plan-button" 
        onClick={() => sendPlanSelection(plan.id || index.toString())}
      >
        <span className="plan-name">{plan.name}</span>
        <div className="plan-price-container">
          <span className="plan-price">{plan.price_per_month}</span>
          {plan.discount_percent > 0 && (
            <span className="discount-badge">-{plan.discount_percent}%</span>
          )}
          <img className="star-icon" src={starLargeIcon} width="16" height="16" alt="star" />
          <span>в месяц</span>
        </div>
      </button>
    ))
  }
  
  return (
    <div ref={containerRef}>
      <div className="info">
        <h2 className="plans-title">Тарифные планы</h2>
      </div>
      <div className="subscription-plan">
        {renderPlans()}
      </div>
    </div>
  )
}

export default PlansPage