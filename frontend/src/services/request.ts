/**
 * Axios 请求封装
 */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// 创建 Axios 实例
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://192.168.72.195:8000',
  timeout: 60000, // AI 分析可能较慢，设置 60 秒超时
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加 Token
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response.data
  },
  (error) => {
    // 统一错误处理
    const errorMessage = error.response?.data?.detail || error.message || '请求失败'
    message.error(errorMessage)
    console.error('Response error:', error)
    return Promise.reject(error)
  }
)

export default request

