# 🚀 NexusIntel 完整设置指南

## 📋 目录
1. [获取 API Keys](#1-获取-api-keys)
2. [本地环境配置](#2-本地环境配置)
3. [测试运行](#3-测试运行)
4. [GitHub 部署](#4-github-部署)
5. [前端集成](#5-前端集成)
6. [常见问题](#6-常见问题)

---

## 1. 获取 API Keys

### 1.1 Gemini API Key（必需）

1. **访问 Google AI Studio**
   - 网址：https://aistudio.google.com/app/apikey
   - 使用 Google 账号登录

2. **创建 API Key**
   - 点击 "Create API Key"
   - 选择现有项目或创建新项目
   - 复制生成的 API Key（格式：`AIza...`）

3. **验证 API 可用性**
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"
   ```

### 1.2 NewsAPI Key（可选）

1. **注册账号**
   - 网址：https://newsapi.org/register
   - 填写基本信息

2. **获取免费 API Key**
   - 免费计划：每天 100 次请求
   - 复制 API Key

3. **如果不使用 NewsAPI**
   - 脚本会自动使用免费的 RSS Feed
   - 无需额外配置

---

## 2. 本地环境配置

### 2.1 安装 Python

**检查 Python 版本**（需要 3.9+）
```bash
python --version
# 或
python3 --version
```

**安装 Python**（如果未安装）
- **Mac**: `brew install python3`
- **Windows**: 下载安装程序 https://www.python.org/downloads/
- **Linux**: `sudo apt-get install python3 python3-pip`

### 2.2 克隆/下载项目

```bash
# 如果已有 Git 仓库
git clone https://github.com/your-username/nexusintel.git
cd nexusintel

# 或直接创建目录
mkdir nexusintel
cd nexusintel
```

### 2.3 安装依赖

```bash
pip install -r requirements.txt

# 如果遇到权限问题
pip install --user -r requirements.txt

# 或使用 Python 3 的 pip
pip3 install -r requirements.txt
```

### 2.4 设置环境变量

**Linux/Mac**
```bash
# 临时设置（仅当前终端有效）
export GEMINI_API_KEY="AIza..."
export NEWS_API_KEY="your_newsapi_key"  # 可选

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export GEMINI_API_KEY="AIza..."' >> ~/.bashrc
source ~/.bashrc
```

**Windows (PowerShell)**
```powershell
# 临时设置
$env:GEMINI_API_KEY="AIza..."
$env:NEWS_API_KEY="your_newsapi_key"

# 永久设置
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'AIza...', 'User')
```

**使用 .env 文件（推荐）**
```bash
# 创建 .env 文件
cat > .env << EOF
GEMINI_API_KEY=AIza...
NEWS_API_KEY=your_newsapi_key
EOF

# 修改脚本加载 .env（在 update_news.py 顶部添加）
from dotenv import load_dotenv
load_dotenv()

# 安装 python-dotenv
pip install python-dotenv
```

---

## 3. 测试运行

### 3.1 运行测试脚本

```bash
python test_system.py
```

**预期输出：**
```
====================================================================
🔮 NEXUS INTEL 系统测试
====================================================================
📦 测试依赖包...
  ✅ requests
  ✅ google-generativeai
  ✅ feedparser
...
总计：5/5 测试通过
🎉 所有测试通过！系统已就绪
```

### 3.2 运行主脚本

```bash
python update_news.py
```

**成功标志：**
```
====================================================================
🔮 NEXUS INTEL 新闻自动更新系统
====================================================================

📡 抓取新闻源...
✅ 成功获取 10 条新闻

🌐 生成 zh 语言数据...
🤖 正在调用 Gemini API 分析 10 条新闻...
✅ 成功生成 10 条情报数据

✅ 数据已保存到 public/data.json
```

### 3.3 验证输出

```bash
# 检查文件是否生成
ls -lh public/data.json

# 查看生成的数据
cat public/data.json | head -50

# 验证 JSON 格式
python -m json.tool public/data.json > /dev/null && echo "✅ JSON 格式正确"
```

---

## 4. GitHub 部署

### 4.1 创建 GitHub 仓库

1. **在 GitHub 上创建新仓库**
   - 访问：https://github.com/new
   - 仓库名：`nexusintel`
   - 可见性：Public 或 Private

2. **推送代码**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: NexusIntel auto-update system"
   git branch -M main
   git remote add origin https://github.com/your-username/nexusintel.git
   git push -u origin main
   ```

### 4.2 配置 GitHub Secrets

1. **进入仓库设置**
   - 仓库页面 → `Settings` → `Secrets and variables` → `Actions`

2. **添加 Secret**
   - 点击 `New repository secret`
   - **Name**: `GEMINI_API_KEY`
   - **Value**: 你的 Gemini API Key
   - 点击 `Add secret`

3. **（可选）添加 NewsAPI Secret**
   - 重复上述步骤
   - **Name**: `NEWS_API_KEY`
   - **Value**: 你的 NewsAPI Key

### 4.3 配置 Actions 权限

1. **启用 Workflow 权限**
   - `Settings` → `Actions` → `General`
   - 找到 "Workflow permissions"
   - 选择 **"Read and write permissions"**
   - 勾选 **"Allow GitHub Actions to create and approve pull requests"**
   - 点击 `Save`

### 4.4 手动触发第一次运行

1. **进入 Actions 页面**
   - 仓库页面 → `Actions` 标签

2. **选择 Workflow**
   - 左侧选择 `Update NexusIntel News Data`

3. **手动运行**
   - 点击右侧 `Run workflow` 按钮
   - 选择分支（main）
   - 点击绿色 `Run workflow` 按钮

4. **查看运行结果**
   - 等待约 1-2 分钟
   - 点击运行记录查看日志
   - 确认 ✅ 所有步骤通过

### 4.5 验证自动提交

```bash
# 拉取最新更改
git pull origin main

# 查看 data.json 是否更新
git log --oneline public/data.json

# 应该看到类似的提交：
# a1b2c3d 🤖 Auto-update: 2025-01-31 12:00 UTC
```

---

## 5. 前端集成

### 5.1 修改 React 代码

**在 `src/App.jsx` 中找到：**
```jsx
const intelData = getIntelData(lang);
```

**替换为：**
```jsx
const [intelData, setIntelData] = useState([]);
const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  const loadData = async () => {
    try {
      const response = await fetch('/data.json');
      const json = await response.json();
      setIntelData(json.languages[lang] || []);
    } catch (error) {
      console.error('Failed to load data:', error);
      // 降级到本地硬编码数据
      setIntelData(getIntelData(lang));
    } finally {
      setIsLoading(false);
    }
  };
  
  loadData();
}, [lang]);
```

### 5.2 添加加载状态

```jsx
if (isLoading) {
  return (
    <div className="fixed inset-0 bg-[#080808] flex items-center justify-center">
      <div className="text-[#C6A87C] text-sm animate-pulse">
        LOADING INTELLIGENCE...
      </div>
    </div>
  );
}
```

### 5.3 测试前端

```bash
# 启动开发服务器
npm run dev

# 打开浏览器访问
# http://localhost:5173
```

**验证要点：**
- ✅ 页面正常加载
- ✅ 新闻数据显示（来自 data.json）
- ✅ 语言切换正常工作
- ✅ 所有字段完整（标题、摘要、分析、投资建议）

---

## 6. 常见问题

### Q1: Gemini API 返回 403 错误

**原因：**
- API Key 无效或过期
- API 未启用

**解决方案：**
```bash
# 验证 API Key
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}'

# 检查是否启用了 Generative Language API
# 访问：https://console.cloud.google.com/apis/library
```

### Q2: JSON 解析失败

**症状：**
```
❌ JSON 解析失败: Expecting value: line 1 column 1
```

**解决方案：**
1. 检查 Gemini 返回内容（查看脚本输出）
2. 可能需要调整 Prompt，强调 "只返回 JSON"
3. 尝试提取 ```json ... ``` 代码块

**临时修复（在 update_news.py 中）：**
```python
# 在 analyze_batch 方法中添加更强的提取逻辑
result_text = response.text
if "```json" in result_text:
    # 提取 JSON 代码块
    result_text = result_text.split("```json")[1].split("```")[0]
elif "```" in result_text:
    result_text = result_text.split("```")[1].split("```")[0]

# 移除可能的前缀文字
result_text = result_text.strip()
if not result_text.startswith('['):
    # 找到第一个 [ 开始位置
    start_idx = result_text.find('[')
    if start_idx != -1:
        result_text = result_text[start_idx:]
```

### Q3: GitHub Actions 权限错误

**症状：**
```
remote: Permission to user/repo.git denied to github-actions[bot]
```

**解决方案：**
1. 确认 Workflow permissions 设置为 "Read and write"
2. 检查仓库是否启用了分支保护
3. 如果仍失败，使用 Personal Access Token（不推荐）

### Q4: 前端无法加载 data.json

**症状：**
- 控制台显示 404 错误
- 数据未显示

**解决方案：**
```bash
# 确保文件在正确位置
ls public/data.json

# Vite 开发服务器应该自动服务 public/ 目录
# 如果使用其他打包工具，确认静态文件配置

# 测试文件可访问性
curl http://localhost:5173/data.json
```

### Q5: 新闻源抓取失败

**症状：**
```
⚠️ RSS 源抓取失败
```

**解决方案：**
1. 检查网络连接
2. 某些 RSS 源可能被墙（使用代理）
3. 降级到模拟数据：
   ```python
   articles = NewsSource._generate_mock_news(NEWS_COUNT)
   ```

### Q6: 数据质量不佳

**问题：**
- AI 生成的分析太泛
- 投资建议不够具体
- 语言不够专业

**解决方案：**
优化 Prompt（修改 `_build_analysis_prompt` 方法）：

```python
prompt = f"""你是华尔街顶级分析师 + 调查记者的融合体。

分析风格要求：
1. 战略分析必须具体、尖锐、有洞察力（避免废话）
2. 投资建议必须包含具体标的、明确风险、清晰逻辑
3. 语言风格：《经济学人》+ 《彭博商业周刊》
4. 避免使用陈词滥调（如"未来可期"、"值得关注"）

示例对比：
❌ 差："这个事件可能会影响市场"
✅ 好："美联储被迫提前降息50个基点，黄金将突破3000美元"

现在分析以下新闻：
{news_list}
"""
```

---

## 🎯 下一步

配置完成后，你可以：

1. **自定义更新频率**
   - 修改 `.github/workflows/update-news.yml` 中的 cron 表达式

2. **添加数据验证**
   - 在脚本中添加质量检查逻辑
   - 自动过滤低质量数据

3. **实现多模型支持**
   - 同时使用 Gemini + GPT-4 + Claude
   - 对比结果取最优

4. **添加监控告警**
   - 失败时发送邮件/Slack 通知
   - 使用 GitHub Issues 跟踪错误

5. **构建数据历史**
   - 每次保存旧数据到 `archive/` 目录
   - 实现时间线回溯功能

---

## 📞 获取帮助

遇到问题？

1. 查看脚本输出日志（详细错误信息）
2. 运行 `python test_system.py` 诊断
3. 查看 GitHub Actions 运行日志
4. 提交 Issue 到仓库

祝你使用愉快！🚀
