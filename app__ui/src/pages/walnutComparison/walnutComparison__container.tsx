'use client';

// Walnut Comparison Container (Redux Connection)

import { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '@/store/hooks';
import { fetchAllPairs } from '@/store/features/walnutComparison/walnutComparison__slice';
import { selectAllPairs, selectLoading, selectError } from '@/store/features/walnutComparison/walnutComparison__selector';
import ComparisonGrid from '@/features/walnutComparison/components/comparisonGrid';
import { Alert } from 'antd';

export default function WalnutComparisonContainer() {
  const dispatch = useAppDispatch();
  const pairs = useAppSelector(selectAllPairs);
  const loading = useAppSelector(selectLoading);
  const error = useAppSelector(selectError);

  useEffect(() => {
    // Fetch all pairs when component mounts
    dispatch(fetchAllPairs());
  }, [dispatch]);

  if (error) {
    return (
      <Alert
        message="Error"
        description={error}
        type="error"
        showIcon
        closable
      />
    );
  }

  return (
    <div className="walnut-comparison-container">
      <h2>Walnut Comparison Results</h2>
      <ComparisonGrid data={pairs} loading={loading} />
    </div>
  );
}

