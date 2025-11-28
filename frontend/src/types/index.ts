/**
 * QA-Brain 类型定义
 */

// === Enums ===
export enum DecisionStatus {
  ACTIVE = 'Active',
  DEPRECATED = 'Deprecated'
}

export enum BugSeverity {
  BLOCKER = 'Blocker',
  CRITICAL = 'Critical',
  MAJOR = 'Major',
  MINOR = 'Minor',
  TRIVIAL = 'Trivial'
}

// === Decision Types ===
export interface Decision {
  id: number
  title: string
  context: string
  verdict: string
  owner: string
  status: DecisionStatus
  attachment_url?: string
  created_at: string
  updated_at: string
}

export interface DecisionCreate {
  title: string
  context: string
  verdict: string
  owner: string
  status?: DecisionStatus
  attachment_url?: string
}

export interface DecisionUpdate {
  title?: string
  context?: string
  verdict?: string
  owner?: string
  status?: DecisionStatus
  attachment_url?: string
  change_reason?: string
  changed_by: string
}

export interface DecisionVersion {
  id: number
  decision_id: number
  version: number
  title: string
  context: string
  verdict: string
  owner: string
  status: DecisionStatus
  attachment_url?: string
  change_reason?: string
  changed_by: string
  created_at: string
}

// === Bug Analysis Types ===
export interface BugAnalysisRequest {
  query: string
}

export interface BugAnalysisResponse {
  answer: string
  sources: string[]
  severity?: BugSeverity
}

// === Upload Types ===
export interface UploadResponse {
  url: string
  filename: string
}

// === Statistics Types ===
export interface StatisticsResponse {
  total_decisions: number
  active_decisions: number
  deprecated_decisions: number
  total_analyses: number
  decisions_by_owner: Array<{ owner: string; count: number }>
  decisions_by_date: Array<{ date: string; count: number }>
  analyses_by_severity: Array<{ severity: string; count: number }>
  recent_decisions: Decision[]
}

export interface TrendDataResponse {
  dates: string[]
  decision_counts: number[]
  analysis_counts: number[]
}

// === API Response ===
export interface ApiResponse<T = any> {
  data?: T
  error?: string
  message?: string
}

