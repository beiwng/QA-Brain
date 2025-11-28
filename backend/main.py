"""
QA-Brain FastAPI Application
主应用入口，定义所有 API 路由
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List
from datetime import datetime, timedelta
from pathlib import Path
import uvicorn
import os

from backend.config import settings
# ✅ 适配 1: 导入 BugRecord，以便在统计接口中使用
from backend.models import (
    Decision, BugInsight, DecisionVersion, BugRecord,
    DecisionCreate, DecisionSchema, DecisionUpdate, DecisionVersionSchema,
    BugAnalysisRequest, BugAnalysisResponse,
    UploadResponse, DecisionStatus,
    StatisticsResponse, TrendDataResponse
)
from backend.utils.database import get_db
from backend.utils.minio_service import minio_service
from backend.utils.vector_service import vector_service
from backend.graph_agent import analyze_bug_with_graph
from backend.routers.knowledge import router as knowledge_router

# === Application Setup ===
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="QA 工程师的智能决策助手",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# ==========================================
# 🚀 核心配置：CORS (允许局域网访问)
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有IP，方便真机调试
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 (知识库/缺陷管理)
app.include_router(knowledge_router, prefix="/api/knowledge", tags=["Knowledge Base"])


# === Startup Event ===
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    print(f"\n🚀 {settings.PROJECT_NAME} is starting...")

    # 连接 Milvus
    try:
        vector_service.connect()
        # vector_service.create_collection() # 初始化脚本已处理，此处可注释防止重复检查
        vector_service.load_collection()
        print("✅ Milvus connected and loaded")
    except Exception as e:
        print(f"⚠️ Milvus initialization failed: {e}")

    print(f"✅ {settings.PROJECT_NAME} is ready!\n")


@app.get("/")
def read_root():
    return {"message": "QA-Brain API is running 🚀"}


# === Decision APIs ===
@app.get("/api/decisions", response_model=List[DecisionSchema])
async def get_decisions(
        status: DecisionStatus = None,
        keyword: str = None,
        db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Decision)

        if status:
            query = query.where(Decision.status == status)

        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.where(
                (Decision.title.like(search_pattern)) |
                (Decision.context.like(search_pattern)) |
                (Decision.verdict.like(search_pattern))
            )

        query = query.order_by(Decision.created_at.desc())

        result = await db.execute(query)
        decisions = result.scalars().all()

        return decisions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/api/decisions", response_model=DecisionSchema)
async def create_decision(
        decision: DecisionCreate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """
    创建新决策 (已适配 v2.0 RAG 逻辑)
    """
    try:
        # 1. 存入 MySQL
        db_decision = Decision(
            title=decision.title,
            context=decision.context,
            verdict=decision.verdict,
            owner=decision.owner,
            status=decision.status,
            attachment_url=decision.attachment_url
        )
        db.add(db_decision)
        await db.commit()
        await db.refresh(db_decision)

        # 2. 后台任务：向量化存入 Milvus
        # ✅ 适配 2: 严格按照 VectorService.insert_knowledge 的 6 字段逻辑
        embedding_content = f"决策标题: {db_decision.title}\n背景: {db_decision.context}\n结论: {db_decision.verdict}"

        metadata = {
            "source_type": "decision",
            "db_id": db_decision.id,
            "status": db_decision.status.value,
            "owner": db_decision.owner,
            # 🔥 关键新增：将结论存入 Metadata，供 LLM 直接读取，无需解析长文本
            "verdict": db_decision.verdict,
            "context_snippet": db_decision.context[:1000]
        }

        background_tasks.add_task(
            vector_service.insert_knowledge,
            knowledge_id=db_decision.id,
            content=embedding_content,
            title=db_decision.title,
            source_type="decision",
            metadata=metadata
        )

        print(f"✅ Decision #{db_decision.id} created: {db_decision.title}")

        return db_decision

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create decision: {str(e)}")


@app.put("/api/decisions/{decision_id}", response_model=DecisionSchema)
async def update_decision(
        decision_id: int,
        update_data: DecisionUpdate,
        background_tasks: BackgroundTasks,
        db: AsyncSession = Depends(get_db)
):
    """
    更新决策并创建版本历史 (已适配 v2.0 RAG 逻辑)
    """
    try:
        # 1. 查询现有决策
        result = await db.execute(select(Decision).where(Decision.id == decision_id))
        decision = result.scalar_one_or_none()

        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")

        # 2. 版本控制逻辑 (保持不变)
        version_result = await db.execute(
            select(func.max(DecisionVersion.version))
            .where(DecisionVersion.decision_id == decision_id)
        )
        max_version = version_result.scalar() or 0
        new_version = max_version + 1

        version = DecisionVersion(
            decision_id=decision.id,
            version=new_version,
            title=decision.title,
            context=decision.context,
            verdict=decision.verdict,
            owner=decision.owner,
            status=decision.status,
            attachment_url=decision.attachment_url,
            change_reason=update_data.change_reason,
            changed_by=update_data.changed_by
        )
        db.add(version)

        # 3. 更新字段
        if update_data.title is not None: decision.title = update_data.title
        if update_data.context is not None: decision.context = update_data.context
        if update_data.verdict is not None: decision.verdict = update_data.verdict
        if update_data.owner is not None: decision.owner = update_data.owner
        if update_data.status is not None: decision.status = update_data.status
        if update_data.attachment_url is not None: decision.attachment_url = update_data.attachment_url

        await db.commit()
        await db.refresh(decision)

        # 4. 后台任务：更新向量库
        # ✅ 适配 3: Metadata 必须包含 verdict 和 context_snippet
        embedding_content = f"决策标题: {decision.title}\n背景: {decision.context}\n结论: {decision.verdict}"

        metadata = {
            "source_type": "decision",
            "db_id": decision.id,
            "status": decision.status.value,
            "owner": decision.owner,
            # 🔥 关键新增
            "verdict": decision.verdict,
            "context_snippet": decision.context[:1000]
        }

        background_tasks.add_task(
            vector_service.insert_knowledge,
            knowledge_id=decision.id,
            content=embedding_content,
            title=decision.title,
            source_type="decision",
            metadata=metadata
        )

        print(f"✅ Decision #{decision_id} updated (version {new_version})")

        return decision

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update decision: {str(e)}")


@app.get("/api/decisions/{decision_id}/versions", response_model=List[DecisionVersionSchema])
async def get_decision_versions(
        decision_id: int,
        db: AsyncSession = Depends(get_db)
):
    try:
        query = select(DecisionVersion).where(
            DecisionVersion.decision_id == decision_id
        ).order_by(DecisionVersion.version.desc())
        result = await db.execute(query)
        return result.scalars().all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get versions: {str(e)}")


# === AI Analysis API ===
@app.post("/api/analyze", response_model=BugAnalysisResponse)
async def analyze_bug(
        request: BugAnalysisRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    智能 Bug 分析接口
    LangGraph 会自动检索 决策(Decision) 和 缺陷(BugRecord) 并进行综合分析
    """
    try:
        print(f"\n🧠 Analyzing bug: {request.query[:50]}...")

        # 运行 LangGraph (已在 graph_agent.py 中适配了双流检索)
        result = await analyze_bug_with_graph(request.query)

        # 保存分析记录
        insight = BugInsight(
            query=request.query,
            analysis_result=result["answer"],
            severity=result["severity"],
            referenced_decisions=",".join(result["sources"]) if result["sources"] else None
        )
        db.add(insight)
        await db.commit()

        print(f"✅ Analysis saved (ID: {insight.id})")

        return BugAnalysisResponse(
            answer=result["answer"],
            sources=result["sources"],
            severity=result["severity"]
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# === File Upload API ===
@app.post("/api/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        MAX_FILE_SIZE = 10 * 1024 * 1024
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

        url = minio_service.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        return UploadResponse(url=url, filename=file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# === Statistics APIs ===
@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics(db: AsyncSession = Depends(get_db)):
    """
    获取统计数据 (适配缺陷库统计)
    """
    try:
        # 1. 总决策数
        total_decisions = (await db.execute(select(func.count(Decision.id)))).scalar() or 0

        # 2. 活跃决策数
        active_decisions = (await db.execute(
            select(func.count(Decision.id)).where(Decision.status == DecisionStatus.ACTIVE)
        )).scalar() or 0

        # 3. 废弃决策
        deprecated_decisions = total_decisions - active_decisions

        # 4. 总分析次数
        total_analyses = (await db.execute(select(func.count(BugInsight.id)))).scalar() or 0

        # ✅ 适配 4: 增加缺陷知识库的总数统计 (体现缺陷数据适配)
        total_bugs = (await db.execute(select(func.count(BugRecord.id)))).scalar() or 0

        # 5. 按决策人统计 (Top 10)
        owner_result = await db.execute(
            select(Decision.owner, func.count(Decision.id).label('count'))
            .group_by(Decision.owner).order_by(func.count(Decision.id).desc()).limit(10)
        )
        decisions_by_owner = [{"owner": row[0], "count": row[1]} for row in owner_result.all()]

        # 6. 按日期统计 (最近7天)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        date_result = await db.execute(
            select(func.date(Decision.created_at).label('date'), func.count(Decision.id).label('count'))
            .where(Decision.created_at >= seven_days_ago)
            .group_by(func.date(Decision.created_at))
        )
        decisions_by_date = [{"date": str(row[0]), "count": row[1]} for row in date_result.all()]

        # 7. 按严重程度统计
        severity_result = await db.execute(
            select(BugInsight.severity, func.count(BugInsight.id).label('count'))
            .where(BugInsight.severity.isnot(None))
            .group_by(BugInsight.severity)
        )
        analyses_by_severity = [{"severity": row[0].value if row[0] else "Unknown", "count": row[1]} for row in
                                severity_result.all()]

        # 8. 最近决策 (最近5条)
        recent_result = await db.execute(select(Decision).order_by(Decision.created_at.desc()).limit(5))
        recent_decisions = recent_result.scalars().all()

        return StatisticsResponse(
            total_decisions=total_decisions,
            active_decisions=active_decisions,
            deprecated_decisions=deprecated_decisions,
            total_analyses=total_analyses,
            total_bugs=total_bugs,
            decisions_by_owner=decisions_by_owner,
            decisions_by_date=decisions_by_date,
            analyses_by_severity=analyses_by_severity,
            recent_decisions=recent_decisions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.get("/api/trends", response_model=TrendDataResponse)
async def get_trends(days: int = 30, db: AsyncSession = Depends(get_db)):
    # ... (保持原有的趋势统计逻辑不变)
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        decision_result = await db.execute(
            select(func.date(Decision.created_at), func.count(Decision.id))
            .where(Decision.created_at >= start_date)
            .group_by(func.date(Decision.created_at))
        )
        decision_data = {str(row[0]): row[1] for row in decision_result.all()}

        analysis_result = await db.execute(
            select(func.date(BugInsight.created_at), func.count(BugInsight.id))
            .where(BugInsight.created_at >= start_date)
            .group_by(func.date(BugInsight.created_at))
        )
        analysis_data = {str(row[0]): row[1] for row in analysis_result.all()}

        dates = []
        decision_counts = []
        analysis_counts = []
        current = start_date.date()
        end = datetime.utcnow().date()
        while current <= end:
            d = str(current)
            dates.append(d)
            decision_counts.append(decision_data.get(d, 0))
            analysis_counts.append(analysis_data.get(d, 0))
            current += timedelta(days=1)

        return TrendDataResponse(dates=dates, decision_counts=decision_counts, analysis_counts=analysis_counts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trends: {str(e)}")


# === Run Server ===
if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG
    )

