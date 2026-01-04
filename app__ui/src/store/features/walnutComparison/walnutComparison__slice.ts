// Redux Slice for Walnut Comparison

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { WalnutComparisonState } from './walnutComparison__type';
import { WalnutComparisonDTO } from '@/types/api__type';

const initialState: WalnutComparisonState = {
  pairs: [],
  loading: false,
  error: null,
  selectedPair: null,
};

const walnutComparisonSlice = createSlice({
  name: 'walnutComparison',
  initialState,
  reducers: {
    // Fetch all pairs
    fetchAllPairs: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchAllPairsSuccess: (state, action: PayloadAction<WalnutComparisonDTO[]>) => {
      state.loading = false;
      state.pairs = action.payload;
      state.error = null;
    },
    fetchAllPairsFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Fetch pairs by walnut ID
    fetchPairsByWalnutId: (state, _action: PayloadAction<string>) => {
      state.loading = true;
      state.error = null;
    },
    fetchPairsByWalnutIdSuccess: (state, action: PayloadAction<WalnutComparisonDTO[]>) => {
      state.loading = false;
      state.pairs = action.payload;
      state.error = null;
    },
    fetchPairsByWalnutIdFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Fetch specific pair
    fetchPair: (state, _action: PayloadAction<{ walnutId: string; comparedWalnutId: string }>) => {
      state.loading = true;
      state.error = null;
    },
    fetchPairSuccess: (state, action: PayloadAction<WalnutComparisonDTO>) => {
      state.loading = false;
      state.selectedPair = action.payload;
      state.error = null;
    },
    fetchPairFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.error = action.payload;
    },

    // Clear selected pair
    clearSelectedPair: (state) => {
      state.selectedPair = null;
    },
  },
});

export const {
  fetchAllPairs,
  fetchAllPairsSuccess,
  fetchAllPairsFailure,
  fetchPairsByWalnutId,
  fetchPairsByWalnutIdSuccess,
  fetchPairsByWalnutIdFailure,
  fetchPair,
  fetchPairSuccess,
  fetchPairFailure,
  clearSelectedPair,
} = walnutComparisonSlice.actions;

export default walnutComparisonSlice.reducer;

