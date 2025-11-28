/**
 * 知识库概览组件
 * 展示知识库统计数据和图表
 */
import React from 'react'
import { Card, Row, Col, Statistic, Spin, Empty } from 'antd'
import { DatabaseOutlined, FileTextOutlined, BugOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { Pie } from '@ant-design/plots'
import { knowledgeApi } from '@/services/knowledgeApi'

const KnowledgeOverview: React.FC = () => {
  // 获取统计数据
  const { data: stats, isLoading } = useQuery({
    queryKey: ['knowledgeStats'],
    queryFn: knowledgeApi.getStats
  })

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: 60 }}>
        <Spin size="large" tip="加载统计数据..." />
      </div>
    )
  }

  if (!stats) {
    return <Empty description="暂无统计数据" />
  }

  // 安全获取数组数据，避免 undefined 报错
  const severityData = stats.bugs_by_severity || []
  const categoryData = stats.bugs_by_category || []
  const versionData = stats.bugs_by_version || []

  // 严重程度分布配置
  const severityConfig = {
    data: severityData,
    angleField: 'value',
    colorField: 'name',
    radius: 0.8,
    label: false, // 禁用标签，避免表达式解析错误
    legend: {
      position: 'bottom' as const
    },
    statistic: {
      title: false,
      content: {
        style: {
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        },
        content: '',
      },
    },
    interactions: [{ type: 'element-active' }],
    color: ({ name }: any) => {
      const colorMap: Record<string, string> = {
        // 中文名称映射
        '致命': '#ff4d4f',
        '严重': '#fa8c16',
        '一般': '#1890ff',
        '建议': '#52c41a',
        // 英文名称映射（兼容）
        'Critical': '#ff4d4f',
        'Major': '#fa8c16',
        'Minor': '#1890ff',
        'Trivial': '#52c41a',
        '未知': '#d9d9d9'
      }
      return colorMap[name] || '#d9d9d9'
    }
  }

  // 分类分布配置
  const categoryConfig = {
    data: categoryData,
    angleField: 'value',
    colorField: 'name',
    radius: 0.8,
    label: false, // 禁用标签
    legend: {
      position: 'bottom' as const
    },
    statistic: {
      title: false,
      content: {
        style: {
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        },
        content: '',
      },
    },
    interactions: [{ type: 'element-active' }]
  }

  // 版本分布配置
  const versionConfig = {
    data: versionData.slice(0, 10), // 只显示前 10 个版本
    angleField: 'value',
    colorField: 'name',
    radius: 0.8,
    label: false, // 禁用标签
    legend: {
      position: 'bottom' as const
    },
    statistic: {
      title: false,
      content: {
        style: {
          whiteSpace: 'pre-wrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        },
        content: '',
      },
    },
    interactions: [{ type: 'element-active' }]
  }

  return (
    <div>
      {/* 统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="历史缺陷总数"
              value={stats.total_bugs}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="已索引决策数"
              value={stats.total_decisions}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="知识库总量"
              value={stats.total_bugs + stats.total_decisions}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="系统智商指数"
              value={Math.min(100, Math.floor((stats.total_bugs + stats.total_decisions) / 10))}
              suffix="/ 100"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表 */}
      <Row gutter={[16, 16]}>
        {/* 严重程度分布 */}
        <Col xs={24} lg={8}>
          <Card title="缺陷严重程度分布" bordered={false}>
            {severityData.length > 0 ? (
              <div style={{ height: 300 }}>
                <Pie {...severityConfig} />
              </div>
            ) : (
              <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>

        {/* 分类分布 */}
        <Col xs={24} lg={8}>
          <Card title="缺陷分类分布" bordered={false}>
            {categoryData.length > 0 ? (
              <div style={{ height: 300 }}>
                <Pie {...categoryConfig} />
              </div>
            ) : (
              <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>

        {/* 版本分布 */}
        <Col xs={24} lg={8}>
          <Card title="各版本缺陷数量分布 (Top 10)" bordered={false}>
            {versionData.length > 0 ? (
              <div style={{ height: 300 }}>
                <Pie {...versionConfig} />
              </div>
            ) : (
              <Empty description="暂无数据" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>

      {/* 知识库说明 */}
      <Card
        title="💡 知识库说明"
        bordered={false}
        style={{ marginTop: 16 }}
      >
        <div style={{ lineHeight: 2 }}>
          <p>
            <strong>系统智商指数</strong>：根据知识库中的决策和缺陷数量计算，反映系统的知识积累程度。
          </p>
          <p>
            <strong>历史缺陷</strong>：从 Excel 导入或手动录入的历史 Bug 记录，包含根因和解决方案等关键知识。
          </p>
          <p>
            <strong>已索引决策</strong>：在"决策回溯"模块中创建的决策记录，已自动同步到向量数据库。
          </p>
          <p>
            <strong>智能分析</strong>：当您在"智能分析"页面提问时，系统会同时检索决策和缺陷库，提供更全面的分析。
          </p>
        </div>
      </Card>
    </div>
  )
}

export default KnowledgeOverview

