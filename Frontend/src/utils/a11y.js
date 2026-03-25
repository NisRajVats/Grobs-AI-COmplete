// Accessibility utilities for GROBS.AI

export const focusTrap = (element) => {
  const focusableElements = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    }
  });
};

export const announceToScreenReader = (message) => {
  const liveRegion = document.getElementById('live-region');
  if (liveRegion) {
    liveRegion.textContent = message;
  }
};

export const skipLink = () => {
  const skipLink = document.createElement('a');
  skipLink.href = '#main-content';
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded';
  return skipLink;
};

// ARIA live region for dynamic content updates
export const createLiveRegion = () => {
  const liveRegion = document.createElement('div');
  liveRegion.id = 'live-region';
  liveRegion.setAttribute('aria-live', 'polite');
  liveRegion.className = 'sr-only';
  document.body.appendChild(liveRegion);
};

// Keyboard navigation utilities
export const handleKeyboardNavigation = (event, options) => {
  const { onEnter, onEscape, onArrowUp, onArrowDown } = options;
  
  switch (event.key) {
    case 'Enter':
      if (onEnter) onEnter(event);
      break;
    case 'Escape':
      if (onEscape) onEscape(event);
      break;
    case 'ArrowUp':
      if (onArrowUp) onArrowUp(event);
      break;
    case 'ArrowDown':
      if (onArrowDown) onArrowDown(event);
      break;
    default:
      break;
  }
};

// Screen reader announcements
export const announce = {
  success: (message) => announceToScreenReader(`Success: ${message}`),
  error: (message) => announceToScreenReader(`Error: ${message}`),
  loading: (message) => announceToScreenReader(`Loading: ${message}`),
  completed: (message) => announceToScreenReader(`Completed: ${message}`)
};

// High contrast mode detection
export const isHighContrastMode = () => {
  const testElement = document.createElement('div');
  testElement.style.borderTop = '1px solid transparent';
  testElement.style.borderBottom = '1px solid transparent';
  document.body.appendChild(testElement);
  
  const computedStyle = window.getComputedStyle(testElement);
  const isHighContrast = computedStyle.borderTopColor === computedStyle.borderBottomColor;
  
  document.body.removeChild(testElement);
  return isHighContrast;
};

// Initialize accessibility features
export const initAccessibility = () => {
  // Create live region for announcements
  createLiveRegion();
  
  // Add skip link
  skipLink();
  
  // Listen for high contrast mode changes
  if (window.matchMedia) {
    const mediaQuery = window.matchMedia('(prefers-contrast: high)');
    mediaQuery.addEventListener('change', (e) => {
      if (e.matches) {
        document.documentElement.classList.add('high-contrast');
      } else {
        document.documentElement.classList.remove('high-contrast');
      }
    });
  }
};