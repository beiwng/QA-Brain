/**
 * 缺陷库管理组件
 * 支持 Excel 导入、手动录入、服务端分页与筛选
 */
import React, { useState, useRef } from 'react'
import { ProTable, ProColumns, ActionType } from '@ant-design/pro-components'
import { Button, Upload, message, Modal, Form, Input, Select, Tag, Space, Tooltip } from 'antd'
import { UploadOutlined, PlusOutlined, DownloadOutlined } from '@ant-design/icons'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { knowledgeApi, BugRecord } from '@/services/knowledgeApi'
import type { UploadFile } from 'antd/es/upload/interface'

const { TextArea } = Input
const { Option } = Select

const BugRepository: React.FC = () => {
  const queryClient = useQueryClient()
  const actionRef = useRef<ActionType>()
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [form] = Form.useForm()

  // 创建缺陷 Mutation
  const createMutation = useMutation({
    mutationFn: knowledgeApi.createBugRecord,
    onSuccess: () => {
      message.success('缺陷记录创建成功')
      setCreateModalVisible(false)
      form.resetFields()
      // 刷新表格数据
      actionRef.current?.reload()
      // 刷新概览统计数据
      queryClient.invalidateQueries({ queryKey: ['knowledgeStats'] })
    },
    onError: (error: any) => {
      message.error(`创建失败: ${error.response?.data?.detail || error.message}`)
    }
  })

  // Excel 上传处理
  const handleExcelUpload = async (file: UploadFile) => {
    try {
      const result = await knowledgeApi.uploadExcel(file as any)

      if (result.success) {
        message.success(result.message)
        if (result.errors && result.errors.length > 0) {
          Modal.warning({
            title: '部分记录导入失败',
            content: (
              <div>
                <p>成功导入: {result.imported_count} 条</p>
                <p>失败: {result.failed_count} 条</p>
                <div style={{ maxHeight: 300, overflow: 'auto' }}>
                  {result.errors.map((err: any, idx: number) => (
                    <p key={idx} style={{ color: 'red', fontSize: 12 }}>{err}</p>
                  ))}
                </div>
              </div>
            ),
            width: 600
          })
        }
        // 刷新表格
        actionRef.current?.reload()
        queryClient.invalidateQueries({ queryKey: ['knowledgeStats'] })
      } else {
        message.error(result.message)
      }
    } catch (error: any) {
      message.error(`上传失败: ${error.response?.data?.detail || error.message}`)
    }

    return false // 阻止默认上传行为
  }

  // 表格列定义
  const columns: ProColumns<BugRecord>[] = [
    {
      title: 'ID',
      dataIndex: 'id',
      width: 80,
      fixed: 'left',
      search: false,
      sorter: false,
    },
    {
      title: '标题',
      dataIndex: 'summary',
      width: 300,
      fixed: 'left',
      ellipsis: true,
      formItemProps: {
        name: 'keyword',
      },
      render: (text) => (
        <Tooltip title={text}>
          <span>{text}</span>
        </Tooltip>
      )
    },
    {
      title: '严重程度',
      dataIndex: 'severity',
      width: 120,
      valueType: 'select',
      valueEnum: {
        Critical: { text: '致命 (Critical)', status: 'Error' },
        Major: { text: '严重 (Major)', status: 'Warning' },
        Minor: { text: '一般 (Minor)', status: 'Processing' },
        Trivial: { text: '建议 (Trivial)', status: 'Success' },
      },
      render: (_, record) => {
        const colorMap: Record<string, string> = {
          'Critical': 'red',
          'Major': 'orange',
          'Minor': 'blue',
          'Trivial': 'green'
        }
        return <Tag color={colorMap[record.severity] || 'default'}>{record.severity}</Tag>
      }
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 120,
      valueType: 'select',
      // ✅ 修复：补充前端筛选用的 options
      fieldProps: {
        options: [
            { label: '功能', value: '功能' },
            { label: '性能', value: '性能' },
            { label: 'UI', value: 'UI' },
            { label: '数据', value: '数据' },
            { label: '部署', value: '部署' }
        ]
      },
      render: (category) => category || '-'
    },
    {
      title: '影响版本',
      dataIndex: 'affected_version',
      width: 120,
    },
    {
      title: '报告人',
      dataIndex: 'reporter',
      width: 100,
      search: false,
      render: (reporter) => reporter || '-'
    },
    {
      title: '经办人',
      dataIndex: 'assignee',
      width: 100,
      search: false,
      render: (assignee) => assignee || '-'
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 100,
      search: false,
      render: (status) => (
        <Tag color={status === 'Closed' ? 'green' : 'blue'}>{status || 'Closed'}</Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      width: 180,
      valueType: 'dateTime',
      search: false,
      sorter: false,
    }
  ]

  // 提交创建表单
  const handleCreate = () => {
    form.validateFields().then((values) => {
      createMutation.mutate(values)
    })
  }

  return (
    <>
      <ProTable<BugRecord>
        headerTitle="历史缺陷列表"
        columns={columns}
        rowKey="id"
        actionRef={actionRef}

        // 3. 开启搜索栏
        search={{
          labelWidth: 'auto',
          defaultCollapsed: false,
        }}

        options={{
          density: false, // 关闭密度，避免严格模式警告
          setting: true,
          reload: () => actionRef.current?.reload(),
        }}

        // 4. 配置服务端分页参数
        pagination={{
          pageSize: 20,
          showSizeChanger: true,
          pageSizeOptions: ['20', '50', '100'],
          showTotal: (total) => `共 ${total} 条记录`
        }}

        scroll={{ x: 1500 }}

        // 🔥🔥🔥 核心修复区：Request 逻辑 🔥🔥🔥
        request={async (params, sort, filter) => {
          console.log('📡 ProTable 发起请求:', params);

          try {
            // 1. 计算分页参数
            const current = params.current || 1;
            const pageSize = params.pageSize || 20;
            const skip = (current - 1) * pageSize;

            // 2. 调用后端接口
            const res = await knowledgeApi.getBugRecords({
              skip: skip,
              limit: pageSize,
              severity: params.severity,
              category: params.category,
              version: params.affected_version,
              keyword: params.keyword,
            });

            console.log('📦 后端原始返回:', res);

            // 3. 🛡️ 究极防御：确保 data 是数组
            let safeData: any[] = [];
            let safeTotal = 0;

            if (res) {
                if (Array.isArray(res.data)) {
                    // 情况 A: 标准结构 { data: [], total: 100 }
                    safeData = res.data;
                    safeTotal = res.total || 0;
                } else if (res.data && Array.isArray(res.data.data)) {
                    // 情况 B: 嵌套结构 { data: { data: [] } }
                    safeData = res.data.data;
                    safeTotal = res.data.total || 0;
                } else if (Array.isArray(res)) {
                    // 情况 C: 直接返回数组
                    safeData = res;
                    safeTotal = res.length;
                }
            }

            // 4. 强制校验，如果解析失败，给空数组，绝不崩页面
            if (!Array.isArray(safeData)) {
                console.error("❌ 数据解析失败，强制置空:", res);
                safeData = [];
            }

            return {
              data: safeData, // ✅ 必须是数组！
              success: true,
              total: safeTotal,
            };
          } catch (error) {
            console.error('❌ 请求异常:', error);
            return {
              data: [], // 异常时也返回空数组
              success: true,
              total: 0,
            };
          }
        }}

        toolBarRender={() => [
          <Button
            key="download"
            icon={<DownloadOutlined />}
            onClick={() => knowledgeApi.downloadTemplate()}
          >
            下载模板
          </Button>,
          <Upload
            key="upload"
            accept=".xlsx,.xls"
            showUploadList={false}
            beforeUpload={handleExcelUpload}
          >
            <Button icon={<UploadOutlined />} type="primary">
              Excel 导入
            </Button>
          </Upload>,
          <Button
            key="create"
            icon={<PlusOutlined />}
            type="primary"
            onClick={() => setCreateModalVisible(true)}
          >
            手动录入
          </Button>
        ]}
      />

      {/* 创建缺陷记录 Modal */}
      <Modal
        title="新增缺陷记录"
        open={createModalVisible}
        onOk={handleCreate}
        onCancel={() => {
          setCreateModalVisible(false)
          form.resetFields()
        }}
        confirmLoading={createMutation.isPending}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ status: 'Closed' }}
        >
          <Form.Item
            name="summary"
            label="缺陷标题"
            rules={[{ required: true, message: '请输入缺陷标题' }]}
          >
            <Input placeholder="请输入缺陷标题" />
          </Form.Item>

          <Form.Item name="description" label="详细描述/复现步骤">
            <TextArea rows={3} placeholder="请输入详细描述或复现步骤" />
          </Form.Item>

          <Form.Item name="root_cause" label="问题原因">
            <TextArea rows={2} placeholder="请输入问题根因" />
          </Form.Item>

          <Form.Item name="solution" label="解决方案">
            <TextArea rows={2} placeholder="请输入解决方案" />
          </Form.Item>

          <Form.Item name="impact_scope" label="影响范围">
            <Input placeholder="例如：所有用户、生产环境等" />
          </Form.Item>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="severity" label="严重程度" style={{ width: 150 }}>
              <Select placeholder="选择严重程度">
                <Option value="Critical">Critical</Option>
                <Option value="Major">Major</Option>
                <Option value="Minor">Minor</Option>
                <Option value="Trivial">Trivial</Option>
              </Select>
            </Form.Item>

            <Form.Item name="category" label="缺陷分类" style={{ width: 150 }}>
              {/* ✅ 修复：手动录入时也需要选项 */}
              <Select placeholder="选择分类">
                <Option value="功能">功能</Option>
                <Option value="性能">性能</Option>
                <Option value="UI">UI</Option>
                <Option value="数据">数据</Option>
                <Option value="部署">部署</Option>
              </Select>
            </Form.Item>

            <Form.Item name="affected_version" label="影响版本" style={{ width: 150 }}>
              <Input placeholder="例如：S010B12P01" />
            </Form.Item>
          </Space>

          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="reporter" label="报告人" style={{ width: 150 }}>
              <Input placeholder="报告人" />
            </Form.Item>

            <Form.Item name="assignee" label="经办人" style={{ width: 150 }}>
              <Input placeholder="经办人/修复人" />
            </Form.Item>

            <Form.Item name="status" label="状态" style={{ width: 150 }}>
              <Select>
                <Option value="Open">Open</Option>
                <Option value="In Progress">In Progress</Option>
                <Option value="Closed">Closed</Option>
              </Select>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </>
  )
}

export default BugRepository