// ============== LLM Management Types ==============

/**
 * LLM Configuration response from API
 */
export interface LLMConfigResponse {
  id: string;
  config_key: string;
  display_name: string;
  description?: string;
  model_name: string;
  temperature: number;
  max_tokens: number;
  top_k: number;
  is_active: boolean;
  is_maintenance: boolean;
  maintenance_message?: string;
  env_defaults?: {
    model_name: string;
    temperature: number;
    max_tokens: number;
    top_k?: number;
  };
  created_at?: string;
  updated_at?: string;
}

/**
 * List of all LLM configurations
 */
export interface LLMConfigListResponse {
  configs: LLMConfigResponse[];
  total: number;
}

/**
 * Available LLM model for selection
 */
export interface LLMAvailableModel {
  id: string;
  name: string;
  description: string;
  tier: 'low' | 'mid' | 'high';
}

/**
 * Available models response
 */
export interface LLMAvailableModelsResponse {
  models: LLMAvailableModel[];
}

/**
 * Switch model response
 */
export interface SwitchModelResponse {
  config_key: string;
  old_model: string;
  new_model: string;
  is_maintenance: boolean;
  message: string;
}

/**
 * Test prompt response
 */
export interface TestPromptResponse {
  config_key: string;
  model_used: string;
  prompt: string;
  response: string;
  tokens_used: number;
  response_time_ms: number;
}

/**
 * Change log entry (audit)
 */
export interface ChangeLogEntry {
  id: string;
  config_key: string;
  display_name: string;
  change_type: string;
  old_values?: Record<string, any>;
  new_values?: Record<string, any>;
  reason?: string;
  changed_by?: string;
  changed_by_email?: string;
  created_at: string;
}

export interface ChangeLogListResponse {
  logs: ChangeLogEntry[];
  total: number;
}

/**
 * Usage statistics
 */
export interface UsageConfigStats {
  config_key: string;
  display_name: string;
  total_requests: number;
  success_count: number;
  error_count: number;
  total_tokens: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  avg_response_time_ms: number;
  last_used_at?: string;
}

export interface BudgetInfo {
  monthly_budget_usd: number;
  price_per_1k_input_tokens: number;
  price_per_1k_output_tokens: number;
  currency: string;
  monthly_prompt_tokens: number;
  monthly_completion_tokens: number;
  monthly_total_tokens: number;
  monthly_estimated_cost: number;
  budget_usage_percent: number;
}

export interface UsageStatsResponse {
  total_requests: number;
  total_tokens: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  estimated_cost: number;
  avg_response_time_ms: number;
  success_rate: number;
  per_config: UsageConfigStats[];
  period_days: number;
  budget?: BudgetInfo;
}

export interface BudgetSettings {
  monthly_budget_usd: number;
  price_per_1k_input_tokens: number;
  price_per_1k_output_tokens: number;
  currency: string;
  updated_at?: string;
}
