"""
知识库服务
处理 Excel 导入、缺陷记录管理、向量化等
"""
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple
from pathlib import Path
import io


class KnowledgeService:
    """知识库服务类"""
    
    # Excel 列名映射（支持中文表头）
    COLUMN_MAPPING = {
        # 核心字段
        "标题": "summary",
        "摘要": "summary",
        "缺陷标题": "summary",
        "描述": "description",
        "详细描述": "description",
        "复现步骤": "description",
        "问题描述": "description",
        "原因": "root_cause",
        "根因": "root_cause",
        "问题原因": "root_cause",
        "根本原因": "root_cause",
        "解决方案": "solution",
        "处理结果": "solution",
        "修复方案": "solution",
        "影响范围": "impact_scope",
        
        # 业务属性
        "报告人": "reporter",
        "提交人": "reporter",
        "经办人": "assignee",
        "修复人": "assignee",
        "处理人": "assignee",
        "严重程度": "severity",
        "优先级": "severity",
        "分类": "category",
        "缺陷分类": "category",
        "类型": "category",
        "影响版本": "affected_version",
        "版本": "affected_version",
        "状态": "status",
        "创建时间": "created_at",
        "创建日期": "created_at",
        "提交时间": "created_at",
    }
    
    @staticmethod
    def parse_excel(file_content: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        解析 Excel 文件
        
        Args:
            file_content: Excel 文件的字节内容
        
        Returns:
            (成功解析的记录列表, 错误信息列表)
        """
        records = []
        errors = []
        
        try:
            # 读取 Excel
            df = pd.read_excel(io.BytesIO(file_content), engine='openpyxl')
            
            # 标准化列名（去除空格）
            df.columns = df.columns.str.strip()
            
            # 映射列名
            column_map = {}
            for col in df.columns:
                if col in KnowledgeService.COLUMN_MAPPING:
                    column_map[col] = KnowledgeService.COLUMN_MAPPING[col]
            
            if not column_map:
                errors.append("未找到可识别的列名，请检查 Excel 表头")
                return records, errors
            
            # 重命名列
            df = df.rename(columns=column_map)
            
            # 检查必填字段
            if 'summary' not in df.columns:
                errors.append("缺少必填字段：标题/摘要")
                return records, errors
            
            # 逐行解析
            for idx, row in df.iterrows():
                try:
                    # 跳过空行
                    if pd.isna(row.get('summary')) or str(row.get('summary')).strip() == '':
                        continue
                    
                    record = {
                        'summary': str(row.get('summary', '')).strip(),
                        'description': str(row.get('description', '')) if pd.notna(row.get('description')) else None,
                        'root_cause': str(row.get('root_cause', '')) if pd.notna(row.get('root_cause')) else None,
                        'solution': str(row.get('solution', '')) if pd.notna(row.get('solution')) else None,
                        'impact_scope': str(row.get('impact_scope', '')) if pd.notna(row.get('impact_scope')) else None,
                        'reporter': str(row.get('reporter', '')) if pd.notna(row.get('reporter')) else None,
                        'assignee': str(row.get('assignee', '')) if pd.notna(row.get('assignee')) else None,
                        'severity': str(row.get('severity', '')) if pd.notna(row.get('severity')) else None,
                        'category': str(row.get('category', '')) if pd.notna(row.get('category')) else None,
                        'affected_version': str(row.get('affected_version', '')) if pd.notna(row.get('affected_version')) else None,
                        'status': str(row.get('status', 'Closed')).strip() or 'Closed',
                    }
                    
                    # 处理时间字段
                    if 'created_at' in df.columns and pd.notna(row.get('created_at')):
                        try:
                            created_at = pd.to_datetime(row.get('created_at'))
                            record['created_at'] = created_at.to_pydatetime()
                        except Exception as e:
                            # 时间解析失败，使用当前时间
                            record['created_at'] = None
                    else:
                        record['created_at'] = None
                    
                    records.append(record)
                
                except Exception as e:
                    errors.append(f"第 {idx + 2} 行解析失败: {str(e)}")
            
            if not records:
                errors.append("未找到有效的数据行")
            
        except Exception as e:
            errors.append(f"Excel 文件解析失败: {str(e)}")
        
        return records, errors

    @staticmethod
    def build_bug_embedding_text(bug_record: Dict[str, Any]) -> str:
        """
        构建缺陷记录的向量化文本 (用于语义检索)
        """
        parts = []

        # 标题
        if bug_record.get('summary'):
            parts.append(f"缺陷: {bug_record['summary']}")

        # 描述
        if bug_record.get('description'):
            parts.append(f"现象: {bug_record['description']}")

        # 根因
        if bug_record.get('root_cause'):
            parts.append(f"根因: {bug_record['root_cause']}")

        # 解决方案
        if bug_record.get('solution'):
            parts.append(f"解决: {bug_record['solution']}")

        # ✅ 新增：影响范围 (让语义检索能感知到范围关键词)
        if bug_record.get('impact_scope'):
            parts.append(f"范围: {bug_record['impact_scope']}")

        return "\n".join(parts)

    @staticmethod
    def build_bug_metadata(bug_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建缺陷记录的元数据 (用于 LLM 分析时的上下文透传)
        """
        return {
            "source_type": "bug_history",
            # 基础属性
            "severity": bug_record.get('severity', ''),
            "category": bug_record.get('category', ''),
            "version": bug_record.get('affected_version', ''),
            "reporter": bug_record.get('reporter', ''),
            "status": bug_record.get('status', 'Closed'),

            # ✅ 新增：关键分析字段 (存入 metadata 以便 LLM 直接读取)
            "impact_scope": bug_record.get('impact_scope', '未知'),
            "root_cause": bug_record.get('root_cause', ''),
            "solution": bug_record.get('solution', '')
        }
    
    @staticmethod
    def generate_excel_template() -> bytes:
        """
        生成 Excel 导入模板
        
        Returns:
            Excel 文件的字节内容
        """
        # 创建示例数据
        template_data = {
            '标题': ['用户登录失败', '数据库连接超时', '页面加载缓慢'],
            '描述': [
                '用户输入正确的用户名和密码后，点击登录按钮无响应',
                '应用启动时，数据库连接池初始化失败，抛出超时异常',
                '首页加载时间超过 10 秒，用户体验差'
            ],
            '根因': [
                '后端 Session 验证逻辑错误，导致认证失败',
                '数据库服务器负载过高，连接数达到上限',
                '前端资源未压缩，图片过大'
            ],
            '解决方案': [
                '修复 Session 验证逻辑，增加错误日志',
                '优化数据库连接池配置，增加最大连接数',
                '启用 Gzip 压缩，优化图片资源'
            ],
            '影响范围': ['所有用户', '生产环境', '首页访问用户'],
            '报告人': ['张三', '李四', '王五'],
            '经办人': ['开发A', '开发B', '前端C'],
            '严重程度': ['Critical', 'Major', 'Minor'],
            '分类': ['功能', '性能', '性能'],
            '影响版本': ['v1.0.0', 'v1.0.1', 'v1.0.2'],
            '状态': ['Closed', 'Closed', 'Closed'],
            '创建时间': ['2024-01-15', '2024-02-20', '2024-03-10']
        }
        
        df = pd.DataFrame(template_data)
        
        # 写入 BytesIO
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='缺陷记录')
            
            # 获取工作表
            worksheet = writer.sheets['缺陷记录']
            
            # 设置列宽
            for idx, col in enumerate(df.columns, 1):
                worksheet.column_dimensions[chr(64 + idx)].width = 20
        
        output.seek(0)
        return output.getvalue()


# 全局实例
knowledge_service = KnowledgeService()

