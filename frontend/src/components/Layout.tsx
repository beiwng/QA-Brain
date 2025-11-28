/**
 * 主布局组件
 * 使用 ProLayout 构建左侧导航栏
 */
import React from 'react'
import { ProLayout } from '@ant-design/pro-components'
import {
  DashboardOutlined,
  FileTextOutlined,
  BulbOutlined,
  BarChartOutlined,
  DatabaseOutlined
} from '@ant-design/icons'
import { Link, Outlet, useLocation } from 'react-router-dom'
import { useAppStore } from '@/store'

const Layout: React.FC = () => {
  const location = useLocation()
  const { collapsed, toggleCollapsed } = useAppStore()

  return (
    <div style={{ height: '100vh', overflow: 'hidden' }}>
      <ProLayout
        title="QA-Brain"
        logo="https://gw.alipayobjects.com/zos/rmsportal/KDpgvguMpGfqaHPjicRK.svg"
        layout="mix"
        collapsed={collapsed}
        onCollapse={toggleCollapsed}
        location={{
          pathname: location.pathname
        }}
        menuItemRender={(item, dom) => (
          <Link to={item.path || '/'}>{dom}</Link>
        )}
        route={{
          path: '/',
          routes: [
            {
              path: '/',
              name: '仪表盘',
              icon: <DashboardOutlined />
            },
            {
              path: '/decisions',
              name: '决策回溯',
              icon: <FileTextOutlined />
            },
            {
              path: '/analysis',
              name: '智能分析',
              icon: <BulbOutlined />
            },
            {
              path: '/visualization',
              name: '数据可视化',
              icon: <BarChartOutlined />
            },
            {
              path: '/knowledge',
              name: '知识库管理',
              icon: <DatabaseOutlined />
            }
          ]
        }}
        headerTitleRender={(logo) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {logo}
            <span style={{ fontWeight: 'bold', fontSize: 18 }}>QA-Brain</span>
          </div>
        )}
        contentStyle={{
          height: 'calc(100vh - 48px)',
          overflow: 'auto'
        }}
      >
        <Outlet />
      </ProLayout>
    </div>
  )
}

export default Layout

