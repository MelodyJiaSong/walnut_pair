// API Response Types (matching backend DTOs)

export interface WalnutComparisonDTO {
  id: number;
  walnut_id: string;
  compared_walnut_id: string;
  width_diff_mm: number;
  height_diff_mm: number;
  thickness_diff_mm: number;
  basic_similarity: number | null;
  advanced_similarity: number | null;
  final_similarity: number;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

