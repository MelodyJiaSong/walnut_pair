// Root Saga

import { all, fork } from 'redux-saga/effects';
import { watchFetchAllPairs, watchFetchPairsByWalnutId, watchFetchPair } from './features/walnutComparison/walnutComparison__saga';
import { watchCameraPreview } from './cameraPreview/cameraPreview__saga';

// Root saga that combines all feature sagas
export default function* rootSaga() {
  yield all([
    fork(watchFetchAllPairs),
    fork(watchFetchPairsByWalnutId),
    fork(watchFetchPair),
    fork(watchCameraPreview),
  ]);
}

