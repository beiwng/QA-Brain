"""
LangGraph RAG Workflow
实现 Retrieve -> Grade -> Generate 的智能分析流程
"""
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from backend.utils.vector_service import vector_service
from backend.utils.llm_service import llm_service


# === State Definition ===
class AgentState(TypedDict):
    """Agent 状态定义"""
    query: str  # 用户输入
    retrieved_decisions: List[Dict[str, Any]]  # 检索到的决策 (Policy)
    retrieved_bugs: List[Dict[str, Any]]  # 检索到的历史缺陷 (Technical) - ✅ 新增
    relevance_score: float  # 相关性评分
    final_answer: str  # 最终答案
    severity: str  # 严重程度
    sources: List[str]  # 引用来源


# === Node Functions ===
async def retrieve_node(state: AgentState) -> AgentState:
    """
    节点 1: 检索 (Retrieve)
    从向量库中通用检索，并分类为决策和缺陷
    """
    query = state["query"]
    print(f"🔍 [Retrieve] Searching for: {query}")

    try:
        # ✅ 适配：调用新的通用检索接口
        # top_k 稍微大一点，因为包含了两种类型的数据
        documents = await vector_service.search_similar(query, top_k=10)

        decisions = []
        bugs = []

        # ✅ 适配：根据 source_type 拆分数据
        for doc in documents:
            source = doc.get("source_type", "")
            if source == "decision":
                decisions.append(doc)
            elif source == "bug_history":
                bugs.append(doc)

        print(f"✅ [Retrieve] Found {len(decisions)} decisions, {len(bugs)} bugs")

        # 返回状态更新
        return {
            "retrieved_decisions": decisions,
            "retrieved_bugs": bugs
        }

    except Exception as e:
        print(f"❌ [Retrieve] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "retrieved_decisions": [],
            "retrieved_bugs": []
        }


async def grade_node(state: AgentState) -> AgentState:
    """
    节点 2: 评估相关性
    判断检索结果是否足够相关（最大值策略）
    """
    decisions = state.get("retrieved_decisions", [])
    bugs = state.get("retrieved_bugs", [])

    # 合并所有文档计算最高分
    all_docs = decisions + bugs

    if not all_docs:
        state["relevance_score"] = 0.0
        print("⚠️ [Grade] No documents found, relevance = 0.0")
        return state

    # ✅ 适配：取最大分，只要有一条命中即可
    max_score = max(d.get("score", 0.0) for d in all_docs)
    state["relevance_score"] = max_score

    print(f"📊 [Grade] Max relevance score: {max_score:.2f}")

    return state


async def generate_node(state: AgentState) -> AgentState:
    """
    节点 3: 生成答案
    调用 LLM 生成专业的 Bug 分析报告
    """
    query = state["query"]
    decisions = state.get("retrieved_decisions", [])
    bugs = state.get("retrieved_bugs", [])
    relevance = state["relevance_score"]

    # 相关性阈值判断 (IP/Cosine 通常 0.35-0.4 算相关)
    RELEVANCE_THRESHOLD = 0.4

    if relevance < RELEVANCE_THRESHOLD:
        print(f"⚠️ [Generate] Relevance too low ({relevance:.2f} < {RELEVANCE_THRESHOLD}), returning fallback")
        state["final_answer"] = """## ⚠️ 知识库资料不足

很抱歉，QA-Brain 在历史决策库或缺陷库中未找到与此问题高度相关的记录。

**建议**：
1. 请提供更详细的错误日志或复现步骤
2. 咨询团队中的资深工程师
3. 若确认为新问题，请及时录入知识库
"""
        state["severity"] = "Major"
        state["sources"] = []
        return state

    # 调用 LLM 生成分析
    print(f"🤖 [Generate] Calling LLM for analysis...")
    try:
        # ✅ 适配：传入双流上下文 (决策 + Bug)
        result = await llm_service.analyze_bug(
            query=query,
            context_decisions=decisions,
            context_bugs=bugs
        )

        state["final_answer"] = result["answer"]
        state["severity"] = result["severity"]
        state["sources"] = result["sources"]

        print(f"✅ [Generate] Analysis complete (Severity: {result['severity']})")

    except Exception as e:
        print(f"❌ [Generate] LLM error: {e}")
        import traceback
        traceback.print_exc()

        state["final_answer"] = f"## ❌ 分析失败\n\n系统错误: {str(e)}"
        state["severity"] = "Major"
        state["sources"] = []

    return state


# === Build Graph ===
def build_graph() -> StateGraph:
    """构建 LangGraph 工作流"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade", grade_node)
    workflow.add_node("generate", generate_node)

    # 定义边
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade")
    workflow.add_edge("grade", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()


# === Main Entry ===
async def analyze_bug_with_graph(query: str) -> Dict[str, Any]:
    """
    主入口：使用 LangGraph 分析 Bug
    """
    print(f"\n{'=' * 60}")
    print(f"🧠 QA-Brain Analysis Started: {query}")
    print(f"{'=' * 60}\n")

    # 初始化状态
    initial_state: AgentState = {
        "query": query,
        "retrieved_decisions": [],
        "retrieved_bugs": [],  # ✅ 初始化为空列表
        "relevance_score": 0.0,
        "final_answer": "",
        "severity": "Major",
        "sources": []
    }

    try:
        # 运行 Graph
        app = build_graph()
        final_state = await app.ainvoke(initial_state)

        print(f"\n{'=' * 60}")
        print(f"✅ QA-Brain Analysis Completed")
        print(f"{'=' * 60}\n")

        return {
            "answer": final_state["final_answer"],
            "severity": final_state["severity"],
            "sources": final_state["sources"]
        }
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()
        # 兜底返回
        return {
            "answer": f"系统运行错误: {str(e)}",
            "severity": "Major",
            "sources": []
        }