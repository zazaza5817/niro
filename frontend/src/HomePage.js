import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './App.css';

const tg = window.Telegram.WebApp;

const HomePage = () => {
  const [username, setUsername] = useState('');
  const [subscriptionStatus, setSubscriptionStatus] = useState('Загрузка...');

  useEffect(() => {
    tg.ready();
    const user = tg.initDataUnsafe?.user;
    if (user) {
      setUsername(user.first_name);
    } else {
      setUsername('Гость');
    }
    fetchSubscriptionStatus();
  }, []);
  const apiUrl = process.env.REACT_APP_API_URL;
  console.log(process.env.REACT_APP_API_URL)
  const fetchSubscriptionStatus = () => {
    setSubscriptionStatus('Загрузка...');
    fetch(`${apiUrl}/check_subscription`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(tg.initData),
    })
      .then((response) => response.json())
      .then((data) => {
        localStorage.setItem('subscriptionData', JSON.stringify(data));
        setSubscriptionStatus(data.display_text || 'Неизвестный статус');
      })
      .catch((error) => {
        console.error('Ошибка:', error);
        setSubscriptionStatus('Ошибка');
      });
  };

  return (
    <div className="App">
      <div className="info">
        <h1>NIRO VPN</h1>
        <h2>Привет, {username}!</h2>
        <p>Статус подписки: {subscriptionStatus}</p>
      </div>
      <div className="buttons">
        <Link to="/config" className="button">
          <div className="button-icon">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/settings.png" alt="settings-icon" />
          </div>
          <span>Настроить конфигурацию</span>
        </Link>
        <button className="button">
          <div className="button-icon">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/shopping-cart.png" alt="cart-icon" />
          </div>
          <span>Купить подписку</span>
        </button>
        <button className="button">
          <div className="button-icon">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/help.png" alt="support-icon" />
          </div>
          <span>Поддержка</span>
        </button>
      </div>
    </div>
  );
};

export default HomePage;
