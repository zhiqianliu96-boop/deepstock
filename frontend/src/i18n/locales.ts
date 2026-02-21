export type Locale = 'en' | 'zh';

export type TranslationKey = keyof typeof en;

const en = {
  // Nav
  'nav.dashboard': 'Dashboard',
  'nav.history': 'History',
  'nav.settings': 'Settings',

  // Dashboard
  'dashboard.title': 'DeepStock',
  'dashboard.subtitle': 'Data First, AI Second — Quantitative Stock Analysis',
  'dashboard.running': 'Running deep analysis...',
  'dashboard.running_sub': 'Computing fundamentals, technicals, and sentiment in parallel',
  'dashboard.pillar_scores': 'Pillar Scores',
  'dashboard.radar_title': 'Multi-Dimension Radar',
  'dashboard.key_risks': 'Key Risks',
  'dashboard.catalysts': 'Catalysts',
  'dashboard.position_advice': 'Position Advice',
  'dashboard.ai_interpretation': 'AI Interpretation',

  // Tabs
  'tab.fundamental': 'Fundamental',
  'tab.technical': 'Technical',
  'tab.sentiment': 'Sentiment',

  // Search
  'search.placeholder': 'Enter stock code (600519, AAPL, 00700...)',
  'search.analyze': 'Analyze',
  'search.analyzing': 'Analyzing...',

  // Verdict
  'verdict.strong_buy': 'STRONG BUY',
  'verdict.buy': 'BUY',
  'verdict.hold': 'HOLD',
  'verdict.sell': 'SELL',
  'verdict.strong_sell': 'STRONG SELL',
  'verdict.composite': 'Composite',
  'verdict.confidence': 'Confidence',

  // Fundamental
  'fundamental.subscores': 'Fundamental Sub-scores',
  'fundamental.valuation': 'Valuation',
  'fundamental.profitability': 'Profitability',
  'fundamental.growth': 'Growth',
  'fundamental.health': 'Financial Health',
  'fundamental.key_ratios': 'Key Ratios',
  'fundamental.pe': 'P/E Ratio',
  'fundamental.pb': 'P/B Ratio',
  'fundamental.ps': 'P/S Ratio',
  'fundamental.peg': 'PEG',
  'fundamental.roe': 'ROE',
  'fundamental.roa': 'ROA',
  'fundamental.gross_margin': 'Gross Margin',
  'fundamental.net_margin': 'Net Margin',
  'fundamental.revenue_growth': 'Revenue Growth YoY',
  'fundamental.profit_growth': 'Profit Growth YoY',
  'fundamental.debt_equity': 'Debt/Equity',
  'fundamental.current_ratio': 'Current Ratio',
  'fundamental.fcf_yield': 'FCF Yield',
  'fundamental.eps': 'EPS',
  'fundamental.dividend_yield': 'Dividend Yield',
  'fundamental.market_cap': 'Market Cap',
  'fundamental.financial_trends': 'Financial Trends',
  'fundamental.company_profile': 'Company Profile',
  'fundamental.sector': 'Sector',
  'fundamental.industry': 'Industry',
  'fundamental.peer_comparison': 'Peer Comparison (Percentile)',

  // Technical
  'technical.subscores': 'Technical Sub-scores',
  'technical.trend': 'Trend',
  'technical.momentum': 'Momentum',
  'technical.volume': 'Volume',
  'technical.structure': 'Structure',
  'technical.pattern': 'Pattern',
  'technical.kline': 'K-Line Chart',
  'technical.kline_empty': 'Chart data not available',
  'technical.indicators': 'Key Indicators',
  'technical.sr': 'Support & Resistance',
  'technical.support': 'Support',
  'technical.resistance': 'Resistance',
  'technical.fund_flow': 'Institutional Fund Flow',
  'technical.classification': 'Classification',
  'technical.chip': 'Chip Distribution',
  'technical.profit_ratio': 'Profit Ratio',
  'technical.avg_cost': 'Avg Cost',
  'technical.concentration': 'Concentration',
  'technical.chip_health': 'Health',
  'technical.patterns': 'Pattern Alerts',

  // Sentiment
  'sentiment.subscores': 'Sentiment Sub-scores',
  'sentiment.news': 'News Sentiment',
  'sentiment.event': 'Event Impact',
  'sentiment.attention': 'Market Attention',
  'sentiment.quality': 'Source Quality',
  'sentiment.distribution': 'Sentiment Distribution',
  'sentiment.positive': 'Positive',
  'sentiment.neutral': 'Neutral',
  'sentiment.negative': 'Negative',
  'sentiment.categories': 'News Categories',
  'sentiment.articles': 'News Articles',
  'sentiment.no_articles': 'No news articles found. Set TAVILY_API_KEY in .env for news analysis.',

  // Charts
  'chart.no_kline': 'No K-Line chart data available',
  'chart.loading': 'Loading chart...',
  'chart.no_radar': 'No score data available for radar chart',
  'chart.no_financial': 'Financial chart data not available',
  'chart.revenue': 'Revenue',
  'chart.net_profit': 'Net Profit',
  'chart.gross_margin': 'Gross Margin %',
  'chart.net_margin': 'Net Margin %',

  // Radar indicators
  'radar.valuation': 'Valuation',
  'radar.profitability': 'Profitability',
  'radar.growth': 'Growth',
  'radar.trend': 'Trend',
  'radar.momentum': 'Momentum',
  'radar.sentiment': 'Sentiment',
  'radar.series_name': 'Score Analysis',

  // History
  'history.title': 'Analysis History',
  'history.empty': 'No analysis history yet. Run your first analysis from the dashboard.',
  'history.score': 'Score',

  // Settings
  'settings.title': 'Settings',
  'settings.ai_provider': 'AI Provider',
  'settings.ai_desc': 'Select which AI model to use for synthesis. Configure API keys in the backend .env file.',
  'settings.api_keys': 'API Keys',
  'settings.api_desc': 'API keys are configured server-side in the',
  'settings.api_desc2': 'file. Copy',
  'settings.api_desc3': 'to',
  'settings.api_desc4': 'and fill in your keys:',
  'settings.gemini': 'Google Gemini 2.0 Flash',
  'settings.claude': 'Anthropic Claude Sonnet',
  'settings.openai': 'GPT-4o Mini',
  'settings.deepseek': 'DeepSeek Chat — cost-effective, strong Chinese analysis',
  'settings.qwen': 'Qwen Plus (DashScope) — excellent Chinese understanding',

  // Dashboard extras
  'dashboard.action_checklist': 'Action Checklist',
  'dashboard.news_digest': 'News Digest',
  'dashboard.bias_check': 'Bias Check',
  'dashboard.ma_alignment': 'MA Alignment',
  'dashboard.chip_health': 'Chip Health',
  'dashboard.volume_signal': 'Volume Signal',

  // KLine tooltip
  'kline.open': 'Open',
  'kline.close': 'Close',
  'kline.low': 'Low',
  'kline.high': 'High',
  'kline.volume': 'Volume',
} as const;

const zh: Record<keyof typeof en, string> = {
  // Nav
  'nav.dashboard': '仪表盘',
  'nav.history': '历史记录',
  'nav.settings': '设置',

  // Dashboard
  'dashboard.title': 'DeepStock',
  'dashboard.subtitle': '数据为先，AI为辅 — 量化股票分析',
  'dashboard.running': '正在深度分析...',
  'dashboard.running_sub': '正在并行计算基本面、技术面和情绪面',
  'dashboard.pillar_scores': '维度评分',
  'dashboard.radar_title': '多维雷达图',
  'dashboard.key_risks': '主要风险',
  'dashboard.catalysts': '催化剂',
  'dashboard.position_advice': '仓位建议',
  'dashboard.ai_interpretation': 'AI 解读',

  // Tabs
  'tab.fundamental': '基本面',
  'tab.technical': '技术面',
  'tab.sentiment': '情绪面',

  // Search
  'search.placeholder': '输入股票代码 (600519, AAPL, 00700...)',
  'search.analyze': '分析',
  'search.analyzing': '分析中...',

  // Verdict
  'verdict.strong_buy': '强烈买入',
  'verdict.buy': '买入',
  'verdict.hold': '持有',
  'verdict.sell': '卖出',
  'verdict.strong_sell': '强烈卖出',
  'verdict.composite': '综合评分',
  'verdict.confidence': '置信度',

  // Fundamental
  'fundamental.subscores': '基本面子评分',
  'fundamental.valuation': '估值',
  'fundamental.profitability': '盈利能力',
  'fundamental.growth': '成长性',
  'fundamental.health': '财务健康',
  'fundamental.key_ratios': '核心指标',
  'fundamental.pe': '市盈率',
  'fundamental.pb': '市净率',
  'fundamental.ps': '市销率',
  'fundamental.peg': 'PEG',
  'fundamental.roe': 'ROE',
  'fundamental.roa': 'ROA',
  'fundamental.gross_margin': '毛利率',
  'fundamental.net_margin': '净利率',
  'fundamental.revenue_growth': '营收同比增长',
  'fundamental.profit_growth': '利润同比增长',
  'fundamental.debt_equity': '资产负债率',
  'fundamental.current_ratio': '流动比率',
  'fundamental.fcf_yield': '自由现金流收益率',
  'fundamental.eps': '每股收益',
  'fundamental.dividend_yield': '股息率',
  'fundamental.market_cap': '市值',
  'fundamental.financial_trends': '财务趋势',
  'fundamental.company_profile': '公司概况',
  'fundamental.sector': '行业板块',
  'fundamental.industry': '细分行业',
  'fundamental.peer_comparison': '同行对比（百分位）',

  // Technical
  'technical.subscores': '技术面子评分',
  'technical.trend': '趋势',
  'technical.momentum': '动量',
  'technical.volume': '成交量',
  'technical.structure': '结构',
  'technical.pattern': '形态',
  'technical.kline': 'K线图',
  'technical.kline_empty': '暂无图表数据',
  'technical.indicators': '核心指标',
  'technical.sr': '支撑与阻力',
  'technical.support': '支撑位',
  'technical.resistance': '阻力位',
  'technical.fund_flow': '机构资金流向',
  'technical.classification': '分类',
  'technical.chip': '筹码分布',
  'technical.profit_ratio': '获利比率',
  'technical.avg_cost': '平均成本',
  'technical.concentration': '集中度',
  'technical.chip_health': '健康度',
  'technical.patterns': '形态预警',

  // Sentiment
  'sentiment.subscores': '情绪面子评分',
  'sentiment.news': '新闻情绪',
  'sentiment.event': '事件影响',
  'sentiment.attention': '市场关注度',
  'sentiment.quality': '信息源质量',
  'sentiment.distribution': '情绪分布',
  'sentiment.positive': '正面',
  'sentiment.neutral': '中性',
  'sentiment.negative': '负面',
  'sentiment.categories': '新闻分类',
  'sentiment.articles': '新闻文章',
  'sentiment.no_articles': '未找到新闻。请在 .env 中设置 TAVILY_API_KEY 以启用新闻分析。',

  // Charts
  'chart.no_kline': '暂无K线数据',
  'chart.loading': '加载中...',
  'chart.no_radar': '暂无雷达图数据',
  'chart.no_financial': '暂无财务图表数据',
  'chart.revenue': '营业收入',
  'chart.net_profit': '净利润',
  'chart.gross_margin': '毛利率 %',
  'chart.net_margin': '净利率 %',

  // Radar indicators
  'radar.valuation': '估值',
  'radar.profitability': '盈利',
  'radar.growth': '成长',
  'radar.trend': '趋势',
  'radar.momentum': '动量',
  'radar.sentiment': '情绪',
  'radar.series_name': '评分分析',

  // History
  'history.title': '分析历史',
  'history.empty': '暂无历史记录。请在仪表盘运行首次分析。',
  'history.score': '评分',

  // Settings
  'settings.title': '设置',
  'settings.ai_provider': 'AI 模型',
  'settings.ai_desc': '选择用于综合分析的AI模型。请在后端 .env 文件中配置API密钥。',
  'settings.api_keys': 'API 密钥',
  'settings.api_desc': 'API密钥在服务端的',
  'settings.api_desc2': '文件中配置。将',
  'settings.api_desc3': '复制为',
  'settings.api_desc4': '并填入您的密钥：',
  'settings.gemini': 'Google Gemini 2.0 Flash',
  'settings.claude': 'Anthropic Claude Sonnet',
  'settings.openai': 'GPT-4o Mini',
  'settings.deepseek': 'DeepSeek Chat — 高性价比，中文金融分析优秀',
  'settings.qwen': 'Qwen Plus（通义千问）— 中文理解能力强',

  // Dashboard extras
  'dashboard.action_checklist': '操作清单',
  'dashboard.news_digest': '新闻摘要',
  'dashboard.bias_check': '乖离率检查',
  'dashboard.ma_alignment': '均线排列',
  'dashboard.chip_health': '筹码健康度',
  'dashboard.volume_signal': '量能信号',

  // KLine tooltip
  'kline.open': '开盘',
  'kline.close': '收盘',
  'kline.low': '最低',
  'kline.high': '最高',
  'kline.volume': '成交量',
};

export const locales = { en, zh } as const;
