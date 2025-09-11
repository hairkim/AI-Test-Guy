import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './PageComponents/CSS/index.css'
import App from './App.jsx'
import React from 'react';
import 'katex/dist/katex.min.css';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
