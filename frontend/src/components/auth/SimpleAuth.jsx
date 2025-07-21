import React, { useState } from 'react';
import { SignIn, SignUp } from '@clerk/clerk-react';

const SimpleAuth = () => {
  const [isSignIn, setIsSignIn] = useState(true);

  return (
    <div className="min-h-screen bg-secondary-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-secondary-900">
            Welcome to Clarifi
          </h2>
          <p className="mt-2 text-sm text-secondary-600">
            Sign in to access your AI-powered browser assistant
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-6">
          {/* Toggle between Sign In and Sign Up */}
          <div className="flex mb-6">
            <button
              onClick={() => setIsSignIn(true)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-l-lg transition-colors ${
                isSignIn
                  ? 'bg-primary-600 text-white'
                  : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => setIsSignIn(false)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-r-lg transition-colors ${
                !isSignIn
                  ? 'bg-primary-600 text-white'
                  : 'bg-secondary-100 text-secondary-700 hover:bg-secondary-200'
              }`}
            >
              Sign Up
            </button>
          </div>

          {/* Clerk Component */}
          <div className="mt-6">
            {isSignIn ? (
              <SignIn 
                appearance={{
                  elements: {
                    formButtonPrimary: 'bg-primary-600 hover:bg-primary-700 text-white',
                    card: 'shadow-none',
                    headerTitle: 'text-secondary-900',
                    headerSubtitle: 'text-secondary-600',
                  }
                }}
                redirectUrl="/"
              />
            ) : (
              <SignUp 
                appearance={{
                  elements: {
                    formButtonPrimary: 'bg-primary-600 hover:bg-primary-700 text-white',
                    card: 'shadow-none',
                    headerTitle: 'text-secondary-900',
                    headerSubtitle: 'text-secondary-600',
                  }
                }}
                redirectUrl="/"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleAuth; 