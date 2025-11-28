/**
 * 决策回溯页面
 * 使用 ProTable 展示决策列表，支持搜索、新建、编辑和版本历史
 */
import React, { useRef, useState } from 'react'
import { ProTable, ModalForm, ProFormText, ProFormTextArea, ProFormSelect, ProFormUploadButton } from '@ant-design/pro-components'
import type { ProColumns, ActionType } from '@ant-design/pro-components'
import { Tag, Badge, message, Button, Space, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, HistoryOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import { decisionApi, uploadApi } from '@/services/api'
import type { Decision, DecisionCreate, DecisionUpdate, DecisionStatus } from '@/types'
import VersionHistory from '@/components/VersionHistory'

const DecisionLog: React.FC = () => {
  const actionRef = useRef<ActionType>()
  const queryClient = useQueryClient()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [versionModalVisible, setVersionModalVisible] = useState(false)
  const [currentDecision, setCurrentDecision] = useState<Decision | null>(null)

  // 创建决策 Mutation
  const createMutation = useMutation({
    mutationFn: decisionApi.createDecision,
    onSuccess: () => {
      message.success('决策创建成功！')
      setCreateModalVisible(false)
      queryClient.invalidateQueries({ queryKey: ['decisions'] })
      actionRef.current?.reload()
    },
    onError: () => {
      message.error('决策创建失败，请重试')
    }
  })

  // 更新决策 Mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: DecisionUpdate }) =>
      decisionApi.updateDecision(id, data),
    onSuccess: () => {
      message.success('决策更新成功！')
      setEditModalVisible(false)
      setCurrentDecision(null)
      queryClient.invalidateQueries({ queryKey: ['decisions'] })
      actionRef.current?.reload()
    },
    onError: () => {
      message.error('决策更新失败，请重试')
    }
  })

  // 表格列定义
  const columns: ProColumns<Decision>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
      search: false,
      sorter: true
    },
    {
      title: '标题',
      dataIndex: 'title',
      width: 250,
      ellipsis: true,
      copyable: true
    },
    {
      title: '决策背景',
      dataIndex: 'context',
      width: 300,
      ellipsis: true,
      search: false,
      render: (text) => (
        <div style={{ maxHeight: 60, overflow: 'hidden' }}>
          {text as string}
        </div>
      )
    },
    {
      title: '决策结论',
      dataIndex: 'verdict',
      width: 300,
      ellipsis: true,
      search: false,
      render: (text) => (
        <div style={{ maxHeight: 60, overflow: 'hidden' }}>
          {text as string}
        </div>
      )
    },
    {
      title: '决策人',
      dataIndex: 'owner',
      width: 120,
      search: false,
      render: (text) => <Tag color="blue">{text as string}</Tag>
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      valueType: 'select',
      valueEnum: {
        Active: { text: 'Active', status: 'Success' },
        Deprecated: { text: 'Deprecated', status: 'Error' }
      },
      render: (_, record) => (
        <Badge
          status={record.status === 'Active' ? 'success' : 'error'}
          text={record.status}
        />
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      search: false,
      sorter: true,
      render: (text) => dayjs(text as string).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: '附件',
      dataIndex: 'attachment_url',
      width: 100,
      search: false,
      render: (text) =>
        text ? (
          <a href={text as string} target="_blank" rel="noopener noreferrer">
            查看
          </a>
        ) : (
          '-'
        )
    },
    {
      title: '操作',
      width: 180,
      search: false,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setCurrentDecision(record)
              setEditModalVisible(true)
            }}
          >
            编辑
          </Button>
          <Button
            type="link"
            size="small"
            icon={<HistoryOutlined />}
            onClick={() => {
              setCurrentDecision(record)
              setVersionModalVisible(true)
            }}
          >
            历史
          </Button>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: 24, height: 'calc(100vh - 112px)', display: 'flex', flexDirection: 'column' }}>
      <ProTable<Decision>
        columns={columns}
        actionRef={actionRef}
        cardBordered
        // 🛡️ 修复 1: 禁用密度设置以消除控制台警告，并绑定刷新逻辑
        options={{
          density: false,
          setting: true,
          reload: () => actionRef.current?.reload(),
        }}
        // 🛡️ 修复 2: 究极防御版 Request 逻辑
        request={async (params) => {
          console.log('📡 DecisionLog Request:', params)
          try {
            const { title, status } = params
            // 调用 API
            const response = await decisionApi.getDecisions({
              keyword: title,
              status: status as DecisionStatus
            })

            console.log('📦 DecisionLog Response:', response)

            // 数据清洗：确保 safeData 绝对是数组
            let safeData: Decision[] = []
            let safeTotal = 0

            if (Array.isArray(response)) {
              // 情况 A: 后端直接返回数组 (main.py目前就是这样)
              safeData = response
              safeTotal = response.length
            } else if (response && Array.isArray((response as any).data)) {
              // 情况 B: 后端返回 { data: [], total: 100 }
              safeData = (response as any).data
              safeTotal = (response as any).total || safeData.length
            }

            return {
              data: safeData, // 这里必须是数组
              success: true,
              total: safeTotal
            }
          } catch (error) {
            console.error('❌ Request failed:', error)
            // 出错时返回空数组，防止白屏
            return {
              data: [],
              success: true,
              total: 0
            }
          }
        }}
        rowKey="id"
        search={{
          labelWidth: 'auto'
        }}
        pagination={{
          pageSize: 10,
          showSizeChanger: true
        }}
        scroll={{
          x: 'max-content',
          y: 'calc(100vh - 400px)'
        }}
        dateFormatter="string"
        headerTitle="决策记录列表"
        toolBarRender={() => [
          <ModalForm<DecisionCreate>
            key="create"
            title="新建决策"
            trigger={
              <Button type="primary" icon={<PlusOutlined />}>
                新建决策
              </Button>
            }
            open={createModalVisible}
            onOpenChange={setCreateModalVisible}
            autoFocusFirstInput
            modalProps={{
              destroyOnClose: true
            }}
            submitTimeout={2000}
            onFinish={async (values) => {
              await createMutation.mutateAsync(values)
              return true
            }}
          >
            <ProFormText
              name="title"
              label="决策标题"
              placeholder="请输入决策标题"
              rules={[{ required: true, message: '请输入决策标题' }]}
            />
            <ProFormTextArea
              name="context"
              label="决策背景"
              placeholder="描述决策的背景和原因"
              rules={[{ required: true, message: '请输入决策背景' }]}
              fieldProps={{
                rows: 4
              }}
            />
            <ProFormTextArea
              name="verdict"
              label="决策结论"
              placeholder="描述最终的决策结论"
              rules={[{ required: true, message: '请输入决策结论' }]}
              fieldProps={{
                rows: 4
              }}
            />
            <ProFormText
              name="owner"
              label="决策人"
              placeholder="请输入决策人姓名"
              rules={[{ required: true, message: '请输入决策人' }]}
            />
            <ProFormSelect
              name="status"
              label="状态"
              initialValue="Active"
              options={[
                { label: 'Active', value: 'Active' },
                { label: 'Deprecated', value: 'Deprecated' }
              ]}
            />
            <ProFormUploadButton
              name="attachment"
              label="附件"
              max={1}
              fieldProps={{
                customRequest: async ({ file, onSuccess, onError }) => {
                  try {
                    const response = await uploadApi.uploadFile(file as File)
                    onSuccess?.(response)
                    message.success('文件上传成功')
                  } catch (error) {
                    onError?.(error as Error)
                  }
                }
              }}
            />
          </ModalForm>
        ]}
      />

      {/* 编辑决策表单 */}
      <ModalForm<DecisionUpdate>
        title="编辑决策"
        open={editModalVisible}
        onOpenChange={(visible) => {
          setEditModalVisible(visible)
          if (!visible) setCurrentDecision(null)
        }}
        initialValues={currentDecision || undefined}
        autoFocusFirstInput
        modalProps={{
          destroyOnClose: true
        }}
        submitTimeout={2000}
        onFinish={async (values) => {
          if (!currentDecision) return false
          await updateMutation.mutateAsync({
            id: currentDecision.id,
            data: values
          })
          return true
        }}
      >
        <ProFormText
          name="title"
          label="决策标题"
          placeholder="请输入决策标题"
        />
        <ProFormTextArea
          name="context"
          label="决策背景"
          placeholder="描述决策的背景和原因"
          fieldProps={{
            rows: 4
          }}
        />
        <ProFormTextArea
          name="verdict"
          label="决策结论"
          placeholder="描述最终的决策结论"
          fieldProps={{
            rows: 4
          }}
        />
        <ProFormText
          name="owner"
          label="决策人"
          placeholder="请输入决策人姓名"
        />
        <ProFormSelect
          name="status"
          label="状态"
          options={[
            { label: 'Active', value: 'Active' },
            { label: 'Deprecated', value: 'Deprecated' }
          ]}
        />
        <ProFormTextArea
          name="change_reason"
          label="修改原因"
          placeholder="请说明本次修改的原因"
          fieldProps={{
            rows: 2
          }}
        />
        <ProFormText
          name="changed_by"
          label="修改人"
          placeholder="请输入修改人姓名"
          rules={[{ required: true, message: '请输入修改人' }]}
        />
      </ModalForm>

      {/* 版本历史 */}
      <VersionHistory
        decisionId={currentDecision?.id || 0}
        visible={versionModalVisible}
        onClose={() => {
          setVersionModalVisible(false)
          setCurrentDecision(null)
        }}
      />
    </div>
  )
}

export default DecisionLog