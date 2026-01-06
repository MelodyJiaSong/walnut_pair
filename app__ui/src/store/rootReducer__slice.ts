// Root Reducer

import { combineReducers } from '@reduxjs/toolkit';
import walnutComparisonReducer from './features/walnutComparison/walnutComparison__slice';
import cameraPreviewReducer from './cameraPreview/cameraPreview__slice';

const rootReducer = combineReducers({
  walnutComparison: walnutComparisonReducer,
  cameraPreview: cameraPreviewReducer,
});

export default rootReducer;

