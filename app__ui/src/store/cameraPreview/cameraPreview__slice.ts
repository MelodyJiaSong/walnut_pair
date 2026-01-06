// Camera Preview Redux Slice

import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { CameraInfo } from '../../../api/cameraPreview__api';

// Redux doesn't support Set/Map in state, so we use an array
interface CameraPreviewStateSerializable {
  availableCameras: CameraInfo[];
  activePreviews: string[]; // Array of unique_ids
  loading: boolean;
  capturing: boolean; // True when capturing all cameras
  error: string | null;
}

const initialState: CameraPreviewStateSerializable = {
  availableCameras: [],
  activePreviews: [],
  loading: false,
  capturing: false,
  error: null,
};

const cameraPreviewSlice = createSlice({
  name: 'cameraPreview',
  initialState,
  reducers: {
    setAvailableCameras: (state, action: PayloadAction<CameraInfo[]>) => {
      state.availableCameras = action.payload;
    },
    addActivePreview: (state, action: PayloadAction<string>) => {
      // action.payload is now unique_id instead of index
      if (!state.activePreviews.includes(action.payload)) {
        state.activePreviews.push(action.payload);
      }
    },
    removeActivePreview: (state, action: PayloadAction<string>) => {
      // action.payload is now unique_id instead of index
      state.activePreviews = state.activePreviews.filter(
        (uniqueId) => uniqueId !== action.payload
      );
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setCapturing: (state, action: PayloadAction<boolean>) => {
      state.capturing = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    clearAllActivePreviews: (state) => {
      state.activePreviews = [];
    },
  },
});

export const {
  setAvailableCameras,
  addActivePreview,
  removeActivePreview,
  setLoading,
  setCapturing,
  setError,
  clearError,
  clearAllActivePreviews,
} = cameraPreviewSlice.actions;

export default cameraPreviewSlice.reducer;

