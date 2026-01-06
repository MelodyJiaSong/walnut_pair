// Camera Preview State Types

import { CameraInfo } from '../../../api/cameraPreview__api';

export interface CameraPreviewState {
  availableCameras: CameraInfo[];
  activePreviews: string[]; // Array of unique_ids instead of indices
  loading: boolean;
  error: string | null;
}

