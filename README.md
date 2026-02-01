# 🔮 NexusIntel 自动新闻更新系统

## 📋 项目概述

NexusIntel 是一个高端金融情报仪表盘，通过 **GitHub Actions + Gemini AI** 实现每日自动新闻分析和数据更新。

### 核心架构

```
┌─────────────────┐
│  每日 00:00 UTC │ ──► GitHub Actions 触发
└─────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  update_news.py 执行流程    │
│  1. 抓取财经/科技新闻       │
│  2. Gemini API 深度分析     │
│  3. 生成 data.json          │
└─────────────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  前端 React 应用读取        │
│  动态显示最新情报           │
└─────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境准备

#### 安装依赖
```bash
pip install -r requirements.txt
```

#### 设置环境变量
```bash
# Linux/Mac
export GEMINI_API_KEY="your_gemini_api_key_here"
export NEWS_API_KEY="your_newsapi_key_here"  # 可选

# Windows
set GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. 本地测试

```bash
# 运行脚本
python update_news.py

# 检查输出
cat public/data.json
```

### 3. GitHub 部署

#### 步骤 1：添加 Secret

在 GitHub 仓库设置中添加：
- `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
  - **Name**: `GEMINI_API_KEY`
  - **Value**: 你的 Gemini API Key

#### 步骤 2：推送代码

```bash
git add .
git commit -m "Add auto-update system"
git push origin main
```

#### 步骤 3：手动触发测试

- 进入 `Actions` 标签页
- 选择 `Update NexusIntel News Data` workflow
- 点击 `Run workflow`

---

## 📂 文件结构

```
NexusIntel/
├── update_news.py              # 核心更新脚本
├── requirements.txt            # Python 依赖
├── .github/
│   └── workflows/
│       └── update-news.yml     # GitHub Actions 配置
├── public/
│   └── data.json               # 生成的数据文件（自动）
├── src/
│   └── App.jsx                 # React 前端（需修改）
└── README.md                   # 本文档
```

---

## 🔧 配置选项

### update_news.py 配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `NEWS_COUNT` | 10 | 每次生成的新闻数量 |
| `OUTPUT_PATH` | `public/data.json` | 输出文件路径 |
| `IMAGE_KEYWORDS` | 预设列表 | Unsplash 图片关键词 |

### GitHub Actions 配置

修改 `.github/workflows/update-news.yml` 中的 cron 表达式：

```yaml
schedule:
  # 每天 00:00 UTC
  - cron: '0 0 * * *'
  
  # 每12小时一次
  # - cron: '0 */12 * * *'
  
  # 工作日 09:00 UTC
  # - cron: '0 9 * * 1-5'
```

---

## 🎨 前端集成

### 修改 App.jsx

替换硬编码数据为动态加载：

```jsx
// 原代码
const intelData = getIntelData(lang);

// 新代码
const [intelData, setIntelData] = useState([]);
const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  fetch('/data.json')
    .then(res => res.json())
    .then(json => {
      setIntelData(json.languages[lang] || []);
      setIsLoading(false);
    })
    .catch(err => {
      console.error('Failed to load data:', err);
      setIntelData(getIntelData(lang)); // 降级到本地数据
      setIsLoading(false);
    });
}, [lang]);
```

完整示例见 `FRONTEND_INTEGRATION.js`

---

## 🧪 数据结构验证

生成的 `data.json` 结构：

```json
{
  "generated_at": "2025-01-31T12:00:00",
  "version": "1.0",
  "languages": {
    "zh": [
      {
        "id": "NEX-8820",
        "image": "https://images.unsplash.com/...",
        "title": "量子霸权：欧盟突破",
        "fullTitle": "量子霸权：欧盟 Project Enigma 算力突破",
        "classification": "TOP SECRET",
        "impactLevel": "CRITICAL",
        "summary": "欧盟秘密量子计算项目成功破解...",
        "relations": [
          {
            "label": "欧盟委员会",
            "type": "entity",
            "desc": "行政机构"
          }
        ],
        "analysis": {
          "strategic": [
            "地缘洗牌：欧盟掌握核按钮",
            "军备竞赛：美中俄启动对抗"
          ]
        },
        "investment": {
          "action": "LONG",
          "asset": "IBM / GOOGL",
          "risk": "HIGH",
          "thesis": "抗量子加密技术将迎来资本涌入"
        },
        "confidence": 96
      }
    ],
    "en": [...],
    "es": [...]
  }
}
```

---

## 🐛 故障排查

### 问题 1：Gemini API 调用失败

**症状**：
```
❌ Gemini API 调用失败: 403 Permission Denied
```

**解决方案**：
1. 检查 API Key 是否正确设置
2. 确认 Gemini API 已启用（访问 [Google AI Studio](https://aistudio.google.com/app/apikey)）
3. 检查 API 配额是否用尽

### 问题 2：JSON 解析失败

**症状**：
```
❌ JSON 解析失败: Expecting value: line 1 column 1
```

**解决方案**：
- Gemini 返回格式不正确
- 修改 `_build_analysis_prompt` 中的 Prompt，强调 "直接返回 JSON，不要添加任何文字"

### 问题 3：GitHub Actions 权限不足

**症状**：
```
! [remote rejected] main -> main (refusing to allow a GitHub App to create or update workflow)
```

**解决方案**：
1. 进入 `Settings` → `Actions` → `General`
2. 选择 `Workflow permissions` → `Read and write permissions`
3. 勾选 `Allow GitHub Actions to create and approve pull requests`

---

## 📊 性能优化

### 1. 缓存策略

在前端添加缓存：

```jsx
const CACHE_DURATION = 1000 * 60 * 60; // 1小时

const getCachedData = () => {
  const cached = localStorage.getItem('nexus_data');
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  return null;
};

const setCachedData = (data) => {
  localStorage.setItem('nexus_data', JSON.stringify({
    data,
    timestamp: Date.now()
  }));
};
```

### 2. 增量更新

修改脚本只更新变化的数据：

```python
# 读取现有数据
try:
    with open(OUTPUT_PATH, 'r') as f:
        old_data = json.load(f)
except:
    old_data = {}

# 合并新旧数据
new_data = {
    "generated_at": datetime.now().isoformat(),
    "previous_update": old_data.get("generated_at"),
    "languages": all_data
}
```

---

## 🛡️ 安全建议

1. **API Key 保护**
   - ❌ 不要将 API Key 提交到代码仓库
   - ✅ 使用 GitHub Secrets
   - ✅ 本地使用 `.env` 文件（添加到 `.gitignore`）

2. **数据验证**
   ```python
   # 在脚本中添加数据验证
   def validate_output(data):
       required_fields = ['id', 'title', 'summary', ...]
       for item in data:
           if not all(field in item for field in required_fields):
               raise ValueError(f"Missing fields in {item.get('id')}")
   ```

3. **错误处理**
   - 添加重试机制
   - 失败时发送通知（GitHub Issues / Email）

---

## 📝 TODO

- [ ] 添加更多新闻源（Bloomberg API, Reuters API）
- [ ] 实现多模型支持（GPT-4, Claude）
- [ ] 添加新闻去重逻辑
- [ ] 实现数据历史版本管理
- [ ] 添加自动测试（pytest）
- [ ] 创建管理后台界面

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目使用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📧 联系方式

- 作者：Jeremy
- 学校：Abington Friends School
- 项目：AlphaTerminal / NexusIntel

---

## 🙏 致谢

- Google Gemini API
- Unsplash 图片服务
- React + Tailwind CSS 社区
