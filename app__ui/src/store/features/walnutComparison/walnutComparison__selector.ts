// Redux Selectors for Walnut Comparison

import { createSelector } from '@reduxjs/toolkit';
import { RootState } from '@/store/store__config';
import { WalnutComparisonState } from './walnutComparison__type';

// Base selector
const selectWalnutComparisonState = (state: RootState): WalnutComparisonState =>
  state.walnutComparison;

// Select all pairs
export const selectAllPairs = createSelector(
  [selectWalnutComparisonState],
  (state) => state.pairs
);

// Select pairs by walnut ID
export const selectPairsByWalnutId = createSelector(
  [selectAllPairs, (_state: RootState, walnutId: string) => walnutId],
  (pairs, walnutId) => pairs.filter((pair) => pair.walnut_id === walnutId || pair.compared_walnut_id === walnutId)
);

// Select loading state
export const selectLoading = createSelector(
  [selectWalnutComparisonState],
  (state) => state.loading
);

// Select error state
export const selectError = createSelector(
  [selectWalnutComparisonState],
  (state) => state.error
);

// Select selected pair
export const selectSelectedPair = createSelector(
  [selectWalnutComparisonState],
  (state) => state.selectedPair
);

