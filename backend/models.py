"""
QA-Brain Data Models
定义 MySQL 表结构和 Pydantic Schema
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
import enum

Base = declarative_base()


# === Enums ===
class DecisionStatus(str, enum.Enum):
    """决策状态枚举"""
    ACTIVE = "Active"
    DEPRECATED = "Deprecated"


class BugSeverity(str, enum.Enum):
    """Bug 严重程度枚举 (符合行业标准)"""
    BLOCKER = "Blocker"
    CRITICAL = "Critical"
    MAJOR = "Major"
    MINOR = "Minor"
    TRIVIAL = "Trivial"


# === SQLAlchemy Models (MySQL) ===
class Decision(Base):
    """决策记录表"""
    __tablename__ = "decisions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, comment="决策标题", index=True)  # 添加索引
    context = Column(Text, nullable=False, comment="决策背景")
    verdict = Column(Text, nullable=False, comment="决策结论")
    owner = Column(String(100), nullable=False, comment="决策人", index=True)  # 添加索引
    status = Column(SQLEnum(DecisionStatus), default=DecisionStatus.ACTIVE, comment="状态", index=True)  # 添加索引
    attachment_url = Column(String(512), nullable=True, comment="附件 URL (MinIO)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间", index=True)  # 添加索引
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 关系
    versions = relationship("DecisionVersion", back_populates="decision", cascade="all, delete-orphan")

    # 复合索引
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),  # 状态+时间复合索引
        Index('idx_owner_status', 'owner', 'status'),  # 决策人+状态复合索引
    )


class DecisionVersion(Base):
    """决策版本历史表"""
    __tablename__ = "decision_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    decision_id = Column(Integer, ForeignKey('decisions.id', ondelete='CASCADE'), nullable=False, comment="关联的决策 ID", index=True)
    version = Column(Integer, nullable=False, comment="版本号")
    title = Column(String(255), nullable=False, comment="决策标题")
    context = Column(Text, nullable=False, comment="决策背景")
    verdict = Column(Text, nullable=False, comment="决策结论")
    owner = Column(String(100), nullable=False, comment="决策人")
    status = Column(SQLEnum(DecisionStatus), nullable=False, comment="状态")
    attachment_url = Column(String(512), nullable=True, comment="附件 URL")
    change_reason = Column(String(500), nullable=True, comment="修改原因")
    changed_by = Column(String(100), nullable=False, comment="修改人")
    created_at = Column(DateTime, default=datetime.utcnow, comment="版本创建时间", index=True)

    # 关系
    decision = relationship("Decision", back_populates="versions")

    # 复合索引
    __table_args__ = (
        Index('idx_decision_version', 'decision_id', 'version'),  # 决策ID+版本号复合索引
    )


class BugInsight(Base):
    """Bug 智能分析记录表"""
    __tablename__ = "bug_insights"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query = Column(Text, nullable=False, comment="用户输入的 Bug 描述")
    analysis_result = Column(Text, nullable=False, comment="AI 分析结果 (Markdown)")
    severity = Column(SQLEnum(BugSeverity), nullable=True, comment="AI 判定的严重程度", index=True)  # 添加索引
    referenced_decisions = Column(String(512), nullable=True, comment="引用的决策 ID (逗号分隔)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="分析时间", index=True)  # 添加索引

    # 复合索引
    __table_args__ = (
        Index('idx_severity_created', 'severity', 'created_at'),  # 严重程度+时间复合索引
    )


class BugRecord(Base):
    """历史缺陷知识库表"""
    __tablename__ = "bug_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # --- 核心描述 (用于向量化) ---
    summary = Column(String(500), nullable=False, comment="缺陷标题", index=True)
    description = Column(Text, nullable=True, comment="详细描述/复现步骤")
    root_cause = Column(Text, nullable=True, comment="问题原因 (关键知识)")
    solution = Column(Text, nullable=True, comment="解决方案 (关键知识)")
    impact_scope = Column(String(500), nullable=True, comment="影响范围")

    # --- 业务属性 (用于 Metadata / 统计) ---
    reporter = Column(String(50), nullable=True, comment="报告人", index=True)
    assignee = Column(String(50), nullable=True, comment="经办人/修复人", index=True)
    severity = Column(String(50), nullable=True, comment="严重程度 (Critical/Major/Minor)", index=True)
    category = Column(String(50), nullable=True, comment="缺陷分类 (功能/性能/UI/数据)", index=True)
    affected_version = Column(String(255), nullable=True, comment="影响版本", index=True)
    status = Column(String(50), default="Closed", comment="状态")

    created_at = Column(DateTime, default=datetime.utcnow, comment="创建日期", index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")

    # 复合索引
    __table_args__ = (
        Index('idx_severity_version', 'severity', 'affected_version'),  # 严重程度+版本复合索引
        Index('idx_category_status', 'category', 'status'),  # 分类+状态复合索引
    )


# === Pydantic Schemas (API) ===
class DecisionCreate(BaseModel):
    """创建决策的请求体"""
    title: str = Field(..., min_length=1, max_length=255, description="决策标题")
    context: str = Field(..., min_length=1, description="决策背景")
    verdict: str = Field(..., min_length=1, description="决策结论")
    owner: str = Field(..., min_length=1, max_length=100, description="决策人")
    status: DecisionStatus = Field(default=DecisionStatus.ACTIVE, description="状态")
    attachment_url: Optional[str] = Field(None, description="附件 URL")


class DecisionSchema(BaseModel):
    """决策记录的响应体"""
    id: int
    title: str
    context: str
    verdict: str
    owner: str
    status: DecisionStatus
    attachment_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DecisionUpdate(BaseModel):
    """更新决策的请求体"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="决策标题")
    context: Optional[str] = Field(None, min_length=1, description="决策背景")
    verdict: Optional[str] = Field(None, min_length=1, description="决策结论")
    owner: Optional[str] = Field(None, min_length=1, max_length=100, description="决策人")
    status: Optional[DecisionStatus] = Field(None, description="状态")
    attachment_url: Optional[str] = Field(None, description="附件 URL")
    change_reason: Optional[str] = Field(None, max_length=500, description="修改原因")
    changed_by: str = Field(..., min_length=1, max_length=100, description="修改人")


class DecisionVersionSchema(BaseModel):
    """决策版本历史的响应体"""
    id: int
    decision_id: int
    version: int
    title: str
    context: str
    verdict: str
    owner: str
    status: DecisionStatus
    attachment_url: Optional[str]
    change_reason: Optional[str]
    changed_by: str
    created_at: datetime

    class Config:
        from_attributes = True


class BugAnalysisRequest(BaseModel):
    """Bug 分析请求"""
    query: str = Field(..., min_length=1, description="Bug 描述或报错日志")


class BugAnalysisResponse(BaseModel):
    """Bug 分析响应"""
    answer: str = Field(..., description="AI 分析结果 (Markdown 格式)")
    sources: List[str] = Field(default_factory=list, description="引用的决策 ID 列表")
    severity: Optional[BugSeverity] = Field(None, description="AI 判定的严重程度")


class UploadResponse(BaseModel):
    """文件上传响应"""
    url: str = Field(..., description="文件访问 URL")
    filename: str = Field(..., description="文件名")


class StatisticsResponse(BaseModel):
    """统计数据响应"""
    total_decisions: int = Field(..., description="总决策数")
    active_decisions: int = Field(..., description="活跃决策数")
    deprecated_decisions: int = Field(..., description="已废弃决策数")
    total_analyses: int = Field(..., description="总分析次数")
    total_bugs: int = Field(..., description="总缺陷数")
    decisions_by_owner: List[dict] = Field(default_factory=list, description="按决策人统计")
    decisions_by_date: List[dict] = Field(default_factory=list, description="按日期统计")
    analyses_by_severity: List[dict] = Field(default_factory=list, description="按严重程度统计")
    recent_decisions: List[DecisionSchema] = Field(default_factory=list, description="最近决策")


class TrendDataResponse(BaseModel):
    """趋势数据响应"""
    dates: List[str] = Field(..., description="日期列表")
    decision_counts: List[int] = Field(..., description="决策数量列表")
    analysis_counts: List[int] = Field(..., description="分析数量列表")


# === Bug Record Schemas ===
class BugRecordCreate(BaseModel):
    """创建缺陷记录的请求体"""
    summary: str = Field(..., min_length=1, max_length=500, description="缺陷标题")
    description: Optional[str] = Field(None, description="详细描述/复现步骤")
    root_cause: Optional[str] = Field(None, description="问题原因")
    solution: Optional[str] = Field(None, description="解决方案")
    impact_scope: Optional[str] = Field(None, max_length=500, description="影响范围")
    reporter: Optional[str] = Field(None, max_length=50, description="报告人")
    assignee: Optional[str] = Field(None, max_length=50, description="经办人/修复人")
    severity: Optional[str] = Field(None, max_length=50, description="严重程度")
    category: Optional[str] = Field(None, max_length=50, description="缺陷分类")
    affected_version: Optional[str] = Field(None, max_length=255, description="影响版本")
    status: Optional[str] = Field("Closed", max_length=50, description="状态")
    created_at: Optional[datetime] = Field(None, description="创建日期（支持导入历史数据）")


class BugRecordSchema(BaseModel):
    """缺陷记录的响应体"""
    id: int
    summary: str
    description: Optional[str]
    root_cause: Optional[str]
    solution: Optional[str]
    impact_scope: Optional[str]
    reporter: Optional[str]
    assignee: Optional[str]
    severity: Optional[str]
    category: Optional[str]
    affected_version: Optional[str]
    status: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BugRecordUpdate(BaseModel):
    """更新缺陷记录的请求体"""
    summary: Optional[str] = Field(None, min_length=1, max_length=500, description="缺陷标题")
    description: Optional[str] = Field(None, description="详细描述")
    root_cause: Optional[str] = Field(None, description="问题原因")
    solution: Optional[str] = Field(None, description="解决方案")
    impact_scope: Optional[str] = Field(None, max_length=500, description="影响范围")
    reporter: Optional[str] = Field(None, max_length=50, description="报告人")
    assignee: Optional[str] = Field(None, max_length=50, description="经办人")
    severity: Optional[str] = Field(None, max_length=50, description="严重程度")
    category: Optional[str] = Field(None, max_length=50, description="缺陷分类")
    affected_version: Optional[str] = Field(None, max_length=255, description="影响版本")
    status: Optional[str] = Field(None, max_length=50, description="状态")


class ExcelUploadResponse(BaseModel):
    """Excel 上传响应"""
    success: bool = Field(..., description="是否成功")
    imported_count: int = Field(..., description="成功导入的记录数")
    failed_count: int = Field(0, description="失败的记录数")
    message: str = Field(..., description="提示信息")
    errors: List[str] = Field(default_factory=list, description="错误详情")


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应"""
    total_bugs: int = Field(..., description="历史缺陷总数")
    total_decisions: int = Field(..., description="已索引决策数")
    bugs_by_severity: List[dict] = Field(default_factory=list, description="按严重程度统计")
    bugs_by_category: List[dict] = Field(default_factory=list, description="按分类统计")
    bugs_by_version: List[dict] = Field(default_factory=list, description="按版本统计")

