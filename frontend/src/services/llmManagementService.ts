import apiClient from './api';
import type { ApiResponse } from '../types/admin';
import type {
  LLMConfigListResponse,
  LLMConfigResponse,
  LLMAvailableModelsResponse,
  SwitchModelResponse,
  TestPromptResponse,
  ChangeLogListResponse,
  UsageStatsResponse,
  BudgetSettings,
} from '../types/llm';

/**
 * LLM Configuration Management Service
 *
 * Handles all LLM model configuration operations for admin:
 * - View configurations (synthesis, chatbot_advisor, chatbot_guide)
 * - Switch models with maintenance mode
 * - Activate/deactivate LLM
 * - Adjust parameters (temperature, max_tokens, top_k)
 * - Test model with custom prompt
 * - View change history
 * - View usage statistics
 * - Budget and pricing management
 */

const BASE_URL = '/llm';

// ── Phase 1: View Configurations ────────────────────────────

/**
 * Get all LLM configurations
 */
export const getAllConfigs = async (): Promise<ApiResponse<LLMConfigListResponse>> => {
  const response = await apiClient.get(`${BASE_URL}/configs`);
  return response.data;
};

/**
 * Get a single LLM configuration by key
 */
export const getConfig = async (configKey: string): Promise<ApiResponse<LLMConfigResponse>> => {
  const response = await apiClient.get(`${BASE_URL}/configs/${configKey}`);
  return response.data;
};

/**
 * Get available LLM models for selection
 */
export const getAvailableModels = async (): Promise<ApiResponse<LLMAvailableModelsResponse>> => {
  const response = await apiClient.get(`${BASE_URL}/available-models`);
  return response.data;
};

// ── Phase 2: Switch Model & Maintenance ─────────────────────

/**
 * Switch LLM model for a config
 * Auto maintenance: enable → switch → disable
 */
export const switchModel = async (
  configKey: string,
  newModel: string,
  reason?: string
): Promise<ApiResponse<SwitchModelResponse>> => {
  const response = await apiClient.put(`${BASE_URL}/configs/${configKey}/model`, {
    new_model: newModel,
    reason,
  });
  return response.data;
};

/**
 * Enable/disable maintenance mode
 */
export const setMaintenance = async (
  configKey: string,
  enabled: boolean,
  message?: string
): Promise<ApiResponse<LLMConfigResponse>> => {
  const response = await apiClient.put(`${BASE_URL}/configs/${configKey}/maintenance`, {
    enabled,
    message,
  });
  return response.data;
};

// ── Phase 3: Toggle Active ──────────────────────────────────

/**
 * Activate/deactivate a LLM config
 */
export const toggleActive = async (
  configKey: string,
  isActive: boolean,
  reason?: string
): Promise<ApiResponse<LLMConfigResponse>> => {
  const response = await apiClient.put(`${BASE_URL}/configs/${configKey}/toggle`, {
    is_active: isActive,
    reason,
  });
  return response.data;
};

// ── Phase 4: Update Parameters ──────────────────────────────

/**
 * Update LLM parameters (temperature, max_tokens, top_k)
 */
export const updateParams = async (
  configKey: string,
  params: {
    temperature?: number;
    max_tokens?: number;
    top_k?: number;
    reason?: string;
  }
): Promise<ApiResponse<LLMConfigResponse>> => {
  const response = await apiClient.put(`${BASE_URL}/configs/${configKey}/params`, params);
  return response.data;
};

// ── Phase 5: Test Prompt ────────────────────────────────

/**
 * Test LLM with a custom prompt
 */
export const testPrompt = async (
  configKey: string,
  prompt: string,
  modelOverride?: string
): Promise<ApiResponse<TestPromptResponse>> => {
  const response = await apiClient.post(`${BASE_URL}/configs/${configKey}/test`, {
    prompt,
    model_override: modelOverride || undefined,
  });
  return response.data;
};

// ── Phase 6: Change Logs ───────────────────────────────

/**
 * Get change log history
 */
export const getChangeLogs = async (
  configKey?: string,
  limit: number = 50,
  offset: number = 0
): Promise<ApiResponse<ChangeLogListResponse>> => {
  const params = new URLSearchParams();
  if (configKey) params.set('config_key', configKey);
  params.set('limit', limit.toString());
  params.set('offset', offset.toString());
  const response = await apiClient.get(`${BASE_URL}/change-logs?${params.toString()}`);
  return response.data;
};

// ── Phase 7: Usage Statistics ────────────────────────────

/**
 * Get usage statistics with optional config_key filter
 */
export const getUsageStats = async (
  days: number = 30,
  configKey?: string
): Promise<ApiResponse<UsageStatsResponse>> => {
  const params = new URLSearchParams();
  params.set('days', days.toString());
  if (configKey) params.set('config_key', configKey);
  const response = await apiClient.get(`${BASE_URL}/usage-stats?${params.toString()}`);
  return response.data;
};

// ── Phase 8: Budget & Pricing ───────────────────────────

/**
 * Get budget settings
 */
export const getBudget = async (): Promise<ApiResponse<BudgetSettings>> => {
  const response = await apiClient.get(`${BASE_URL}/budget`);
  return response.data;
};

/**
 * Update budget settings
 */
export const updateBudget = async (
  data: Partial<Pick<BudgetSettings, 'monthly_budget_usd' | 'price_per_1k_input_tokens' | 'price_per_1k_output_tokens'>>
): Promise<ApiResponse<BudgetSettings>> => {
  const response = await apiClient.put(`${BASE_URL}/budget`, data);
  return response.data;
};
