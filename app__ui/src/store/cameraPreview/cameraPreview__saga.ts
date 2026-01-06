// Camera Preview Redux Saga

import { call, put, takeEvery } from 'redux-saga/effects';
import {
  getAvailableCameras,
  startCameraPreview,
  stopCameraPreview,
  StartPreviewRequest,
  StopPreviewRequest,
} from '../../api/cameraPreview__api';
import {
  setAvailableCameras,
  addActivePreview,
  removeActivePreview,
  setLoading,
  setError,
  clearError,
} from './cameraPreview__slice';

// Action types
const FETCH_AVAILABLE_CAMERAS = 'cameraPreview/fetchAvailableCameras';
const START_PREVIEW = 'cameraPreview/startPreview';
const STOP_PREVIEW = 'cameraPreview/stopPreview';

export const fetchAvailableCameras = () => ({
  type: FETCH_AVAILABLE_CAMERAS,
});

export const startPreview = (request: StartPreviewRequest) => ({
  type: START_PREVIEW,
  payload: request,
});

export const stopPreview = (request: StopPreviewRequest) => ({
  type: STOP_PREVIEW,
  payload: request,
});

// Sagas
function* fetchAvailableCamerasSaga() {
  try {
    yield put(setLoading(true));
    yield put(clearError());
    const cameras = yield call(getAvailableCameras);
    yield put(setAvailableCameras(cameras));
  } catch (error: any) {
    yield put(setError(error.message || 'Failed to fetch available cameras'));
  } finally {
    yield put(setLoading(false));
  }
}

function* startPreviewSaga(action: { type: string; payload: StartPreviewRequest }) {
  try {
    yield put(setLoading(true));
    yield put(clearError());
    const response = yield call(startCameraPreview, action.payload);
    if (response.success) {
      // Use unique_id instead of index
      yield put(addActivePreview(action.payload.camera_unique_id));
    } else {
      yield put(setError('Failed to start camera preview'));
    }
  } catch (error: any) {
    yield put(setError(error.message || 'Failed to start camera preview'));
  } finally {
    yield put(setLoading(false));
  }
}

function* stopPreviewSaga(action: { type: string; payload: StopPreviewRequest }) {
  try {
    yield put(setLoading(true));
    yield put(clearError());
    const response = yield call(stopCameraPreview, action.payload);
    if (response.success) {
      // Use unique_id instead of index
      yield put(removeActivePreview(action.payload.camera_unique_id));
    } else {
      yield put(setError('Failed to stop camera preview'));
    }
  } catch (error: any) {
    yield put(setError(error.message || 'Failed to stop camera preview'));
  } finally {
    yield put(setLoading(false));
  }
}

// Watchers
export function* watchCameraPreview() {
  yield takeEvery(FETCH_AVAILABLE_CAMERAS, fetchAvailableCamerasSaga);
  yield takeEvery(START_PREVIEW, startPreviewSaga);
  yield takeEvery(STOP_PREVIEW, stopPreviewSaga);
}

