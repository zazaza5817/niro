import './Skeletons.css';

// Скелетон для текста имени пользователя и статуса подписки
export const UserInfoSkeleton = () => {
  return (
    <div className="user-info-container">
      <div className="skeleton-container">
        <div className="skeleton-text-line"></div>
        <div className="skeleton-text-line skeleton-text-line-2"></div>
      </div>
    </div>
  );
};

// Скелетон для планов подписки
export const PlansSkeleton = () => {
  return (
    <div className="skeleton-plans-container">
      <div className="skeleton-plan-item">
        <div className="skeleton-plan-name"></div>
        <div className="skeleton-plan-price"></div>
      </div>
      <div className="skeleton-plan-item">
        <div className="skeleton-plan-name"></div>
        <div className="skeleton-plan-price"></div>
      </div>
      <div className="skeleton-plan-item">
        <div className="skeleton-plan-name"></div>
        <div className="skeleton-plan-price"></div>
      </div>
    </div>
  );
};

// Общий компонент пульсирующего контейнера для любого содержимого
export const SkeletonPulse = ({ children, width, height }) => {
  return (
    <div 
      className="skeleton-pulse"
      style={{ width: width || 'auto', height: height || 'auto' }}
    >
      {children}
    </div>
  );
};