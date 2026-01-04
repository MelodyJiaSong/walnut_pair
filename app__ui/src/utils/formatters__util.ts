// Formatter Utility Functions

/**
 * Format a number as a percentage
 */
export const formatPercentage = (value: number | null, decimals: number = 2): string => {
  if (value === null) return 'N/A';
  return `${(value * 100).toFixed(decimals)}%`;
};

/**
 * Format a number with fixed decimal places
 */
export const formatNumber = (value: number, decimals: number = 2): string => {
  return value.toFixed(decimals);
};

/**
 * Format a date string to locale string
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString();
};

