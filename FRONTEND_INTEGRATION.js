/**
 * NexusIntel 前端代码修改指南
 * 从硬编码数据切换到 data.json 动态加载
 */

// ============== 修改方案 1：替换 getIntelData 函数 ==============

// 原代码（硬编码）：
// const getIntelData = (lang) => [
//   { id: "NEX-8821", ... },
//   { id: "NEX-8822", ... }
// ];

// 新代码（动态加载）：
const [intelData, setIntelData] = useState([]);
const [isLoading, setIsLoading] = useState(true);

useEffect(() => {
  const loadData = async () => {
    try {
      const response = await fetch('/data.json');
      const json = await response.json();
      
      // 根据当前语言选择对应数据
      const langData = json.languages[lang] || json.languages['en'];
      setIntelData(langData);
      setIsLoading(false);
    } catch (error) {
      console.error('Failed to load news data:', error);
      // 降级到本地备份数据
      setIntelData(FALLBACK_DATA);
      setIsLoading(false);
    }
  };
  
  loadData();
}, [lang]);


// ============== 修改方案 2：在 Main Component 中添加加载状态 ==============

export default function NexusIntel() {
  const [booted, setBooted] = useState(false);
  const [selectedIntel, setSelectedIntel] = useState(null);
  const [viewMode, setViewMode] = useState('news');
  const [lang, setLang] = useState('zh');
  
  // 新增：数据加载状态
  const [intelData, setIntelData] = useState([]);
  const [isDataLoading, setIsDataLoading] = useState(true);
  
  // 新增：数据加载 Effect
  useEffect(() => {
    const fetchNewsData = async () => {
      try {
        const response = await fetch('/data.json');
        const json = await response.json();
        setIntelData(json.languages[lang] || []);
      } catch (error) {
        console.error('Data load failed:', error);
        // 使用降级数据
        setIntelData(getIntelData(lang)); // 原硬编码函数作为备份
      } finally {
        setIsDataLoading(false);
      }
    };
    
    fetchNewsData();
  }, [lang]); // 语言切换时重新加载
  
  // 修改原来的渲染逻辑
  const t = LANG_CONFIG[lang];
  
  if (!booted) return <BootSequence onComplete={() => setBooted(true)} lang={lang} />;
  
  // 新增：数据加载中显示
  if (isDataLoading) {
    return (
      <div className="fixed inset-0 bg-[#080808] flex items-center justify-center">
        <div className="text-[#C6A87C] text-sm animate-pulse">LOADING INTELLIGENCE...</div>
      </div>
    );
  }
  
  // 后续使用 intelData 替换原来的 getIntelData(lang)
  return (
    <div className="fixed inset-0 bg-[#080808]...">
      {/* ... */}
      {viewMode === 'network' && (
        <NetworkGraph data={intelData} onNodeClick={...} />
      )}
      {viewMode === 'news' && (
        <NewsFeed data={intelData} onSelect={...} t={t} lang={lang} />
      )}
      {viewMode === 'invest' && (
        <InvestmentTerminal data={intelData} t={t} />
      )}
    </div>
  );
}


// ============== 修改方案 3：添加数据刷新功能 ==============

const RefreshButton = ({ onRefresh, isRefreshing }) => (
  <button 
    onClick={onRefresh}
    disabled={isRefreshing}
    className="p-3 rounded-lg transition-all text-[#555] hover:text-[#C6A87C]"
  >
    <RefreshCw size={20} className={isRefreshing ? 'animate-spin' : ''} />
  </button>
);

// 在主组件中添加刷新逻辑
const handleRefresh = async () => {
  setIsDataLoading(true);
  try {
    // 添加时间戳避免缓存
    const response = await fetch(`/data.json?t=${Date.now()}`);
    const json = await response.json();
    setIntelData(json.languages[lang] || []);
  } catch (error) {
    console.error('Refresh failed:', error);
  } finally {
    setIsDataLoading(false);
  }
};


// ============== 数据结构验证 ==============

// 在加载数据后验证结构完整性
const validateDataStructure = (data) => {
  const requiredFields = [
    'id', 'title', 'fullTitle', 'classification', 
    'impactLevel', 'summary', 'relations', 'analysis', 
    'investment', 'confidence'
  ];
  
  return data.every(item => 
    requiredFields.every(field => field in item)
  );
};

// 使用示例
useEffect(() => {
  const loadData = async () => {
    const response = await fetch('/data.json');
    const json = await response.json();
    const langData = json.languages[lang];
    
    if (validateDataStructure(langData)) {
      setIntelData(langData);
    } else {
      console.error('Invalid data structure');
      setIntelData(FALLBACK_DATA);
    }
    setIsDataLoading(false);
  };
  
  loadData();
}, [lang]);


// ============== 环境变量配置（可选）==============

// vite.config.js
export default defineConfig({
  // ...其他配置
  define: {
    __DATA_SOURCE__: JSON.stringify(
      process.env.NODE_ENV === 'production' 
        ? '/data.json'  // 生产环境使用自动生成的数据
        : '/data-dev.json'  // 开发环境使用本地数据
    )
  }
});

// 在代码中使用
const DATA_URL = __DATA_SOURCE__;
const response = await fetch(DATA_URL);
