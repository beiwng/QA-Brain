"""
LLM 服务封装
使用 LangChain 调用私有化大模型
"""
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from backend.config import settings
from typing import Dict, Any, List, Optional


class LLMService:
    """大模型服务封装"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.LLM_API_KEY,
            openai_api_base=settings.LLM_BASE_URL,
            temperature=0.3,
            max_tokens=4096
        )

    async def analyze_bug(
            self,
            query: str,
            context_decisions: List[Dict] = None,
            context_bugs: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析 Bug 并生成报告 (融合决策与历史缺陷)
        """
        if context_decisions is None: context_decisions = []
        if context_bugs is None: context_bugs = []

        # 1. 构建“决策”上下文 (保持不变)
        decision_text = ""
        if context_decisions:
            decision_text = "\n\n### 📚 相关项目决策 (Policy Context)：\n"
            for d in context_decisions:
                decision_text += f"- [决策#{d.get('id')}] {d.get('title')}\n"
                decision_text += f"  结论: {d.get('verdict')}\n"
        else:
            decision_text = "\n\n### 📚 相关项目决策：\n(无相关记录)"

        # 2. 构建“历史缺陷”上下文 (✅ 已新增 impact_scope)
        bug_text = ""
        if context_bugs:
            bug_text = "\n\n### 🐞 相似历史缺陷 (Technical Context)：\n"
            for b in context_bugs:
                # 注意：b 是从 Milvus metadata 解析出来的字典
                bug_text += f"- [Bug#{b.get('id')}] {b.get('text')[:100]}...\n"
                bug_text += f"  根因: {b.get('root_cause', '无')}\n"
                bug_text += f"  解决: {b.get('solution', '无')}\n"
                # --- 新增 ---
                bug_text += f"  范围: {b.get('impact_scope', '未知')}\n"
        else:
            bug_text = "\n\n### 🐞 相似历史缺陷：\n(无相关记录)"

        # 3. 升级 System Prompt (✅ 引导 AI 关注影响范围)
        system_prompt = """你是 QA-Brain，一位资深的软件测试专家。
你的任务是基于检索到的【项目决策】和【历史缺陷】知识库，对用户提交的新 Bug 进行深度分析。

**严重程度判定原则**：
- 必须参考历史缺陷的【影响范围 (impact_scope)】。
- 若历史问题涉及核心业务或生产环境，本次分析应倾向于定级为 High/Critical。

**分析逻辑链**：
1. **策略检查**：查看决策库，确认是否为已知设计或豁免项。
2. **技术比对**：对比历史 Bug 的【根因】与【解决】，推断当前问题。
3. **综合定级**：结合【影响范围】给出严重程度。

**输出要求**：
- 输出格式必须为 Markdown。
- 引用知识库内容必须明确指出 ID。
"""

        user_prompt = f"""请分析以下待处理问题：

## 🐛 待分析问题描述
{query}

---
{decision_text}
---
{bug_text}
---

请输出 **Bug 分析报告** (Markdown)。
"""

        user_prompt = f"""请分析以下待处理问题：

        ## 🐛 待分析问题描述
        {query}

        ---
        {decision_text}
        ---
        {bug_text}
        ---

        请输出 **Bug 分析报告**，包含以下章节：
        1. **问题定性**：(是 Bug、需求问题、还是重复问题？)
        2. **严重程度**：(Blocker/Critical/Major/Minor)
        3. **智能根因推测**：(结合历史缺陷的根因进行推断)
        4. **修复建议**：(参考历史解决方案)
        5. **知识库引用**：(列出参考的决策 ID 或 历史 Bug ID)
        """

        # 调用 LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        response = await self.llm.ainvoke(messages)
        answer = response.content

        # 提取严重程度
        severity = self._extract_severity(answer)

        # 提取所有引用的 Source ID (用于前端展示引用来源)
        sources = []
        if context_decisions:
            sources.extend([f"决策#{d.get('id')}" for d in context_decisions])
        if context_bugs:
            sources.extend([f"Bug#{b.get('id')}" for b in context_bugs])

        return {
            "answer": answer,
            "severity": severity,
            "sources": sources
        }

    def _extract_severity(self, text: str) -> str:
        """从 LLM 输出中提取严重程度"""
        severity_keywords = ["Blocker", "Critical", "Major", "Minor", "Trivial"]
        for keyword in severity_keywords:
            if keyword in text:
                return keyword
        return "Major"  # 默认值

# 全局实例
llm_service = LLMService()

