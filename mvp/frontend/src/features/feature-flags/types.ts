/**
 * Feature Flags Types
 */

export interface FeatureFlag {
  name: string;
  default: boolean | null;
  override: string | null;
  effective: boolean | string | null;
}

export interface FeatureFlagList {
  count: number;
  flags: Record<string, FeatureFlag>;
}

export interface FeatureFlagUpdate {
  value: string;
}

export interface FeatureFlagUserResolved {
  user_id: string;
  flags: Record<string, boolean>;
}

export interface KillSwitchResponse {
  module: string;
  flag_name: string;
  action: string;
  status: string;
}
