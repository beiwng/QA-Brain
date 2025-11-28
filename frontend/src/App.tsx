/**
 * 主应用组件
 * 配置路由和 React Query
 */
import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import DecisionLog from '@/pages/DecisionLog'
import AIAnalysis from '@/pages/AIAnalysis'
import DataVisualization from '@/pages/DataVisualization'
import KnowledgeBase from '@/pages/KnowledgeBase'

// 创建 QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000 // 5 分钟
    }
  }
})

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="decisions" element={<DecisionLog />} />
              <Route path="analysis" element={<AIAnalysis />} />
              <Route path="visualization" element={<DataVisualization />} />
              <Route path="knowledge" element={<KnowledgeBase />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  )
}

export default App

