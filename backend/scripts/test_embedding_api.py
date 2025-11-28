"""
测试 Embedding API 的请求格式
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import httpx
from backend.config import settings


async def test_embedding_formats():
    """测试不同的 Embedding API 请求格式"""

    test_text = "这是一个测试文本"

    print(f"🔍 测试 Embedding API: {settings.EMBEDDING_API_URL}")
    print(f"📝 测试文本: {test_text}")
    print(f"🤖 模型名称: {settings.EMBEDDING_MODEL_NAME}\n")

    # 测试格式 0: OpenAI 兼容格式（优先）
    print("=" * 60)
    print("测试格式 0 (OpenAI 兼容): {'input': 'text', 'model': '...', 'encoding_format': 'float'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={
                    "input": test_text,
                    "model": settings.EMBEDDING_MODEL_NAME,
                    "encoding_format": "float"
                }
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                if "data" in data and len(data["data"]) > 0:
                    embedding = data["data"][0].get("embedding", [])
                    print(f"✅ Embedding 维度: {len(embedding)}")
                    print(f"✅ 前 5 个值: {embedding[:5]}")
                print(f"响应示例: {str(data)[:300]}...")
                return "openai_format"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:500]}")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 测试格式 1: {"input": "text"}
    print("\n" + "=" * 60)
    print("测试格式 1: {'input': 'text'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"input": test_text}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format1"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试格式 2: {"text": "text"}
    print("\n" + "=" * 60)
    print("测试格式 2: {'text': 'text'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"text": test_text}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format2"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试格式 3: {"texts": ["text"]}
    print("\n" + "=" * 60)
    print("测试格式 3: {'texts': ['text']}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"texts": [test_text]}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format3"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试格式 4: {"inputs": "text"}
    print("\n" + "=" * 60)
    print("测试格式 4: {'inputs': 'text'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"inputs": test_text}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format4"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试格式 5: {"prompt": "text"}
    print("\n" + "=" * 60)
    print("测试格式 5: {'prompt': 'text'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"prompt": test_text}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format5"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试格式 6: {"content": "text"}
    print("\n" + "=" * 60)
    print("测试格式 6: {'content': 'text'}")
    print("=" * 60)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                settings.EMBEDDING_API_URL,
                json={"content": test_text}
            )
            print(f"状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 成功！响应格式: {list(data.keys())}")
                print(f"响应示例: {str(data)[:200]}...")
                return "format6"
            else:
                print(f"❌ 失败: {response.status_code}")
                print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("❌ 所有格式测试失败！")
    print("=" * 60)
    print("\n建议：")
    print("1. 检查 Embedding API 是否正常运行")
    print("2. 检查 API URL 是否正确")
    print("3. 查看 Embedding API 的文档，确认请求格式")
    print("4. 尝试使用 curl 或 Postman 手动测试 API")
    
    return None


async def main():
    """主函数"""
    result = await test_embedding_formats()
    
    if result:
        print(f"\n\n🎉 找到正确的格式: {result}")
        print("\n请根据测试结果修改 backend/utils/vector_service.py 中的 get_embedding 方法")
    else:
        print("\n\n❌ 未找到正确的格式，请检查 Embedding API")


if __name__ == "__main__":
    asyncio.run(main())

