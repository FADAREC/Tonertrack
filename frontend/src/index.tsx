import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css'; // Must be here
import App from './App';
import reportWebVitals from './reportWebVitals';

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// // Service worker registration
// if ('serviceWorker' in navigator) {
//   window.addEventListener('load', () => {
//     navigator.serviceWorker.register('/sw.js').catch(err => console.error('Service Worker Error:', err));
//   });
// }

// Log performance (optional)
reportWebVitals(console.log);
