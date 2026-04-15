import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { toast } from 'sonner'
import { Toaster } from 'sonner'
import {
  Brain, MessageSquare, BookOpen, Cpu, CheckCircle2,
  XCircle, AlertTriangle, Settings, Info, RefreshCw,
  Wrench, X, Power, SlidersHorizontal, Zap, History, BarChart3,
  DollarSign, Filter
} from 'lucide-react'
import * as llmService from '../../services/llmManagementService'
import type { LLMConfigResponse, LLMAvailableModel, TestPromptResponse, ChangeLogEntry, UsageStatsResponse, BudgetInfo } from '../../types/llm'
import StatCard from './shared/StatCard'
import styles from './LLMManagement.module.css'

// Map config_key to icon + CSS class
const CONFIG_META: Record<string, { icon: typeof Brain; cssClass: string; color: 'blue' | 'green' | 'orange' }> = {
  synthesis: { icon: Brain, cssClass: styles.synthesis, color: 'blue' },
  chatbot_advisor: { icon: MessageSquare, cssClass: styles.chatbotAdvisor, color: 'green' },
  chatbot_guide: { icon: BookOpen, cssClass: styles.chatbotGuide, color: 'orange' },
}

// Model tier lookup
const MODEL_TIERS: Record<string, { tier: string; label: string }> = {
  'gpt-4.1-mini': { tier: 'mid', label: 'Trung bình' },
  'gpt-4.1-nano': { tier: 'low', label: 'Tiết kiệm' },
  'gpt-4.1': { tier: 'high', label: 'Cao cấp' },
  'gpt-4o-mini': { tier: 'low', label: 'Tiết kiệm' },
  'gpt-4o': { tier: 'high', label: 'Cao cấp' },
}

export default function LLMManagement() {
  const { t } = useTranslation()
  const [configs, setConfigs] = useState<LLMConfigResponse[]>([])
  const [availableModels, setAvailableModels] = useState<LLMAvailableModel[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'config' | 'stats' | 'logs'>('config')

  // Phase 2: Switch model modal
  const [switchModalOpen, setSwitchModalOpen] = useState(false)
  const [switchTarget, setSwitchTarget] = useState<LLMConfigResponse | null>(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [switchReason, setSwitchReason] = useState('')
  const [switching, setSwitching] = useState(false)

  // Phase 2: Maintenance toggle
  const [maintenanceLoading, setMaintenanceLoading] = useState<string | null>(null)

  // Phase 3: Toggle active
  const [toggleLoading, setToggleLoading] = useState<string | null>(null)

  // Phase 4: Edit params modal
  const [paramsModalOpen, setParamsModalOpen] = useState(false)
  const [paramsTarget, setParamsTarget] = useState<LLMConfigResponse | null>(null)
  const [editTemperature, setEditTemperature] = useState(0.3)
  const [editMaxTokens, setEditMaxTokens] = useState(2000)
  const [editTopK, setEditTopK] = useState(5)
  const [paramsReason, setParamsReason] = useState('')
  const [savingParams, setSavingParams] = useState(false)

  // Phase 5: Test prompt modal
  const [testModalOpen, setTestModalOpen] = useState(false)
  const [testTarget, setTestTarget] = useState<LLMConfigResponse | null>(null)
  const [testPrompt, setTestPrompt] = useState('')
  const [testModelOverride, setTestModelOverride] = useState('')
  const [testing, setTesting] = useState(false)
  const [testResult, setTestResult] = useState<TestPromptResponse | null>(null)

  // Phase 6: Change logs
  const [changeLogs, setChangeLogs] = useState<ChangeLogEntry[]>([])
  const [logTotal, setLogTotal] = useState(0)
  const [logFilter, setLogFilter] = useState('')
  const [logPage, setLogPage] = useState(1)
  const [logsLoading, setLogsLoading] = useState(false)
  const LOG_PAGE_SIZE = 10

  // Phase 7: Usage stats
  const [usageStats, setUsageStats] = useState<UsageStatsResponse | null>(null)
  const [usagePeriod, setUsagePeriod] = useState(30)
  const [usageFilter, setUsageFilter] = useState('')

  // Phase 8: Budget modal
  const [budgetModalOpen, setBudgetModalOpen] = useState(false)
  const [editBudget, setEditBudget] = useState(0)
  const [editInputPrice, setEditInputPrice] = useState(0.40)
  const [editOutputPrice, setEditOutputPrice] = useState(1.60)
  const [savingBudget, setSavingBudget] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [configsResult, modelsResult] = await Promise.all([
        llmService.getAllConfigs(),
        llmService.getAvailableModels(),
      ])

      if (configsResult.success && configsResult.data) {
        setConfigs(configsResult.data.configs)
      }
      if (modelsResult.success && modelsResult.data) {
        setAvailableModels(modelsResult.data.models)
      }
      // Load change logs too
      await loadChangeLogs()
      // Load usage stats
      await loadUsageStats(usagePeriod)
    } catch (err: any) {
      toast.error(err.message || 'Không thể tải cấu hình LLM')
    } finally {
      setLoading(false)
    }
  }

  const activeCount = configs.filter(c => c.is_active).length
  const maintenanceCount = configs.filter(c => c.is_maintenance).length
  const totalConfigs = configs.length

  const getModelTier = (modelName: string) => {
    return MODEL_TIERS[modelName] || { tier: 'mid', label: 'Trung bình' }
  }

  const getTierClass = (tier: string) => {
    switch (tier) {
      case 'low': return styles.tierLow
      case 'high': return styles.tierHigh
      default: return styles.tierMid
    }
  }

  // ── Phase 2: Switch Model ───────────────────────────────

  const openSwitchModal = (config: LLMConfigResponse) => {
    setSwitchTarget(config)
    setSelectedModel('')
    setSwitchReason('')
    setSwitchModalOpen(true)
  }

  const closeSwitchModal = () => {
    setSwitchModalOpen(false)
    setSwitchTarget(null)
    setSelectedModel('')
    setSwitchReason('')
  }

  const handleSwitchModel = async () => {
    if (!switchTarget || !selectedModel) return

    try {
      setSwitching(true)
      const result = await llmService.switchModel(
        switchTarget.config_key,
        selectedModel,
        switchReason || undefined
      )
      if (result.success) {
        toast.success(result.message || `Đã đổi model thành công`)
        closeSwitchModal()
        await loadData()
      } else {
        toast.error(result.message || 'Đổi model thất bại')
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || 'Đổi model thất bại'
      toast.error(msg)
    } finally {
      setSwitching(false)
    }
  }

  // ── Phase 2: Maintenance Toggle ─────────────────────────

  const handleToggleMaintenance = async (config: LLMConfigResponse) => {
    const newEnabled = !config.is_maintenance
    const action = newEnabled ? 'bật' : 'tắt'

    try {
      setMaintenanceLoading(config.config_key)
      const result = await llmService.setMaintenance(
        config.config_key,
        newEnabled,
        newEnabled ? 'Bảo trì theo yêu cầu admin' : undefined
      )
      if (result.success) {
        toast.success(`Đã ${action} chế độ bảo trì cho "${config.display_name}"`)
        await loadData()
      } else {
        toast.error(result.message || `${action} bảo trì thất bại`)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || `${action} bảo trì thất bại`
      toast.error(msg)
    } finally {
      setMaintenanceLoading(null)
    }
  }

  // ── Phase 3: Toggle Active ───────────────────────────────

  const handleToggleActive = async (config: LLMConfigResponse) => {
    const newActive = !config.is_active
    const action = newActive ? 'kích hoạt' : 'tắt'

    // Confirm before deactivating
    if (!newActive) {
      const confirmed = window.confirm(
        `Bạn chắc chắn muốn TẮT cấu hình "${config.display_name}"?\n\n` +
        'Khi tắt, hệ thống sẽ không gọi LLM cho chức năng này mà sẽ fallback sang dữ liệu có sẵn.'
      )
      if (!confirmed) return
    }

    try {
      setToggleLoading(config.config_key)
      const result = await llmService.toggleActive(
        config.config_key,
        newActive
      )
      if (result.success) {
        toast.success(`Đã ${action} cấu hình "${config.display_name}"`)
        await loadData()
      } else {
        toast.error(result.message || `${action} thất bại`)
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || `${action} thất bại`
      toast.error(msg)
    } finally {
      setToggleLoading(null)
    }
  }

  // ── Phase 4: Edit Params ───────────────────────────────

  const openParamsModal = (config: LLMConfigResponse) => {
    setParamsTarget(config)
    setEditTemperature(config.temperature)
    setEditMaxTokens(config.max_tokens)
    setEditTopK(config.top_k)
    setParamsReason('')
    setParamsModalOpen(true)
  }

  const closeParamsModal = () => {
    setParamsModalOpen(false)
    setParamsTarget(null)
  }

  const handleUpdateParams = async () => {
    if (!paramsTarget) return

    // Only send changed values
    const params: Record<string, any> = {}
    if (editTemperature !== paramsTarget.temperature) params.temperature = editTemperature
    if (editMaxTokens !== paramsTarget.max_tokens) params.max_tokens = editMaxTokens
    if (editTopK !== paramsTarget.top_k) params.top_k = editTopK

    if (Object.keys(params).length === 0) {
      toast.info('Không có tham số nào thay đổi')
      return
    }

    if (paramsReason) params.reason = paramsReason

    try {
      setSavingParams(true)
      const result = await llmService.updateParams(paramsTarget.config_key, params)
      if (result.success) {
        toast.success(result.message || 'Đã cập nhật tham số thành công')
        closeParamsModal()
        await loadData()
      } else {
        toast.error(result.message || 'Cập nhật thất bại')
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || 'Cập nhật thất bại'
      toast.error(msg)
    } finally {
      setSavingParams(false)
    }
  }

  // ── Phase 5: Test Prompt ───────────────────────────────

  const openTestModal = (config: LLMConfigResponse) => {
    setTestTarget(config)
    setTestPrompt('')
    setTestModelOverride('')
    setTestResult(null)
    setTestModalOpen(true)
  }

  const closeTestModal = () => {
    setTestModalOpen(false)
    setTestTarget(null)
    setTestResult(null)
  }

  const handleTestPrompt = async () => {
    if (!testTarget || !testPrompt.trim()) return

    try {
      setTesting(true)
      setTestResult(null)
      const result = await llmService.testPrompt(
        testTarget.config_key,
        testPrompt.trim(),
        testModelOverride || undefined
      )
      if (result.success && result.data) {
        setTestResult(result.data)
      } else {
        toast.error(result.message || 'Test thất bại')
      }
    } catch (err: any) {
      const msg = err?.response?.data?.detail || err.message || 'Test thất bại'
      toast.error(msg)
    } finally {
      setTesting(false)
    }
  }

  // ── Phase 6: Change Logs ──────────────────────────────

  const CHANGE_TYPE_LABELS: Record<string, string> = {
    model_change: 'Đổi model',
    param_update: 'Cập nhật tham số',
    activate: 'Kích hoạt',
    deactivate: 'Tắt',
    maintenance_on: 'Bật bảo trì',
    maintenance_off: 'Tắt bảo trì',
  }

  const loadChangeLogs = async (filterKey?: string, page: number = 1) => {
    try {
      setLogsLoading(true)
      const offset = (page - 1) * LOG_PAGE_SIZE
      const result = await llmService.getChangeLogs(
        filterKey || undefined,
        LOG_PAGE_SIZE,
        offset
      )
      if (result.success && result.data) {
        setChangeLogs(result.data.logs)
        setLogTotal(result.data.total)
        setLogPage(page)
      }
    } catch {
      // silent fail for logs
    } finally {
      setLogsLoading(false)
    }
  }

  const handleLogFilterChange = (key: string) => {
    setLogFilter(key)
    loadChangeLogs(key, 1)
  }

  const logTotalPages = Math.ceil(logTotal / LOG_PAGE_SIZE)

  const formatValues = (vals: Record<string, any> | undefined) => {
    if (!vals) return ''
    // Human-readable labels
    const labels: Record<string, string> = {
      is_maintenance: 'Bảo trì',
      is_active: 'Trạng thái',
      maintenance_message: 'Thông báo bảo trì',
      model_name: 'Model',
      temperature: 'Temperature',
      max_tokens: 'Max Tokens',
      top_k: 'Top K',
    }
    const formatVal = (v: any) => {
      if (v === null || v === undefined) return '—'
      if (v === true) return 'Bật'
      if (v === false) return 'Tắt'
      return String(v)
    }
    return Object.entries(vals)
      .filter(([k]) => k !== 'maintenance_message')
      .map(([k, v]) => `${labels[k] || k}: ${formatVal(v)}`)
      .join(', ')
  }

  // ── Phase 7: Usage Stats ──────────────────────────────

  const loadUsageStats = async (days: number, configKey?: string) => {
    try {
      const result = await llmService.getUsageStats(days, configKey || undefined)
      if (result.success && result.data) {
        setUsageStats(result.data)
      }
    } catch {
      // silent
    }
  }

  const handlePeriodChange = (days: number) => {
    setUsagePeriod(days)
    loadUsageStats(days, usageFilter)
  }

  const handleUsageFilterChange = (key: string) => {
    setUsageFilter(key)
    loadUsageStats(usagePeriod, key)
  }

  // ── Phase 8: Budget ────────────────────────────────────

  const openBudgetModal = () => {
    if (usageStats?.budget) {
      setEditBudget(usageStats.budget.monthly_budget_usd)
      setEditInputPrice(usageStats.budget.price_per_1k_input_tokens)
      setEditOutputPrice(usageStats.budget.price_per_1k_output_tokens)
    }
    setBudgetModalOpen(true)
  }

  const handleSaveBudget = async () => {
    setSavingBudget(true)
    try {
      const result = await llmService.updateBudget({
        monthly_budget_usd: editBudget,
        price_per_1k_input_tokens: editInputPrice,
        price_per_1k_output_tokens: editOutputPrice,
      })
      if (result.success) {
        toast.success('Cập nhật budget thành công')
        setBudgetModalOpen(false)
        loadUsageStats(usagePeriod, usageFilter)
      }
    } catch {
      toast.error('Lỗi khi cập nhật budget')
    } finally {
      setSavingBudget(false)
    }
  }

  // --- LOADING ---
  if (loading) {
    return (
      <div className={styles.llmManagementPage}>
        <div className={styles.loadingContainer}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>Đang tải cấu hình LLM...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.llmManagementPage}>
      <Toaster richColors position="top-right" />

      {/* Header */}
      <div className={styles.pageHeader}>
        <div className={styles.pageTitle}>
          <h1>Quản lý LLM</h1>
          <p>Cấu hình và quản lý các model ngôn ngữ lớn (LLM) cho hệ thống</p>
        </div>
      </div>

      {/* Stats */}
      <div className={styles.statsGrid}>
        <StatCard
          icon={Cpu}
          value={totalConfigs}
          label="Tổng cấu hình"
          color="blue"
        />
        <StatCard
          icon={CheckCircle2}
          value={activeCount}
          label="Đang hoạt động"
          color="green"
        />
        <StatCard
          icon={AlertTriangle}
          value={maintenanceCount}
          label="Đang bảo trì"
          color={maintenanceCount > 0 ? 'orange' : 'default'}
        />
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabBar}>
        <button
          className={`${styles.tabBtn} ${activeTab === 'config' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('config')}
        >
          <Settings size={16} />
          Cấu hình
        </button>
        <button
          className={`${styles.tabBtn} ${activeTab === 'stats' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('stats')}
        >
          <BarChart3 size={16} />
          Thống kê sử dụng
        </button>
        <button
          className={`${styles.tabBtn} ${activeTab === 'logs' ? styles.tabActive : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          <History size={16} />
          Lịch sử thay đổi
        </button>
      </div>

      {/* ── Tab 1: Cấu hình ──────────────────────────────── */}
      {activeTab === 'config' && (
        <div>

      {/* Info Section */}
      <div className={styles.infoSection}>
        <h3 className={styles.infoSectionTitle}>
          <Info size={18} />
          Thông tin hệ thống
        </h3>
        <div className={styles.infoGrid}>
          <div className={styles.infoItem}>
            <p className={styles.infoLabel}>API Provider</p>
            <p className={styles.infoValue}>OpenAI</p>
          </div>
          <div className={styles.infoItem}>
            <p className={styles.infoLabel}>Model có sẵn</p>
            <p className={styles.infoValue}>{availableModels.length} model</p>
          </div>
          <div className={styles.infoItem}>
            <p className={styles.infoLabel}>API Key</p>
            <p className={styles.infoValue}>•••••••••••••••</p>
          </div>
          <div className={styles.infoItem}>
            <p className={styles.infoLabel}>Trạng thái kết nối</p>
            <p className={styles.infoValue} style={{ color: '#16a34a' }}>✓ Đã cấu hình</p>
          </div>
        </div>
      </div>

      {/* Config Cards */}
      {configs.length === 0 ? (
        <div className={styles.emptyState}>
          <Settings size={64} />
          <p>Chưa có cấu hình LLM nào</p>
        </div>
      ) : (
        <div className={styles.configCardsGrid}>
          {configs.map((config) => {
            const meta = CONFIG_META[config.config_key] || { icon: Cpu, cssClass: '', color: 'blue' as const }
            const IconComp = meta.icon
            const tier = getModelTier(config.model_name)

            return (
              <div key={config.id} className={styles.configCard}>
                {/* Card Header */}
                <div className={styles.configCardHeader}>
                  <div className={styles.configCardTitle}>
                    <div className={`${styles.configIcon} ${meta.cssClass}`}>
                      <IconComp size={20} />
                    </div>
                    <div>
                      <h3>{config.display_name}</h3>
                      <p>{config.config_key}</p>
                    </div>
                  </div>
                  <div className={styles.configBadges}>
                    {config.is_maintenance && (
                      <span className={styles.badgeMaintenance}>
                        <AlertTriangle size={10} />
                        Bảo trì
                      </span>
                    )}
                    {config.is_active ? (
                      <span className={styles.badgeActive}>
                        <CheckCircle2 size={10} />
                        Hoạt động
                      </span>
                    ) : (
                      <span className={styles.badgeInactive}>
                        <XCircle size={10} />
                        Tắt
                      </span>
                    )}
                  </div>
                </div>

                {/* Card Body */}
                <div className={styles.configCardBody}>
                  <div className={styles.configParams}>
                    {/* Model Name - full width */}
                    <div className={`${styles.paramItem} ${styles.paramModelName}`}>
                      <p className={styles.paramLabel}>Model</p>
                      <div className={styles.modelNameValue}>
                        <span className={styles.paramValue}>{config.model_name}</span>
                        <span className={`${styles.modelBadge} ${getTierClass(tier.tier)}`}>
                          {tier.label}
                        </span>
                      </div>
                    </div>

                    {/* Temperature */}
                    <div className={styles.paramItem}>
                      <p className={styles.paramLabel}>Temperature</p>
                      <p className={styles.paramValue}>{config.temperature}</p>
                    </div>

                    {/* Max Tokens */}
                    <div className={styles.paramItem}>
                      <p className={styles.paramLabel}>Max Tokens</p>
                      <p className={styles.paramValue}>{config.max_tokens.toLocaleString()}</p>
                    </div>

                    {/* Top K */}
                    <div className={styles.paramItem}>
                      <p className={styles.paramLabel}>Top K</p>
                      <p className={styles.paramValue}>{config.top_k}</p>
                    </div>

                    {/* Updated At */}
                    <div className={styles.paramItem}>
                      <p className={styles.paramLabel}>Cập nhật lần cuối</p>
                      <p className={styles.paramValue} style={{ fontSize: '0.8125rem' }}>
                        {config.updated_at
                          ? new Date(config.updated_at).toLocaleString('vi-VN')
                          : '—'}
                      </p>
                    </div>
                  </div>

                  {/* Maintenance Banner */}
                  {config.is_maintenance && (
                    <div className={styles.maintenanceBanner}>
                      <AlertTriangle size={16} className={styles.maintenanceIcon} />
                      {config.maintenance_message || 'Đang trong chế độ bảo trì'}
                    </div>
                  )}

                  {/* Description */}
                  {config.description && (
                    <div className={styles.configDescription}>
                      {config.description}
                    </div>
                  )}
                </div>

                {/* Phase 2: Card Actions */}
                <div className={styles.cardActions}>
                  <button
                    className={styles.btnSwitchModel}
                    onClick={() => openSwitchModal(config)}
                  >
                    <RefreshCw size={14} />
                    Đổi model
                  </button>

                  <button
                    className={styles.btnEditParams}
                    onClick={() => openParamsModal(config)}
                  >
                    <SlidersHorizontal size={14} />
                    Chỉnh tham số
                  </button>

                  <button
                    className={styles.btnTest}
                    onClick={() => openTestModal(config)}
                  >
                    <Zap size={14} />
                    Test
                  </button>

                  {config.is_maintenance ? (
                    <button
                      className={styles.btnMaintenanceOff}
                      onClick={() => handleToggleMaintenance(config)}
                      disabled={maintenanceLoading === config.config_key}
                    >
                      <Wrench size={14} />
                      {maintenanceLoading === config.config_key ? 'Đang xử lý...' : 'Tắt bảo trì'}
                    </button>
                  ) : (
                    <button
                      className={styles.btnMaintenance}
                      onClick={() => handleToggleMaintenance(config)}
                      disabled={maintenanceLoading === config.config_key}
                    >
                      <Wrench size={14} />
                      {maintenanceLoading === config.config_key ? 'Đang xử lý...' : 'Bảo trì'}
                    </button>
                  )}

                  {/* Phase 3: Toggle Active */}
                  <div className={styles.toggleGroup}>
                    <Power size={14} style={{ color: config.is_active ? '#1E9378' : '#94a3b8' }} />
                    <span className={styles.toggleLabel}>
                      Trạng thái: {config.is_active ? 'Hoạt động' : 'Đã tắt'}
                    </span>
                    <button
                      className={`${styles.toggleSwitch} ${config.is_active ? styles.active : ''} ${toggleLoading === config.config_key ? styles.loading : ''}`}
                      onClick={() => handleToggleActive(config)}
                      disabled={toggleLoading === config.config_key}
                      title={config.is_active ? 'Click để tắt' : 'Click để kích hoạt'}
                    >
                      <span className={styles.toggleKnob}></span>
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
      </div>
      )}

      {/* ── Tab 2: Lịch sử thay đổi ─────────────────────── */}
      {activeTab === 'logs' && (
      <div className={styles.auditSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>
            <History size={18} />
            Lịch sử thay đổi
          </h3>
          <div className={styles.filterGroup}>
            <select
              className={styles.filterSelect}
              value={logFilter}
              onChange={(e) => handleLogFilterChange(e.target.value)}
            >
              <option value="">Tất cả cấu hình</option>
              {configs.map(c => (
                <option key={c.config_key} value={c.config_key}>{c.display_name}</option>
              ))}
            </select>
          </div>
        </div>

        {changeLogs.length === 0 ? (
          <div className={styles.auditEmpty}>
            {logsLoading ? 'Đang tải lịch sử...' : 'Chưa có lịch sử thay đổi nào'}
          </div>
        ) : (
          <>
            <div className={styles.timeline}>
              {changeLogs.map((log) => (
                <div key={log.id} className={styles.timelineItem}>
                  <div className={`${styles.timelineDot} ${styles[log.change_type] || ''}`}></div>
                  <div className={styles.timelineHeader}>
                    <span className={`${styles.changeTypeBadge} ${styles[log.change_type] || ''}`}>
                      {CHANGE_TYPE_LABELS[log.change_type] || log.change_type}
                    </span>
                    <span className={styles.timelineConfigName}>{log.display_name}</span>
                    {log.changed_by_email && (
                      <span className={styles.timelineActor}>{log.changed_by_email}</span>
                    )}
                    <span className={styles.timelineTime}>
                      {new Date(log.created_at).toLocaleString('vi-VN')}
                    </span>
                  </div>
                  <div className={styles.timelineBody}>
                    {(log.old_values || log.new_values) && (
                      <div className={styles.timelineChanges}>
                        {log.old_values && (
                          <span className={styles.changeOld}>{formatValues(log.old_values)}</span>
                        )}
                        {log.old_values && log.new_values && (
                          <span className={styles.changeArrow}>→</span>
                        )}
                        {log.new_values && (
                          <span className={styles.changeNew}>{formatValues(log.new_values)}</span>
                        )}
                      </div>
                    )}
                    {log.reason && (
                      <div className={styles.timelineReason}>"{log.reason}"</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
            {logTotalPages > 1 && (
              <div className={styles.pagination}>
                <button
                  className={styles.pageBtn}
                  onClick={() => loadChangeLogs(logFilter, logPage - 1)}
                  disabled={logPage <= 1 || logsLoading}
                >
                  ←
                </button>
                {Array.from({ length: logTotalPages }, (_, i) => i + 1)
                  .filter(p => p === 1 || p === logTotalPages || Math.abs(p - logPage) <= 1)
                  .reduce<(number | string)[]>((acc, p, idx, arr) => {
                    if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('...')
                    acc.push(p)
                    return acc
                  }, [])
                  .map((p, i) =>
                    typeof p === 'string' ? (
                      <span key={`dot-${i}`} className={styles.pageDots}>…</span>
                    ) : (
                      <button
                        key={p}
                        className={`${styles.pageBtn} ${p === logPage ? styles.pageActive : ''}`}
                        onClick={() => loadChangeLogs(logFilter, p)}
                        disabled={logsLoading}
                      >
                        {p}
                      </button>
                    )
                  )}
                <button
                  className={styles.pageBtn}
                  onClick={() => loadChangeLogs(logFilter, logPage + 1)}
                  disabled={logPage >= logTotalPages || logsLoading}
                >
                  →
                </button>
                <span className={styles.pageInfo}>
                  {logTotal} bản ghi
                </span>
              </div>
            )}
          </>
        )}
      </div>
      )}

      {/* ── Tab 2: Thống kê sử dụng ──────────────────────── */}
      {activeTab === 'stats' && (
      <div className={styles.usageSection}>
        <div className={styles.sectionHeader}>
          <h3 className={styles.sectionTitle}>
            <BarChart3 size={18} />
            Thống kê sử dụng
          </h3>
          <div className={styles.usageControls}>
            <div className={styles.filterDropdown}>
              <Filter size={14} />
              <select
                value={usageFilter}
                onChange={(e) => handleUsageFilterChange(e.target.value)}
                className={styles.filterSelect}
              >
                <option value="">Tất cả</option>
                {configs.map(c => (
                  <option key={c.config_key} value={c.config_key}>{c.display_name}</option>
                ))}
              </select>
            </div>
            <div className={styles.periodSelector}>
              {[7, 30, 90].map(d => (
                <button
                  key={d}
                  className={`${styles.periodBtn} ${usagePeriod === d ? styles.activePeriod : ''}`}
                  onClick={() => handlePeriodChange(d)}
                >
                  {d} ngày
                </button>
              ))}
            </div>
          </div>
        </div>

        {usageStats ? (
          <>
            <div className={styles.usageOverview}>
              <div className={styles.usageStat}>
                <div className={styles.usageStatValue}>{usageStats.total_requests.toLocaleString()}</div>
                <div className={styles.usageStatLabel}>Tổng requests</div>
              </div>
              <div className={styles.usageStat}>
                <div className={styles.usageStatValue}>{usageStats.total_tokens.toLocaleString()}</div>
                <div className={styles.usageStatLabel}>Tổng tokens</div>
              </div>
              <div className={styles.usageStat}>
                <div className={styles.usageStatValue}>{usageStats.avg_response_time_ms}ms</div>
                <div className={styles.usageStatLabel}>Avg response time</div>
              </div>
              <div className={styles.usageStat}>
                <div className={styles.usageStatValue}>{usageStats.success_rate}%</div>
                <div className={styles.usageStatLabel}>Tỷ lệ thành công</div>
              </div>
              <div className={`${styles.usageStat} ${styles.costStat}`}>
                <div className={styles.usageStatValue}>
                  <DollarSign size={16} />
                  {usageStats.estimated_cost < 0.01
                    ? usageStats.estimated_cost.toFixed(6)
                    : usageStats.estimated_cost.toFixed(4)}
                </div>
                <div className={styles.usageStatLabel}>Ước tính chi phí (USD)</div>
              </div>
            </div>

            {/* Budget Progress */}
            {usageStats.budget && (
              <div className={styles.budgetSection}>
                <div className={styles.budgetHeader}>
                  <div>
                    <span className={styles.budgetTitle}>Budget tháng này</span>
                    <span className={styles.budgetCost}>
                      ${usageStats.budget.monthly_estimated_cost < 0.01
                        ? usageStats.budget.monthly_estimated_cost.toFixed(6)
                        : usageStats.budget.monthly_estimated_cost.toFixed(4)}
                      {usageStats.budget.monthly_budget_usd > 0 && (
                        <> / ${usageStats.budget.monthly_budget_usd.toFixed(2)}</>
                      )}
                    </span>
                  </div>
                  <button className={styles.budgetSettingsBtn} onClick={openBudgetModal}>
                    <Settings size={14} />
                    Cài đặt
                  </button>
                </div>
                {usageStats.budget.monthly_budget_usd > 0 && (
                  <div className={styles.budgetBarWrap}>
                    <div
                      className={`${styles.budgetBar} ${
                        usageStats.budget.budget_usage_percent > 80 ? styles.budgetWarning : ''
                      } ${
                        usageStats.budget.budget_usage_percent > 100 ? styles.budgetDanger : ''
                      }`}
                      style={{ width: `${Math.min(usageStats.budget.budget_usage_percent, 100)}%` }}
                    ></div>
                  </div>
                )}
                <div className={styles.budgetMeta}>
                  <span>{usageStats.budget.monthly_total_tokens.toLocaleString()} tokens tháng này</span>
                  {usageStats.budget.monthly_budget_usd > 0 && (
                    <span className={
                      usageStats.budget.budget_usage_percent > 80
                        ? styles.budgetPctWarning
                        : styles.budgetPctNormal
                    }>
                      {usageStats.budget.budget_usage_percent}% đã sử dụng
                    </span>
                  )}
                </div>
              </div>
            )}

            {usageStats.per_config.length > 0 && (
              <table className={styles.usageTable}>
                <thead>
                  <tr>
                    <th>Cấu hình</th>
                    <th>Requests</th>
                    <th>Tokens</th>
                    <th>Avg Time</th>
                    <th>Thành công</th>
                  </tr>
                </thead>
                <tbody>
                  {usageStats.per_config.map(s => {
                    const successPct = s.total_requests > 0
                      ? Math.round((s.success_count / s.total_requests) * 100)
                      : 100
                    return (
                      <tr key={s.config_key}>
                        <td>{s.display_name}</td>
                        <td>{s.total_requests.toLocaleString()}</td>
                        <td>{s.total_tokens.toLocaleString()}</td>
                        <td>{s.avg_response_time_ms}ms</td>
                        <td>
                          <span className={styles.successBadge}>{successPct}%</span>
                          <div className={styles.progressBarWrap}>
                            <div
                              className={styles.progressBar}
                              style={{ width: `${successPct}%` }}
                            ></div>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            )}
          </>
        ) : (
          <div className={styles.auditEmpty}>
            Chưa có dữ liệu thống kê
          </div>
        )}
      </div>
      )}

      {/* ── Switch Model Modal ───────────────────────────── */}
      {switchModalOpen && switchTarget && (
        <div className={styles.modalOverlay} onClick={closeSwitchModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Đổi Model LLM</h2>
                <p className={styles.modalSubtitle}>
                  {switchTarget.display_name} ({switchTarget.config_key})
                </p>
              </div>
              <button className={styles.modalClose} onClick={closeSwitchModal}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              <div className={styles.warningBox}>
                <AlertTriangle size={16} />
                <span>
                  Khi đổi model, hệ thống sẽ tự động vào chế độ bảo trì trong vài giây.
                  Các request LLM trong lúc đổi model sẽ được trả lỗi thân thiện.
                </span>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Chọn model mới</label>
                <div className={styles.modelOptions}>
                  {availableModels.map((model) => {
                    const isCurrent = model.id === switchTarget.model_name
                    const isSelected = model.id === selectedModel
                    const tierInfo = getModelTier(model.id)

                    return (
                      <div
                        key={model.id}
                        className={`${styles.modelOption} ${isSelected ? styles.selected : ''} ${isCurrent ? styles.currentModel : ''}`}
                        onClick={() => !isCurrent && setSelectedModel(model.id)}
                      >
                        <div className={styles.modelOptionRadio}></div>
                        <div className={styles.modelOptionInfo}>
                          <p className={styles.modelOptionName}>{model.name}</p>
                          <p className={styles.modelOptionDesc}>{model.description}</p>
                        </div>
                        {isCurrent ? (
                          <span className={styles.currentBadge}>Hiện tại</span>
                        ) : (
                          <span className={`${styles.modelOptionBadge} ${getTierClass(tierInfo.tier)}`}>
                            {tierInfo.label}
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Lý do đổi model (không bắt buộc)</label>
                <textarea
                  className={styles.formTextarea}
                  placeholder="Ví dụ: Chuyển sang model nhẹ hơn để tiết kiệm chi phí..."
                  value={switchReason}
                  onChange={(e) => setSwitchReason(e.target.value)}
                  rows={2}
                />
              </div>
            </div>

            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={closeSwitchModal}>
                Hủy
              </button>
              <button
                className={styles.btnSubmit}
                onClick={handleSwitchModel}
                disabled={!selectedModel || switching}
              >
                {switching && <span className={styles.spinnerInline}></span>}
                {switching ? 'Đang đổi...' : 'Xác nhận đổi model'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Edit Params Modal (Phase 4) ─────────────────── */}
      {paramsModalOpen && paramsTarget && (
        <div className={styles.modalOverlay} onClick={closeParamsModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Chỉnh tham số LLM</h2>
                <p className={styles.modalSubtitle}>
                  {paramsTarget.display_name} ({paramsTarget.config_key})
                </p>
              </div>
              <button className={styles.modalClose} onClick={closeParamsModal}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              {/* Temperature — slider */}
              <div className={styles.paramEditRow}>
                <div className={styles.paramEditHeader}>
                  <span className={styles.paramEditLabel}>Temperature</span>
                  <span className={styles.paramEditValue}>{editTemperature.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  className={styles.paramSlider}
                  min={0}
                  max={2}
                  step={0.05}
                  value={editTemperature}
                  onChange={(e) => setEditTemperature(parseFloat(e.target.value))}
                />
                <p className={styles.paramHint}>
                  0.0 = chính xác nhất • 0.3-0.7 = cân bằng • 1.0+ = sáng tạo
                </p>
              </div>

              {/* Max Tokens — number input */}
              <div className={styles.paramEditRow}>
                <div className={styles.paramEditHeader}>
                  <span className={styles.paramEditLabel}>Max Tokens</span>
                  <span className={styles.paramEditValue}>{editMaxTokens.toLocaleString()}</span>
                </div>
                <input
                  type="number"
                  className={styles.paramNumberInput}
                  min={100}
                  max={16000}
                  step={100}
                  value={editMaxTokens}
                  onChange={(e) => setEditMaxTokens(Math.max(100, Math.min(16000, parseInt(e.target.value) || 100)))}
                />
                <p className={styles.paramHint}>
                  100 - 16,000 tokens • 1 token ≈ 4 ký tự tiếng Anh
                </p>
              </div>

              {/* Top K — number input */}
              <div className={styles.paramEditRow}>
                <div className={styles.paramEditHeader}>
                  <span className={styles.paramEditLabel}>Top K (RAG)</span>
                  <span className={styles.paramEditValue}>{editTopK}</span>
                </div>
                <input
                  type="number"
                  className={styles.paramNumberInput}
                  min={1}
                  max={20}
                  step={1}
                  value={editTopK}
                  onChange={(e) => setEditTopK(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                />
                <p className={styles.paramHint}>
                  Số kết quả RAG retrieval (1 - 20) • Giá trị cao hơn = nhiều ngữ cảnh hơn
                </p>
              </div>

              {/* Reason */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Lý do thay đổi (không bắt buộc)</label>
                <textarea
                  className={styles.formTextarea}
                  placeholder="Ví dụ: Giảm temperature để tăng độ chính xác..."
                  value={paramsReason}
                  onChange={(e) => setParamsReason(e.target.value)}
                  rows={2}
                />
              </div>
            </div>

            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={closeParamsModal}>
                Hủy
              </button>
              <button
                className={styles.btnSubmit}
                onClick={handleUpdateParams}
                disabled={savingParams}
              >
                {savingParams && <span className={styles.spinnerInline}></span>}
                {savingParams ? 'Đang lưu...' : 'Lưu tham số'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Test Prompt Modal (Phase 5) ─────────────────── */}
      {testModalOpen && testTarget && (
        <div className={styles.modalOverlay} onClick={closeTestModal}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Test thử Model</h2>
                <p className={styles.modalSubtitle}>
                  {testTarget.display_name} — {testTarget.model_name}
                </p>
              </div>
              <button className={styles.modalClose} onClick={closeTestModal}>
                <X size={20} />
              </button>
            </div>

            <div className={styles.modalBody}>
              {/* Model override */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Model (mặc định: {testTarget.model_name})</label>
                <select
                  className={styles.formSelect}
                  value={testModelOverride}
                  onChange={(e) => setTestModelOverride(e.target.value)}
                >
                  <option value="">Dùng model hiện tại ({testTarget.model_name})</option>
                  {availableModels
                    .filter(m => m.id !== testTarget.model_name)
                    .map(m => (
                      <option key={m.id} value={m.id}>{m.name} — {m.description}</option>
                    ))}
                </select>
              </div>

              {/* Prompt */}
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Prompt test</label>
                <textarea
                  className={styles.formTextarea}
                  placeholder="Ví dụ: Vết trầy xước nhẹ ở tay, cần sơ cứu thế nào?"
                  value={testPrompt}
                  onChange={(e) => setTestPrompt(e.target.value)}
                  rows={3}
                />
              </div>

              {/* Response area */}
              {testing && (
                <div className={styles.testLoading}>
                  <div className={styles.typingDots}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  Đang gửi prompt đến {testModelOverride || testTarget.model_name}...
                </div>
              )}

              {testResult && (
                <div className={styles.testResponseBox}>
                  <div className={styles.testResponseHeader}>
                    <span className={styles.testResponseLabel}>Phản hồi từ {testResult.model_used}</span>
                    <div className={styles.testResponseStats}>
                      <span className={`${styles.testStat} ${styles.success}`}>
                        {testResult.tokens_used} tokens
                      </span>
                      <span className={styles.testStat}>
                        {testResult.response_time_ms}ms
                      </span>
                    </div>
                  </div>
                  <div className={styles.testResponseText}>
                    {testResult.response}
                  </div>
                </div>
              )}
            </div>

            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={closeTestModal}>
                Đóng
              </button>
              <button
                className={styles.btnSubmit}
                onClick={handleTestPrompt}
                disabled={testing || !testPrompt.trim()}
              >
                {testing && <span className={styles.spinnerInline}></span>}
                {testing ? 'Đang test...' : 'Gửi test'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Budget Settings Modal ─────────────────────────── */}
      {budgetModalOpen && (
        <div className={styles.modalOverlay} onClick={() => setBudgetModalOpen(false)}>
          <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div>
                <h2>Cài đặt Budget & Giá token</h2>
                <p className={styles.modalSubtitle}>Thiết lập ngân sách hàng tháng và giá token</p>
              </div>
              <button className={styles.modalClose} onClick={() => setBudgetModalOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Budget hàng tháng (USD)</label>
                <input
                  type="number"
                  className={styles.paramNumberInput}
                  min={0}
                  step={1}
                  value={editBudget}
                  onChange={(e) => setEditBudget(Math.max(0, parseFloat(e.target.value) || 0))}
                />
                <p className={styles.paramHint}>
                  0 = không giới hạn. Hệ thống sẽ cảnh báo khi vượt 80% budget.
                </p>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Giá / 1K input tokens (USD)</label>
                <input
                  type="number"
                  className={styles.paramNumberInput}
                  min={0}
                  step={0.01}
                  value={editInputPrice}
                  onChange={(e) => setEditInputPrice(Math.max(0, parseFloat(e.target.value) || 0))}
                />
                <p className={styles.paramHint}>
                  GPT-4.1-mini: $0.40 • GPT-4.1-nano: $0.10 • GPT-4.1: $2.00
                </p>
              </div>
              <div className={styles.formGroup}>
                <label className={styles.formLabel}>Giá / 1K output tokens (USD)</label>
                <input
                  type="number"
                  className={styles.paramNumberInput}
                  min={0}
                  step={0.01}
                  value={editOutputPrice}
                  onChange={(e) => setEditOutputPrice(Math.max(0, parseFloat(e.target.value) || 0))}
                />
                <p className={styles.paramHint}>
                  GPT-4.1-mini: $1.60 • GPT-4.1-nano: $0.40 • GPT-4.1: $8.00
                </p>
              </div>
            </div>
            <div className={styles.modalFooter}>
              <button className={styles.btnCancel} onClick={() => setBudgetModalOpen(false)}>
                Hủy
              </button>
              <button
                className={styles.btnPrimary}
                onClick={handleSaveBudget}
                disabled={savingBudget}
              >
                {savingBudget && <span className={styles.spinnerInline}></span>}
                {savingBudget ? 'Đang lưu...' : 'Lưu cài đặt'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
