import React from 'react';
import ReactDOM from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import App from './App';
import './index.css';

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
if (!PUBLISHABLE_KEY) {
  throw new Error("Missing Clerk Publishable Key");
}

const root = ReactDOM.createRoot(
  document.getElementById('root')
);

root.render(
  <React.StrictMode>
    <ClerkProvider 
      publishableKey={PUBLISHABLE_KEY} 
      afterSignOutUrl="/"
      appearance={{
        elements: {
          formButtonPrimary: 'bg-primary-600 hover:bg-primary-700 text-white',
          card: 'bg-white shadow-lg',
          headerTitle: 'text-secondary-900',
          headerSubtitle: 'text-secondary-600',
        }
      }}
    >
    <App />
    </ClerkProvider>
  </React.StrictMode>
);