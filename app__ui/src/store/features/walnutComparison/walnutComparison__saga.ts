// Redux Saga for Walnut Comparison

import { call, put, takeEvery } from 'redux-saga/effects';
import {
  fetchAllPairs,
  fetchAllPairsSuccess,
  fetchAllPairsFailure,
  fetchPairsByWalnutId,
  fetchPairsByWalnutIdSuccess,
  fetchPairsByWalnutIdFailure,
  fetchPair,
  fetchPairSuccess,
  fetchPairFailure,
} from './walnutComparison__slice';
import { getAllPairs, getPairsByWalnutId, getPair } from '@/api/walnutComparison__api';
import { WalnutComparisonDTO } from '@/types/api__type';

// Worker saga for fetching all pairs
function* fetchAllPairsWorker() {
  try {
    const data: WalnutComparisonDTO[] = yield call(getAllPairs);
    yield put(fetchAllPairsSuccess(data));
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch pairs';
    yield put(fetchAllPairsFailure(errorMessage));
  }
}

// Watcher saga for fetchAllPairs
export function* watchFetchAllPairs() {
  yield takeEvery(fetchAllPairs.type, fetchAllPairsWorker);
}

// Worker saga for fetching pairs by walnut ID
function* fetchPairsByWalnutIdWorker(action: ReturnType<typeof fetchPairsByWalnutId>) {
  try {
    const walnutId = action.payload;
    const data: WalnutComparisonDTO[] = yield call(getPairsByWalnutId, walnutId);
    yield put(fetchPairsByWalnutIdSuccess(data));
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch pairs by walnut ID';
    yield put(fetchPairsByWalnutIdFailure(errorMessage));
  }
}

// Watcher saga for fetchPairsByWalnutId
export function* watchFetchPairsByWalnutId() {
  yield takeEvery(fetchPairsByWalnutId.type, fetchPairsByWalnutIdWorker);
}

// Worker saga for fetching specific pair
function* fetchPairWorker(action: ReturnType<typeof fetchPair>) {
  try {
    const { walnutId, comparedWalnutId } = action.payload;
    const data: WalnutComparisonDTO = yield call(getPair, walnutId, comparedWalnutId);
    yield put(fetchPairSuccess(data));
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Failed to fetch pair';
    yield put(fetchPairFailure(errorMessage));
  }
}

// Watcher saga for fetchPair
export function* watchFetchPair() {
  yield takeEvery(fetchPair.type, fetchPairWorker);
}

