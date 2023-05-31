import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';
import App from './App';
import { ContextProvider } from './model/State'
import KeyHandler from "./controller/KeyHandler"

// React will search for this element and drop everything under it. Make sure
// that index.html in `public` includes this div.
const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// Render an <App /> that has all
// the necessary state available from
// the context provider.
root.render(
  <React.StrictMode>
    <ContextProvider>
      <KeyHandler>
        <App />
      </ KeyHandler>
    </ ContextProvider>
  </React.StrictMode>
);