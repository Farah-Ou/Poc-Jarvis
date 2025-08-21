import React from 'react';
import '../styles/LoadingAnimation.css';

interface LoadingAnimationProps {
  message?: string;
}

const LoadingAnimation: React.FC<LoadingAnimationProps> = ({ message = 'Initializing Agents , please wait...' }) => {
  return (
    <div className="loading-container">
      <div className="loading-spinner">
        <div className="spinner-circle"></div>
        <div className="spinner-circle inner"></div>
      </div>
      <p className="loading-message">{message}</p>
    </div>
  );
};

export default LoadingAnimation; 