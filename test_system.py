#!/usr/bin/env python3
"""
NexusIntel 快速测试脚本
验证环境配置和数据生成功能
"""

import sys
import os
from dotenv import load_dotenv 

load_dotenv() 

def test_dependencies():
    """测试依赖安装"""
    print("📦 测试依赖包...")
    
    required = {
        'requests': 'requests',
        'google.generativeai': 'google-generativeai',
        'feedparser': 'feedparser'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n💡 安装缺失包：pip install {' '.join(missing)}")
        return False
    return True


def test_api_key():
    """测试 API Key"""
    print("\n🔑 测试 API Key...")
    
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    if gemini_key:
        print(f"  ✅ GEMINI_API_KEY 已设置 ({gemini_key[:10]}...)")
    else:
        print(f"  ❌ GEMINI_API_KEY 未设置")
        print(f"     运行：export GEMINI_API_KEY='your_key_here'")
        return False
    
    news_key = os.environ.get("NEWS_API_KEY", "")
    if news_key:
        print(f"  ✅ NEWS_API_KEY 已设置（可选）")
    else:
        print(f"  ⚠️  NEWS_API_KEY 未设置（将使用 RSS 源）")
    
    return True


def test_gemini_connection():
    """测试 Gemini API 连接"""
    print("\n🤖 测试 Gemini API 连接...")
    
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("  ⏭️  跳过（API Key 未设置）")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        response = model.generate_content("Say 'Hello NexusIntel'")
        print(f"  ✅ API 响应：{response.text[:50]}...")
        return True
        
    except Exception as e:
        print(f"  ❌ 连接失败：{e}")
        return False


def test_json_output():
    """测试 JSON 生成"""
    print("\n📄 测试 JSON 输出...")
    
    try:
        import json
        
        sample_data = {
            "id": "TEST-001",
            "title": "测试新闻",
            "fullTitle": "测试新闻完整标题",
            "classification": "UNCLASSIFIED",
            "impactLevel": "INFO",
            "summary": "这是一条测试数据",
            "relations": [
                {"label": "测试实体", "type": "entity", "desc": "测试"}
            ],
            "analysis": {
                "strategic": ["测试分析1", "测试分析2"]
            },
            "investment": {
                "action": "LONG",
                "asset": "TEST",
                "risk": "LOW",
                "thesis": "测试投资逻辑"
            },
            "confidence": 85
        }
        
        # 验证 JSON 序列化
        json_str = json.dumps([sample_data], ensure_ascii=False, indent=2)
        print(f"  ✅ JSON 序列化成功")
        print(f"  📊 示例数据大小：{len(json_str)} 字节")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 测试失败：{e}")
        return False


def test_directory_structure():
    """测试目录结构"""
    print("\n📁 检查目录结构...")
    
    required_files = [
        'update_news.py',
        'requirements.txt',
        '.github/workflows/update-news.yml'
    ]
    
    for filepath in required_files:
        if os.path.exists(filepath):
            print(f"  ✅ {filepath}")
        else:
            print(f"  ❌ {filepath} - 未找到")
    
    # 检查输出目录
    if not os.path.exists('public'):
        print(f"  ⚠️  public/ 目录不存在，将自动创建")
        os.makedirs('public', exist_ok=True)
    else:
        print(f"  ✅ public/ 目录")
    
    return True


def main():
    """主测试流程"""
    print("=" * 60)
    print("🔮 NEXUS INTEL 系统测试")
    print("=" * 60)
    
    tests = [
        ("依赖检查", test_dependencies),
        ("API Key 验证", test_api_key),
        ("Gemini 连接", test_gemini_connection),
        ("JSON 生成", test_json_output),
        ("目录结构", test_directory_structure)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 测试出错：{e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name:20s} {status}")
    
    print(f"\n总计：{passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统已就绪")
        print("\n▶️  运行主脚本：python update_news.py")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())
