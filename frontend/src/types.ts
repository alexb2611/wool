export type YarnWeight = "Lace" | "4 Ply" | "DK" | "Aran" | "Worsted" | "Chunky" | "Super Chunky";

export interface Yarn {
  id: number;
  name: string;
  weight: YarnWeight;
  colour: string;
  fibre: string;
  metres_per_ball: number | null;
  full_balls: number;
  part_balls: number;
  extra_metres: number | null;
  estimated_total_metres: number | null;
  intended_project: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface YarnCreate {
  name: string;
  weight: YarnWeight;
  colour: string;
  fibre: string;
  metres_per_ball?: number | null;
  full_balls?: number;
  part_balls?: number;
  extra_metres?: number | null;
  intended_project?: string | null;
  notes?: string | null;
}

export interface YarnUpdate {
  name?: string;
  weight?: YarnWeight;
  colour?: string;
  fibre?: string;
  metres_per_ball?: number | null;
  full_balls?: number;
  part_balls?: number;
  extra_metres?: number | null;
  intended_project?: string | null;
  notes?: string | null;
}

export interface YarnStats {
  total_yarns: number;
  total_estimated_metres: number;
  by_weight: Record<string, number>;
  by_fibre: Record<string, number>;
}

export interface YarnListParams {
  q?: string;
  weight?: YarnWeight;
  fibre?: string;
  has_project?: boolean;
  sort_by?: string;
  sort_dir?: "asc" | "desc";
  limit?: number;
  offset?: number;
}

export interface SeedResult {
  created: number;
  skipped: number;
}
