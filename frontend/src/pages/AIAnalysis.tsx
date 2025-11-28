/**
 * 智能分析页面
 * 左侧输入框 + 历史记录，右侧分析结果展示
 */
import React, { useState, useEffect } from 'react'
import { Card, Input, Button, List, Typography, Tag, Spin, Empty, Space, Steps } from 'antd'
import { SendOutlined, BulbOutlined, HistoryOutlined, SearchOutlined, CheckCircleOutlined, RobotOutlined } from '@ant-design/icons'
import { useMutation } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github-dark.css'
import { analysisApi } from '@/services/api'
import type { BugAnalysisResponse, BugSeverity } from '@/types'

const { TextArea } = Input
const { Title, Paragraph, Text } = Typography

interface AnalysisHistory {
  id: string
  query: string
  result: BugAnalysisResponse
  timestamp: string
}

// LocalStorage 键名
const HISTORY_STORAGE_KEY = 'qa_brain_analysis_history'
const MAX_HISTORY_COUNT = 5

// 从 localStorage 加载历史记录
const loadHistoryFromStorage = (): AnalysisHistory[] => {
  try {
    const stored = localStorage.getItem(HISTORY_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Failed to load history from localStorage:', error)
  }
  return []
}

// 保存历史记录到 localStorage
const saveHistoryToStorage = (history: AnalysisHistory[]) => {
  try {
    localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
  } catch (error) {
    console.error('Failed to save history to localStorage:', error)
  }
}

const AIAnalysis: React.FC = () => {
  const [query, setQuery] = useState('')
  const [history, setHistory] = useState<AnalysisHistory[]>([])
  const [currentResult, setCurrentResult] = useState<BugAnalysisResponse | null>(null)
  const [currentStep, setCurrentStep] = useState(0) // 当前执行步骤

  // 组件挂载时加载历史记录
  useEffect(() => {
    const loadedHistory = loadHistoryFromStorage()
    setHistory(loadedHistory)
  }, [])

  // 分析 Mutation
  const analyzeMutation = useMutation({
    mutationFn: async (data: { query: string }) => {
      // 步骤 1: 检索
      setCurrentStep(1)
      await new Promise(resolve => setTimeout(resolve, 500)) // 模拟延迟，让用户看到进度

      // 步骤 2: 评估
      setCurrentStep(2)
      await new Promise(resolve => setTimeout(resolve, 500))

      // 步骤 3: 生成
      setCurrentStep(3)
      const result = await analysisApi.analyzeBug(data)

      return result
    },
    onSuccess: (data) => {
      setCurrentResult(data)
      setCurrentStep(4) // 完成

      // 添加到历史记录
      const newHistory: AnalysisHistory = {
        id: Date.now().toString(),
        query,
        result: data,
        timestamp: new Date().toISOString()
      }

      // 更新历史记录（保留最近 5 条）
      const updatedHistory = [newHistory, ...history].slice(0, MAX_HISTORY_COUNT)
      setHistory(updatedHistory)

      // 保存到 localStorage
      saveHistoryToStorage(updatedHistory)
    },
    onError: () => {
      setCurrentStep(0) // 重置步骤
    }
  })

  const handleAnalyze = () => {
    if (!query.trim()) {
      return
    }
    setCurrentStep(0) // 重置步骤
    analyzeMutation.mutate({ query })
  }

  const handleHistoryClick = (item: AnalysisHistory) => {
    setQuery(item.query)
    setCurrentResult(item.result)
  }

  // 严重程度颜色映射
  const getSeverityColor = (severity?: BugSeverity): string => {
    const colorMap: Record<string, string> = {
      Blocker: 'red',
      Critical: 'volcano',
      Major: 'orange',
      Minor: 'gold',
      Trivial: 'green'
    }
    return colorMap[severity || 'Major'] || 'default'
  }

  return (
    <div style={{ padding: 24, display: 'flex', gap: 24, height: 'calc(100vh - 112px)' }}>
      {/* 左侧：输入区 + 历史记录 */}
      <div style={{ width: '320px', minWidth: '320px', display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
        {/* 输入区 */}
        <Card
          title={
            <Space>
              <BulbOutlined />
              <span>Bug 描述</span>
            </Space>
          }
          bordered={false}
          style={{ flexShrink: 0 }}
        >
          <TextArea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="请输入 Bug 描述或报错日志...&#10;&#10;示例：&#10;- 用户登录时出现 500 错误&#10;- 数据库连接超时&#10;- 前端页面白屏"
            rows={6}
            style={{ marginBottom: 16 }}
          />
          <Button
            type="primary"
            icon={<SendOutlined />}
            onClick={handleAnalyze}
            loading={analyzeMutation.isPending}
            block
            size="large"
          >
            {analyzeMutation.isPending ? 'QA-Brain 正在检索知识库...' : '开始分析'}
          </Button>
        </Card>

        {/* 历史记录 */}
        <Card
          title={
            <Space>
              <HistoryOutlined />
              <span>分析历史</span>
              {history.length > 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  ({history.length}/5)
                </Text>
              )}
            </Space>
          }
          bordered={false}
          style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
          bodyStyle={{ flex: 1, overflow: 'auto', padding: history.length === 0 ? '24px' : '12px' }}
        >
          {history.length === 0 ? (
            <Empty description="暂无历史记录" />
          ) : (
            <List
              dataSource={history}
              renderItem={(item) => (
                <List.Item
                  style={{ cursor: 'pointer', padding: '12px' }}
                  onClick={() => handleHistoryClick(item)}
                >
                  <List.Item.Meta
                    title={
                      <Text ellipsis style={{ width: '100%' }}>
                        {item.query}
                      </Text>
                    }
                    description={
                      <Space>
                        <Tag color={getSeverityColor(item.result.severity)}>
                          {item.result.severity || 'Major'}
                        </Tag>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {new Date(item.timestamp).toLocaleString()}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          )}
        </Card>
      </div>

      {/* 右侧：分析结果 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <Card
          title="分析结果"
          bordered={false}
          style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}
          bodyStyle={{ flex: 1, overflow: 'auto' }}
        >
          {analyzeMutation.isPending ? (
            <div style={{ padding: '40px 20px' }}>
              {/* 进度步骤 */}
              <Steps
                current={currentStep}
                direction="vertical"
                items={[
                  {
                    title: '检索相关决策',
                    description: '从知识库中搜索相似的历史决策...',
                    icon: currentStep === 1 ? <Spin size="small" /> : <SearchOutlined />,
                    status: currentStep > 1 ? 'finish' : currentStep === 1 ? 'process' : 'wait'
                  },
                  {
                    title: '评估相关性',
                    description: '分析检索结果的相关性和可信度...',
                    icon: currentStep === 2 ? <Spin size="small" /> : <CheckCircleOutlined />,
                    status: currentStep > 2 ? 'finish' : currentStep === 2 ? 'process' : 'wait'
                  },
                  {
                    title: '生成分析报告',
                    description: '调用 AI 模型生成专业的 Bug 分析...',
                    icon: currentStep === 3 ? <Spin size="small" /> : <RobotOutlined />,
                    status: currentStep > 3 ? 'finish' : currentStep === 3 ? 'process' : 'wait'
                  }
                ]}
              />
              <div style={{ textAlign: 'center', marginTop: 32 }}>
                <Spin size="large" />
                <Paragraph style={{ marginTop: 16, color: '#1890ff' }}>
                  QA-Brain 正在分析中，请稍候...
                </Paragraph>
              </div>
            </div>
          ) : currentResult ? (
            <div>
              {/* 严重程度标签 */}
              {currentResult.severity && (
                <div style={{ marginBottom: 16 }}>
                  <Tag color={getSeverityColor(currentResult.severity)} style={{ fontSize: 14, padding: '4px 12px' }}>
                    严重程度: {currentResult.severity}
                  </Tag>
                </div>
              )}

              {/* Markdown 渲染 */}
              <div className="markdown-body" style={{ fontSize: 15, lineHeight: 1.8 }}>
                <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                  {currentResult.answer}
                </ReactMarkdown>
              </div>

              {/* 引用来源 */}
              {currentResult.sources && currentResult.sources.length > 0 && (
                <div style={{ marginTop: 24, padding: 16, backgroundColor: '#f5f5f5', borderRadius: 8 }}>
                  <Text strong>📚 参考决策 ID: </Text>
                  {currentResult.sources.map((source) => (
                    <Tag key={source} color="blue" style={{ marginLeft: 8 }}>
                      #{source}
                    </Tag>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <Empty
              description='请在左侧输入 Bug 描述并点击"开始分析"'
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Card>
      </div>
    </div>
  )
}

export default AIAnalysis

