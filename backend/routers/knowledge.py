"""
知识库管理路由
处理缺陷记录的 CRUD、Excel 导入、统计等
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from datetime import datetime
import io

from backend.models import (
    BugRecord, Decision,
    BugRecordCreate, BugRecordSchema, BugRecordUpdate,
    ExcelUploadResponse, KnowledgeStatsResponse
)
from backend.utils.database import get_db
from backend.utils.vector_service import vector_service
from backend.services.knowledge_service import knowledge_service

router = APIRouter(tags=["Knowledge Base"])


# === Excel 模板下载 ===
@router.get("/template/download")
async def download_excel_template():
    """
    下载 Excel 导入模板
    """
    try:
        template_bytes = knowledge_service.generate_excel_template()
        
        return StreamingResponse(
            io.BytesIO(template_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=bug_import_template.xlsx"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate template: {str(e)}")


# === Excel 批量导入 ===
@router.post("/upload/excel", response_model=ExcelUploadResponse)
async def upload_excel(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    上传 Excel 文件批量导入缺陷记录
    
    - 支持中文表头自动映射
    - 批量写入 MySQL
    - 后台异步批量写入 Milvus
    """
    try:
        # 1. 验证文件类型
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="只支持 Excel 文件 (.xlsx, .xls)")
        
        # 2. 读取文件内容
        file_content = await file.read()
        
        # 3. 解析 Excel
        records, errors = knowledge_service.parse_excel(file_content)
        
        if not records:
            return ExcelUploadResponse(
                success=False,
                imported_count=0,
                failed_count=0,
                message="未找到有效数据",
                errors=errors
            )
        
        # 4. 批量插入 MySQL
        imported_count = 0
        failed_count = 0
        bug_ids = []
        
        for record in records:
            try:
                db_bug = BugRecord(**record)
                db.add(db_bug)
                await db.flush()  # 获取 ID
                bug_ids.append((db_bug.id, record))
                imported_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f"记录 '{record.get('summary', 'Unknown')}' 插入失败: {str(e)}")
        
        await db.commit()
        
        # 5. 后台任务：批量向量化
        if bug_ids:
            background_tasks.add_task(
                batch_vectorize_bugs,
                bug_ids
            )
        
        return ExcelUploadResponse(
            success=True,
            imported_count=imported_count,
            failed_count=failed_count,
            message=f"成功导入 {imported_count} 条记录，后台正在建立索引...",
            errors=errors if errors else []
        )
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Excel 导入失败: {str(e)}")


async def batch_vectorize_bugs(bug_ids: List[tuple]):
    """
    后台任务：批量向量化缺陷记录
    
    Args:
        bug_ids: [(bug_id, bug_record_dict), ...]
    """
    print(f"🚀 开始批量向量化 {len(bug_ids)} 条缺陷记录...")
    
    for bug_id, bug_record in bug_ids:
        try:
            # 构建向量化文本
            embedding_text = knowledge_service.build_bug_embedding_text(bug_record)
            
            # 构建元数据
            metadata = knowledge_service.build_bug_metadata(bug_record)
            
            # 插入向量库
            await vector_service.insert_knowledge(
                knowledge_id=bug_id,
                content=embedding_text,
                title=bug_record.get('summary', ''),
                source_type="bug_history",
                metadata=metadata
            )
            
            print(f"✅ Bug #{bug_id} 向量化完成")
        
        except Exception as e:
            print(f"❌ Bug #{bug_id} 向量化失败: {e}")
    
    print(f"✅ 批量向量化完成")


# === 手动新增单条缺陷 ===
@router.post("/bug", response_model=BugRecordSchema)
async def create_bug_record(
    bug: BugRecordCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    手动新增单条缺陷记录
    
    - 写入 MySQL
    - 后台异步写入 Milvus
    """
    try:
        # 1. 插入 MySQL
        db_bug = BugRecord(
            summary=bug.summary,
            description=bug.description,
            root_cause=bug.root_cause,
            solution=bug.solution,
            impact_scope=bug.impact_scope,
            reporter=bug.reporter,
            assignee=bug.assignee,
            severity=bug.severity,
            category=bug.category,
            affected_version=bug.affected_version,
            status=bug.status,
            created_at=bug.created_at if bug.created_at else datetime.utcnow()
        )
        db.add(db_bug)
        await db.commit()
        await db.refresh(db_bug)
        
        # 2. 后台任务：向量化
        background_tasks.add_task(
            vectorize_single_bug,
            db_bug.id,
            bug.dict()
        )
        
        print(f"✅ Bug #{db_bug.id} 创建成功: {db_bug.summary}")
        
        return db_bug
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create bug record: {str(e)}")


async def vectorize_single_bug(bug_id: int, bug_data: dict):
    """
    后台任务：向量化单条缺陷记录
    """
    try:
        embedding_text = knowledge_service.build_bug_embedding_text(bug_data)
        metadata = knowledge_service.build_bug_metadata(bug_data)
        
        await vector_service.insert_knowledge(
            knowledge_id=bug_id,
            content=embedding_text,
            title=bug_data.get('summary', ''),
            source_type="bug_history",
            metadata=metadata
        )
        
        print(f"✅ Bug #{bug_id} 向量化完成")
    except Exception as e:
        print(f"❌ Bug #{bug_id} 向量化失败: {e}")


# === 获取缺陷列表 ===
@router.get("/bugs")
async def get_bug_records(
        severity: Optional[str] = None,
        category: Optional[str] = None,
        version: Optional[str] = None,
        keyword: Optional[str] = None,
        # ProTable 默认传 current 和 pageSize，我们可以保留 skip/limit 但逻辑要适配
        skip: int = Query(0, ge=0),
        # 将最大限制调大，或者干脆去掉 le=1000 的限制，只由前端控制
        limit: int = Query(20, ge=1, le=10000),
        db: AsyncSession = Depends(get_db)
):
    """
    获取缺陷记录列表（支持筛选 + 分页总数统计）
    """
    try:
        # --- 1. 构建筛选条件 ---
        conditions = []
        if severity:
            conditions.append(BugRecord.severity == severity)
        if category:
            conditions.append(BugRecord.category == category)
        if version:
            conditions.append(BugRecord.affected_version == version)
        if keyword:
            # 支持模糊搜索
            conditions.append(BugRecord.summary.contains(keyword))

        # --- 2. 关键步骤：计算总数 (Total) ---
        # 必须在 apply offset/limit 之前计算，否则 total 永远等于 limit
        count_query = select(func.count()).select_from(BugRecord)
        if conditions:
            count_query = count_query.where(and_(*conditions))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0  # 获取总条数 (例如 3021)

        # --- 3. 获取当前页数据 (Data) ---
        query = select(BugRecord)
        if conditions:
            query = query.where(and_(*conditions))

        # 应用排序、偏移量和限制
        query = query.order_by(BugRecord.created_at.desc()).offset(skip).limit(limit)

        result = await db.execute(query)
        bugs = result.scalars().all()

        # --- 4. 返回符合 ProTable 规范的结构 ---
        # 这样前端就知道：虽然我这次只拿了 20 条，但总共有 3021 条，从而生成页码
        return {
            "data": bugs,
            "total": total,
            "success": True,
            "pageSize": limit,
            "current": (skip // limit) + 1 if limit > 0 else 1
        }

    except Exception as e:
        print(f"❌ Fetch bugs error: {e}")  # 打印日志方便排查
        raise HTTPException(status_code=500, detail=f"Failed to fetch bug records: {str(e)}")


# === 获取知识库统计 ===
@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats(db: AsyncSession = Depends(get_db)):
    """
    获取知识库统计数据
    """
    try:
        # 1. 总缺陷数
        total_bugs_query = select(func.count(BugRecord.id))
        total_bugs_result = await db.execute(total_bugs_query)
        total_bugs = total_bugs_result.scalar() or 0
        
        # 2. 总决策数
        total_decisions_query = select(func.count(Decision.id))
        total_decisions_result = await db.execute(total_decisions_query)
        total_decisions = total_decisions_result.scalar() or 0
        
        # 3. 按严重程度统计
        severity_query = select(
            BugRecord.severity,
            func.count(BugRecord.id).label('count')
        ).group_by(BugRecord.severity)
        severity_result = await db.execute(severity_query)
        bugs_by_severity = [
            {"name": row[0] or "未知", "value": row[1]}
            for row in severity_result.all()
        ]
        
        # 4. 按分类统计
        category_query = select(
            BugRecord.category,
            func.count(BugRecord.id).label('count')
        ).group_by(BugRecord.category)
        category_result = await db.execute(category_query)
        bugs_by_category = [
            {"name": row[0] or "未知", "value": row[1]}
            for row in category_result.all()
        ]
        
        # 5. 按版本统计
        version_query = select(
            BugRecord.affected_version,
            func.count(BugRecord.id).label('count')
        ).group_by(BugRecord.affected_version).order_by(func.count(BugRecord.id).desc()).limit(10)
        version_result = await db.execute(version_query)
        bugs_by_version = [
            {"name": row[0] or "未知", "value": row[1]}
            for row in version_result.all()
        ]
        
        return KnowledgeStatsResponse(
            total_bugs=total_bugs,
            total_decisions=total_decisions,
            bugs_by_severity=bugs_by_severity,
            bugs_by_category=bugs_by_category,
            bugs_by_version=bugs_by_version
        )
    
    except Exception as e:
        import traceback
        error_detail = f"Failed to fetch stats: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 打印到控制台
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")

