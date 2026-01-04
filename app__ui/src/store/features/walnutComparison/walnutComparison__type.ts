// Redux State Types for Walnut Comparison

import { WalnutComparisonDTO } from '@/types/api__type';

export interface WalnutComparisonState {
  pairs: WalnutComparisonDTO[];
  loading: boolean;
  error: string | null;
  selectedPair: WalnutComparisonDTO | null;
}

