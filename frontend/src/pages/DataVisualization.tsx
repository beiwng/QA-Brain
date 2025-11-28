/**
 * 数据可视化页面
 * 展示决策和分析的统计图表
 */
import { Card, Row, Col, Statistic, Spin, Empty } from 'antd'
import { Line, Column, Pie } from '@ant-design/charts'
import { useQuery } from '@tanstack/react-query'
import { statisticsApi } from '@/services/api'
import {
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  BulbOutlined,
  BugOutlined // ✅ 新增图标
} from '@ant-design/icons'

const DataVisualization = () => {
  // 获取统计数据
  const { data: statistics, isLoading: statsLoading } = useQuery({
    queryKey: ['statistics'],
    queryFn: statisticsApi.getStatistics,
    refetchInterval: 30000 // 每30秒刷新一次
  })

  // 获取趋势数据
  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['trends'],
    queryFn: () => statisticsApi.getTrends(30),
    refetchInterval: 30000
  })

  if (statsLoading || trendsLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载数据中..." />
      </div>
    )
  }

  // 基础判空
  if (!statistics || !trends) {
    return <Empty description="暂无数据" />
  }

  // 🛡️ 修复 1: 趋势图数据 - 增加防御性判断 (?.) 和空数组兜底 (|| [])
  // 防止 trends.dates 为 undefined 导致白屏
  const trendData = (trends?.dates || []).map((date: string, index: number) => [
    {
      date,
      value: trends.decision_counts?.[index] || 0, // 防止索引越界
      type: '决策数量'
    },
    {
      date,
      value: trends.analysis_counts?.[index] || 0,
      type: '分析次数'
    }
  ]).flat()

  // 🛡️ 修复 2: 决策人分布数据
  const ownerData = (statistics?.decisions_by_owner || []).map((item: any) => ({
    owner: item.owner,
    count: item.count
  }))

  // 🛡️ 修复 3: 严重程度分布数据
  const severityData = (statistics?.analyses_by_severity || []).map((item: any) => ({
    severity: item.severity,
    count: item.count
  }))

  // 严重程度颜色映射
  const severityColors: Record<string, string> = {
    'Blocker': '#ff4d4f',
    'Critical': '#ff7a45',
    'Major': '#ffa940',
    'Minor': '#ffc53d',
    'Trivial': '#52c41a'
  }

  // 公共卡片样式 (flex布局用)
  const colProps = {
    flex: "1",
    style: { minWidth: '200px' }
  }

  return (
    <div style={{ padding: '24px', height: 'calc(100vh - 112px)', overflow: 'auto' }}>
      {/* 统计卡片 - 使用 Flex 布局实现 5 等分 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }} wrap={true}>
        <Col {...colProps}>
          <Card bordered={false} hoverable>
            <Statistic
              title="总决策数"
              value={statistics.total_decisions}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col {...colProps}>
          <Card bordered={false} hoverable>
            <Statistic
              title="活跃决策"
              value={statistics.active_decisions}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col {...colProps}>
          <Card bordered={false} hoverable>
            <Statistic
              title="已废弃决策"
              value={statistics.deprecated_decisions}
              prefix={<CloseCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col {...colProps}>
          <Card bordered={false} hoverable>
            <Statistic
              title="AI 分析次数"
              value={statistics.total_analyses}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        {/* ✅ 新增: 缺陷知识库统计 */}
        <Col {...colProps}>
          <Card bordered={false} hoverable>
            <Statistic
              title="缺陷知识库"
              value={statistics.total_bugs || 0}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 趋势图 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24}>
          <Card title="📈 30天趋势分析" bordered={false}>
            <div style={{ height: 300 }}>
              <Line
                data={trendData}
                xField="date"
                yField="value"
                seriesField="type"
                smooth={true}
                animation={{
                  appear: {
                    animation: 'path-in',
                    duration: 1000
                  }
                }}
                legend={{
                  position: 'top'
                }}
                tooltip={{
                  showMarkers: true
                }}
                point={{
                  size: 3,
                  shape: 'circle'
                }}
                autoFit={true}
              />
            </div>
          </Card>
        </Col>
      </Row>

      {/* 决策人分布 & 严重程度分布 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="👥 决策人分布 (Top 10)" bordered={false}>
            {ownerData.length > 0 ? (
              <div style={{ height: 350 }}>
                <Column
                  data={ownerData}
                  xField="owner"
                  yField="count"
                  label={{
                    position: 'top',
                    style: {
                      fill: '#000',
                      opacity: 0.6
                    }
                  }}
                  xAxis={{
                    label: {
                      autoRotate: true,
                      autoHide: false
                    }
                  }}
                  meta={{
                    owner: { alias: '决策人' },
                    count: { alias: '决策数量' }
                  }}
                  columnStyle={{
                    fill: 'l(270) 0:#1890ff 1:#36cfc9'
                  }}
                  autoFit={true}
                />
              </div>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="🎯 Bug 严重程度分布" bordered={false}>
            {severityData.length > 0 ? (
              <div style={{ height: 350 }}>
                <Pie
                  data={severityData}
                  angleField="count"
                  colorField="severity"
                  radius={0.8}
                  innerRadius={0.6}
                  label={{
                    type: 'outer',
                    content: '{name} {percentage}'
                  }}
                  statistic={{
                    title: {
                      content: '总计'
                    },
                    content: {
                      value: severityData.reduce((sum: number, item: any) => sum + item.count, 0).toString()
                    }
                  }}
                  color={({ severity }: any) => severityColors[severity] || '#d9d9d9'}
                  legend={{
                    position: 'bottom'
                  }}
                  autoFit={true}
                />
              </div>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>

      {/* 最近7天决策分布 */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24}>
          <Card title="📅 最近7天决策分布" bordered={false}>
            {/* 🛡️ 修复 4: 数组长度判断前先兜底 */}
            {(statistics?.decisions_by_date || []).length > 0 ? (
              <div style={{ height: 300 }}>
                <Column
                  data={statistics.decisions_by_date || []}
                  xField="date"
                  yField="count"
                  label={{
                    position: 'top'
                  }}
                  meta={{
                    date: { alias: '日期' },
                    count: { alias: '决策数量' }
                  }}
                  columnStyle={{
                    fill: 'l(270) 0:#ffd666 1:#ff7a45'
                  }}
                  autoFit={true}
                />
              </div>
            ) : (
              <Empty description="暂无数据" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default DataVisualization