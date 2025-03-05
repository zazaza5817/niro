import React, { useEffect } from 'react';
import './App.css';

const tg = window.Telegram.WebApp;

const getOS = () => {
  const userAgent = window.navigator.userAgent;
  if (/Win/i.test(userAgent) || /Windows NT/i.test(userAgent)) {
    return 'Windows';
  }
  if (/android/i.test(userAgent)) {
    return 'Android';
  }
  if (/iPad|iPhone|iPod/.test(userAgent) && !window.MSStream) {
    return 'iOS';
  }
  if (/Mac/.test(userAgent)) {
    return 'MacOS';
  }
  return 'Unknown';
};

const setupAppInstallButton = () => {
  const os = getOS();
  const installAppBtn = document.getElementById('install-app-btn');

  if (os === 'iOS' || os === 'MacOS') {
    installAppBtn.onclick = () => {
      window.open('https://apps.apple.com/us/app/streisand/id6450534064', '_blank');
    };
  } else if (os === 'Android') {
    installAppBtn.onclick = () => {
      window.open('https://play.google.com/store/apps/details?id=app.hiddify.com', '_blank');
    };
  } else if (os === 'Windows') {
    installAppBtn.onclick = () => {
      window.open('https://www.microsoft.com/store/productId/9PDFNL3QV2S5', '_blank');
    };
  } else {
    installAppBtn.onclick = () => {
      alert('Неизвестная операционная система.');
    };
  }
};

const fetchConfig = () => {
  const authData = tg.initData;
  const apiUrl = process.env.REACT_APP_API_URL;

  fetch(`${apiUrl}/check_subscription`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(authData)
  })
    .then(response => response.json())
    .then(data => {
      const installConfigBtn = document.getElementById('install-config-btn');
      if (data.config_url) {
        const os = getOS();
        let configUrl = data.config_url;
        if (os === 'Windows') {
          configUrl = `https://nirovpn.com/redirect?config_url=${encodeURIComponent(configUrl)}`;
        } else if (os === 'iOS' || os === 'MacOS') {
          configUrl = `streisand://import/${configUrl}`;
        } else if (os === 'Android') {
          configUrl = `hiddify://import/${configUrl}`;
        }
        installConfigBtn.onclick = () => window.open(configUrl, '_blank');
      }
    })
    .catch(error => {
      console.error('Ошибка получения конфигурации:', error);
    });
};

const ConfigPage = () => {
  useEffect(() => {
    setupAppInstallButton();
    fetchConfig();
  }, []);

  return (
    <div className="App">
      <div className="info">
        <h1>NIRO VPN</h1>
        <h2>Краткая инструкция</h2>
        <p>Выберите одну из опций ниже, чтобы установить приложение или конфигурацию для вашего устройства.</p>
      </div>
      <div className="buttons">
        <button id="install-app-btn" className="button">
          <div className="button-icon">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/download.png" alt="install-icon" />
          </div>
          <span>Установить приложение</span>
        </button>
        <button id="install-config-btn" className="button">
          <div className="button-icon">
            <img src="https://img.icons8.com/material-outlined/24/ffffff/settings.png" alt="config-icon" />
          </div>
          <span>Установить конфигурацию</span>
        </button>
      </div>
    </div>
  );
};

export default ConfigPage;
