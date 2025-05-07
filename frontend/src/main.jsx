import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

const root = document.getElementById('root')

const isTelegramWebApp = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const tgWebAppData = urlParams.get('tgWebAppData');
  const tgWebAppVersion = urlParams.get('tgWebAppVersion');
  
  const hasTelegramObject = Boolean(window.Telegram);
  const hasWebAppObject = Boolean(window.Telegram?.WebApp);
  const isInitialized = Boolean(window.Telegram?.WebApp?.initData);
  
  return (
    (tgWebAppData || tgWebAppVersion) ||
    (hasTelegramObject && hasWebAppObject && isInitialized)
  );
};

if (!isTelegramWebApp()) {
  const favicon = document.createElement('link');
  favicon.rel = 'icon';
  favicon.type = 'image/svg+xml';
  favicon.href = '/icons/envelope.svg';
  document.head.appendChild(favicon);

  fetch('/html/telegram_only.html')
    .then(response => response.text())
    .then(html => {
      document.open();
      document.write(html);
      document.close();
    })
    .catch(error => {
      console.error('Ошибка при загрузке HTML:', error);
    });
} else {
  createRoot(root).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}
