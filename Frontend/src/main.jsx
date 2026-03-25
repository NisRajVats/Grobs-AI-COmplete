import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'
import { ThemeProvider } from './context/ThemeContext';
import { initAccessibility, createLiveRegion, skipLink } from './utils/a11y.js'

// Initialize accessibility features
initAccessibility();
createLiveRegion();
document.body.insertBefore(skipLink(), document.body.firstChild);

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ThemeProvider>
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)
