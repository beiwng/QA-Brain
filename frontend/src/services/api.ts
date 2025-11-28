/**
 * API 接口定义
 */
import request from './request'
import type {
  Decision,
  DecisionCreate,
  DecisionUpdate,
  DecisionVersion,
  BugAnalysisRequest,
  BugAnalysisResponse,
  UploadResponse,
  DecisionStatus,
  StatisticsResponse,
  TrendDataResponse
} from '@/types'

// === Decision APIs ===
export const decisionApi = {
  /**
   * 获取决策列表
   */
  getDecisions: (params?: { status?: DecisionStatus; keyword?: string }) => {
    return request.get<Decision[]>('/api/decisions', { params })
  },

  /**
   * 创建决策
   */
  createDecision: (data: DecisionCreate) => {
    return request.post<Decision>('/api/decisions', data)
  },

  /**
   * 更新决策
   */
  updateDecision: (id: number, data: DecisionUpdate) => {
    return request.put<Decision>(`/api/decisions/${id}`, data)
  },

  /**
   * 获取决策版本历史
   */
  getDecisionVersions: (id: number) => {
    return request.get<DecisionVersion[]>(`/api/decisions/${id}/versions`)
  }
}

// === AI Analysis API ===
export const analysisApi = {
  /**
   * 分析 Bug
   */
  analyzeBug: (data: BugAnalysisRequest) => {
    return request.post<BugAnalysisResponse>('/api/analyze', data)
  }
}

// === Upload API ===
export const uploadApi = {
  /**
   * 上传文件
   */
  uploadFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// === Statistics APIs ===
export const statisticsApi = {
  /**
   * 获取统计数据
   */
  getStatistics: () => {
    return request.get<StatisticsResponse>('/api/statistics')
  },

  /**
   * 获取趋势数据
   */
  getTrends: (days: number = 30) => {
    return request.get<TrendDataResponse>('/api/trends', { params: { days } })
  }
}

