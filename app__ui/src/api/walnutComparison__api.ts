// Walnut Comparison API Functions

import { apiClient } from './client__api';
import { WALNUT_PAIRS_BASE, WALNUT_PAIRS_LIST, WALNUT_PAIRS_BY_WALNUT, WALNUT_PAIRS_SPECIFIC } from './endpoints__constant';
import { WalnutComparisonDTO } from '@/types/api__type';

export interface GetAllPairsParams {
  limit?: number;
  offset?: number;
}

/**
 * Get all walnut pairs
 * Matches backend: get_all_pairs_async
 */
export const getAllPairs = async (params?: GetAllPairsParams): Promise<WalnutComparisonDTO[]> => {
  const response = await apiClient.get<WalnutComparisonDTO[]>(`${WALNUT_PAIRS_BASE}${WALNUT_PAIRS_LIST}`, {
    params: {
      limit: params?.limit,
      offset: params?.offset,
    },
  });
  return response.data;
};

/**
 * Get pairs for a specific walnut
 * Matches backend: get_pairs_by_walnut_id_async
 */
export const getPairsByWalnutId = async (walnutId: string): Promise<WalnutComparisonDTO[]> => {
  const response = await apiClient.get<WalnutComparisonDTO[]>(
    `${WALNUT_PAIRS_BASE}${WALNUT_PAIRS_BY_WALNUT}/${walnutId}`
  );
  return response.data;
};

/**
 * Get specific pair between two walnuts
 * Matches backend: get_pair_async
 */
export const getPair = async (
  walnutId: string,
  comparedWalnutId: string
): Promise<WalnutComparisonDTO> => {
  const response = await apiClient.get<WalnutComparisonDTO>(
    `${WALNUT_PAIRS_BASE}${WALNUT_PAIRS_SPECIFIC}/${walnutId}/compared/${comparedWalnutId}`
  );
  return response.data;
};

