'use client';

// Redux Provider Component

import { Provider } from 'react-redux';
import { ReactNode } from 'react';
import { store } from './store__config';

interface ReduxProviderProps {
  children: ReactNode;
}

export default function ReduxProvider({ children }: ReduxProviderProps) {
  return <Provider store={store}>{children}</Provider>;
}

