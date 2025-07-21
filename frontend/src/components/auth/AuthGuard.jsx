import React from 'react';
import { SignedIn, SignedOut, useClerk } from '@clerk/clerk-react';
import SimpleAuth from './SimpleAuth';

const AuthGuard = ({ children }) => {
  const { loaded } = useClerk();

  // Show loading state while Clerk is initializing
  if (!loaded) {
    return (
      <div className="min-h-screen bg-secondary-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-secondary-600">Loading authentication...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <SignedIn>
        {children}
      </SignedIn>
      <SignedOut>
        <SimpleAuth />
      </SignedOut>
    </>
  );
};

export default AuthGuard; 