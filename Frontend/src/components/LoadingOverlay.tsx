import React from 'react';
import LoadingAnimation from './LoadingAnimation';
import '../styles/LoadingAnimation.css';

interface LoadingOverlayProps {
  message?: string;
  isVisible: boolean;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  message = 'Loading project data, please wait...', 
  isVisible 
}) => {
  if (!isVisible) return null;
  
  return (
    <div className="loading-overlay">
      <LoadingAnimation message={message} />
    </div>
  );
};

export default LoadingOverlay; 