// Root Reducer

import { combineReducers } from '@reduxjs/toolkit';
import walnutComparisonReducer from './features/walnutComparison/walnutComparison__slice';

const rootReducer = combineReducers({
  walnutComparison: walnutComparisonReducer,
});

export default rootReducer;

