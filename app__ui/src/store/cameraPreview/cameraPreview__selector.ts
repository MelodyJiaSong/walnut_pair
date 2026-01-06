// Camera Preview Selectors

import { createSelector } from 'reselect';
import { RootState } from '../store__config';

const selectCameraPreviewState = (state: RootState) => state.cameraPreview;

export const selectAvailableCameras = createSelector(
  [selectCameraPreviewState],
  (cameraPreview) => cameraPreview.availableCameras
);

export const selectActivePreviews = createSelector(
  [selectCameraPreviewState],
  (cameraPreview) => cameraPreview.activePreviews
);

export const selectIsPreviewActive = (cameraUniqueId: string) =>
  createSelector([selectActivePreviews], (activePreviews) =>
    activePreviews.includes(cameraUniqueId)
  );

export const selectLoading = createSelector(
  [selectCameraPreviewState],
  (cameraPreview) => cameraPreview.loading
);

export const selectError = createSelector(
  [selectCameraPreviewState],
  (cameraPreview) => cameraPreview.error
);

export const selectCapturing = createSelector(
  [selectCameraPreviewState],
  (cameraPreview) => cameraPreview.capturing
);

