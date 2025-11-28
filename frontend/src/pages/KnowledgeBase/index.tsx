/**
 * 知识库管理页面
 * Tab 1: 缺陷库管理
 * Tab 2: 知识库概览
 */
import React, { useState } from 'react'
import { Tabs } from 'antd'
import { DatabaseOutlined, BarChartOutlined } from '@ant-design/icons'
import BugRepository from './BugRepository'
import KnowledgeOverview from './KnowledgeOverview'

const { TabPane } = Tabs

const KnowledgeBase: React.FC = () => {
  const [activeTab, setActiveTab] = useState('bugs')

  return (
    <div style={{ padding: 24 }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        size="large"
        items={[
          {
            key: 'bugs',
            label: (
              <span>
                <DatabaseOutlined />
                缺陷库管理
              </span>
            ),
            children: <BugRepository />
          },
          {
            key: 'overview',
            label: (
              <span>
                <BarChartOutlined />
                知识库概览
              </span>
            ),
            children: <KnowledgeOverview />
          }
        ]}
      />
    </div>
  )
}

export default KnowledgeBase

