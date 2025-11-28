/**
 * 仪表盘页面
 * 展示系统概览和快捷入口
 */
import React from 'react'
import { Card, Row, Col, Statistic, Typography, Space, Button } from 'antd'
import { FileTextOutlined, BulbOutlined, CheckCircleOutlined, ClockCircleOutlined, BarChartOutlined, BugOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { decisionApi, statisticsApi } from '@/services/api'

const { Title, Paragraph } = Typography

const Dashboard: React.FC = () => {
  const navigate = useNavigate()

  // 获取统计数据
  const { data: statistics } = useQuery({
    queryKey: ['statistics'],
    queryFn: statisticsApi.getStatistics
  })

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>📊 仪表盘</Title>
      <Paragraph type="secondary">
        欢迎使用 QA-Brain - 您的智能质量助手
      </Paragraph>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} sm={12} lg={5}>
          <Card bordered={false}>
            <Statistic
              title="总决策数"
              value={statistics?.total_decisions || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <Card bordered={false}>
            <Statistic
              title="活跃决策"
              value={statistics?.active_decisions || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <Card bordered={false}>
            <Statistic
              title="已废弃"
              value={statistics?.deprecated_decisions || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={5}>
          <Card bordered={false}>
            <Statistic
              title="AI 分析次数"
              value={statistics?.total_analyses || 0}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={4}>
          <Card bordered={false}>
            <Statistic
              title="总缺陷数"
              // 使用后端 StatisticsResponse 新增的 total_bugs 字段
              value={statistics?.total_bugs || 0}
              prefix={<BugOutlined />}
              // 建议使用紫色或洋红色，与 Bug 的警示感相符，且区别于红色的“废弃”
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 数据可视化入口 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24}>
          <Card
            title="📊 数据可视化"
            bordered={false}
            extra={
              <Button
                type="primary"
                icon={<BarChartOutlined />}
                onClick={() => navigate('/visualization')}
              >
                查看详细图表
              </Button>
            }
          >
            <Paragraph>
              查看决策和分析的趋势图表、分布统计等可视化数据。
            </Paragraph>
            <Paragraph>
              <strong>包含内容：</strong>
            </Paragraph>
            <ul>
              <li>30天趋势分析</li>
              <li>决策人分布统计</li>
              <li>Bug 严重程度分布</li>
              <li>最近7天决策分布</li>
            </ul>
          </Card>
        </Col>
      </Row>

      {/* 功能介绍 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="📝 决策回溯" bordered={false}>
            <Paragraph>
              记录和查询历史决策，支持按状态和关键词搜索。
            </Paragraph>
            <Paragraph>
              <strong>核心功能：</strong>
            </Paragraph>
            <ul>
              <li>快速记录决策背景和结论</li>
              <li>支持附件上传</li>
              <li>决策状态管理 (Active/Deprecated)</li>
              <li>决策编辑和版本历史追溯</li>
            </ul>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="🧠 智能分析" bordered={false}>
            <Paragraph>
              基于 RAG 技术的 Bug 智能分析助手。
            </Paragraph>
            <Paragraph>
              <strong>核心功能：</strong>
            </Paragraph>
            <ul>
              <li>自动检索相关历史决策</li>
              <li>AI 生成专业分析报告</li>
              <li>严重程度自动判定</li>
            </ul>
          </Card>
        </Col>
      </Row>

      {/* 快速开始 */}
      <Card title="🚀 快速开始" bordered={false} style={{ marginTop: 24 }}>
        <Space direction="vertical" size="middle">
          <Paragraph>
            <strong>1. 记录决策：</strong> 前往"决策回溯"页面，点击"新建决策"按钮
          </Paragraph>
          <Paragraph>
            <strong>2. 智能分析：</strong> 前往"智能分析"页面，输入 Bug 描述并点击"开始分析"
          </Paragraph>
          <Paragraph>
            <strong>3. 查看历史：</strong> 在"决策回溯"页面使用搜索功能快速定位历史记录
          </Paragraph>
        </Space>
      </Card>
    </div>
  )
}

export default Dashboard

