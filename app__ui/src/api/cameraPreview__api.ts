// Camera Preview API

import { apiClient } from './client__api';
import {
  CAMERA_PREVIEW_BASE,
  CAMERA_PREVIEW_LIST,
  CAMERA_PREVIEW_START,
  CAMERA_PREVIEW_STOP,
  CAMERA_PREVIEW_STREAM,
  CAMERA_PREVIEW_CAPTURE,
} from './endpoints__constant';

export interface CameraInfo {
  unique_id: string;
  index: number;
  name: string | null;
  vid: number | null;
  pid: number | null;
}

export interface StartPreviewRequest {
  camera_unique_id: string;
  width?: number;
  height?: number;
}

export interface StopPreviewRequest {
  camera_unique_id: string;
}

export interface StartPreviewResponse {
  success: boolean;
  camera_unique_id: string;
  camera_index: number;
}

export interface StopPreviewResponse {
  success: boolean;
  camera_unique_id: string;
  camera_index: number;
}

export interface CaptureAllResponse {
  success: boolean;
  captured_count: number;
  total_cameras: number;
  saved_paths: Array<{ [key: string]: string }>;
  errors: string[];
}

/**
 * Get list of available cameras with unique identifiers
 */
export const getAvailableCameras = async (): Promise<CameraInfo[]> => {
  const response = await apiClient.get<CameraInfo[]>(
    `${CAMERA_PREVIEW_BASE}${CAMERA_PREVIEW_LIST}`
  );
  return response.data;
};

/**
 * Start camera preview stream using unique identifier
 */
export const startCameraPreview = async (
  request: StartPreviewRequest
): Promise<StartPreviewResponse> => {
  const response = await apiClient.post<StartPreviewResponse>(
    `${CAMERA_PREVIEW_BASE}${CAMERA_PREVIEW_START}`,
    request
  );
  return response.data;
};

/**
 * Stop camera preview stream using unique identifier
 */
export const stopCameraPreview = async (
  request: StopPreviewRequest
): Promise<StopPreviewResponse> => {
  const response = await apiClient.post<StopPreviewResponse>(
    `${CAMERA_PREVIEW_BASE}${CAMERA_PREVIEW_STOP}`,
    request
  );
  return response.data;
};

/**
 * Get WebSocket URL for camera preview stream using unique identifier
 */
export const getCameraPreviewWebSocketUrl = (cameraUniqueId: string): string => {
  // For client-side, use window.location if available, otherwise fallback to env
  let baseURL = 'http://localhost:8000';
  
  if (typeof window !== 'undefined') {
    // Use current host for WebSocket connection
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    baseURL = `${protocol}//${host}`;
  } else {
    // Server-side fallback
    baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const wsProtocol = baseURL.startsWith('https') ? 'wss' : 'ws';
    baseURL = baseURL.replace(/^https?/, wsProtocol);
  }
  
  return `${baseURL}${CAMERA_PREVIEW_BASE}${CAMERA_PREVIEW_STREAM}/ws?camera_unique_id=${encodeURIComponent(cameraUniqueId)}`;
};

/**
 * Capture images from all available cameras simultaneously
 */
export const captureAllCameras = async (): Promise<CaptureAllResponse> => {
  const response = await apiClient.post<CaptureAllResponse>(
    `${CAMERA_PREVIEW_BASE}${CAMERA_PREVIEW_CAPTURE}`
  );
  return response.data;
};

