/**
 * 决策版本历史组件
 * 展示决策的修改历史
 */
import { Modal, Timeline, Tag, Empty, Spin, Descriptions } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { decisionApi } from '@/services/api'
import { DecisionStatus } from '@/types'
import dayjs from 'dayjs'

interface VersionHistoryProps {
  decisionId: number
  visible: boolean
  onClose: () => void
}

const VersionHistory: React.FC<VersionHistoryProps> = ({
  decisionId,
  visible,
  onClose
}) => {
  // 获取版本历史
  const { data: versions, isLoading } = useQuery({
    queryKey: ['decision-versions', decisionId],
    queryFn: () => decisionApi.getDecisionVersions(decisionId),
    enabled: visible && decisionId > 0
  })

  return (
    <Modal
      title={`📜 决策版本历史 (ID: ${decisionId})`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      bodyStyle={{ maxHeight: '70vh', overflow: 'auto' }}
    >
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '50px 0' }}>
          <Spin size="large" tip="加载版本历史..." />
        </div>
      ) : !versions || versions.length === 0 ? (
        <Empty description="暂无版本历史" />
      ) : (
        <Timeline mode="left">
          {versions.map((version) => (
            <Timeline.Item
              key={version.id}
              label={
                <div style={{ fontSize: '12px', color: '#999' }}>
                  {dayjs(version.created_at).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              }
              color="blue"
            >
              <div style={{ marginBottom: 16 }}>
                <div style={{ marginBottom: 8 }}>
                  <Tag color="blue">版本 {version.version}</Tag>
                  <Tag color={version.status === DecisionStatus.ACTIVE ? 'green' : 'orange'}>
                    {version.status}
                  </Tag>
                  <span style={{ color: '#666', fontSize: '12px' }}>
                    修改人: {version.changed_by}
                  </span>
                </div>

                {version.change_reason && (
                  <div
                    style={{
                      padding: '8px 12px',
                      background: '#fff7e6',
                      border: '1px solid #ffd591',
                      borderRadius: 4,
                      marginBottom: 12,
                      fontSize: '13px'
                    }}
                  >
                    <strong>修改原因:</strong> {version.change_reason}
                  </div>
                )}

                <Descriptions
                  size="small"
                  column={1}
                  bordered
                  style={{ background: '#fafafa' }}
                >
                  <Descriptions.Item label="标题">
                    {version.title}
                  </Descriptions.Item>
                  <Descriptions.Item label="背景">
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {version.context}
                    </div>
                  </Descriptions.Item>
                  <Descriptions.Item label="结论">
                    <div style={{ whiteSpace: 'pre-wrap' }}>
                      {version.verdict}
                    </div>
                  </Descriptions.Item>
                  <Descriptions.Item label="决策人">
                    {version.owner}
                  </Descriptions.Item>
                  {version.attachment_url && (
                    <Descriptions.Item label="附件">
                      <a
                        href={version.attachment_url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        查看附件
                      </a>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </div>
            </Timeline.Item>
          ))}
        </Timeline>
      )}
    </Modal>
  )
}

export default VersionHistory

