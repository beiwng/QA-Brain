/**
 * 知识库 API 服务
 */
import axios from 'axios'

const API_BASE_URL = 'http://192.168.72.195:8000'

export interface BugRecord {
  id: number
  summary: string
  description?: string
  root_cause?: string
  solution?: string
  impact_scope?: string
  reporter?: string
  assignee?: string
  severity?: string
  category?: string
  affected_version?: string
  status?: string
  created_at: string
  updated_at: string
}

export interface BugRecordCreate {
  summary: string
  description?: string
  root_cause?: string
  solution?: string
  impact_scope?: string
  reporter?: string
  assignee?: string
  severity?: string
  category?: string
  affected_version?: string
  status?: string
  created_at?: string
}

export interface ExcelUploadResponse {
  success: boolean
  imported_count: number
  failed_count: number
  message: string
  errors: string[]
}

export interface KnowledgeStats {
  total_bugs: number
  total_decisions: number
  bugs_by_severity: Array<{ name: string; value: number }>
  bugs_by_category: Array<{ name: string; value: number }>
  bugs_by_version: Array<{ name: string; value: number }>
}

export const knowledgeApi = {
  // 下载 Excel 模板
  downloadTemplate: () => {
    window.open(`${API_BASE_URL}/api/knowledge/template/download`, '_blank')
  },

  // 上传 Excel
  uploadExcel: async (file: File): Promise<ExcelUploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await axios.post(
      `${API_BASE_URL}/api/knowledge/upload/excel`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  // 创建缺陷记录
  createBugRecord: async (data: BugRecordCreate): Promise<BugRecord> => {
    const response = await axios.post(`${API_BASE_URL}/api/knowledge/bug`, data)
    return response.data
  },

  // 获取缺陷列表
  getBugRecords: async (params?: {
    severity?: string
    category?: string
    version?: string
    keyword?: string
    skip?: number
    limit?: number
  }): Promise<BugRecord[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/knowledge/bugs`, { params })
    return response.data
  },

  // 获取知识库统计
  getStats: async (): Promise<KnowledgeStats> => {
    const response = await axios.get(`${API_BASE_URL}/api/knowledge/stats`)
    return response.data
  }
}

