## Requirement
1) 可导入垂直领域词表 和 词表原始文本  
2) 我可以选择任何文本对应的所有专业词汇 
3) 专业词汇可以点击获取文本中整个句子 
4) 专业词汇和句子可以 TTS 读 (openai api)  --- tts 生成后可以存储下来,不用重复调用api 花钱
5) 可以自动翻译句子, 可以解释词表在句子或对应文中含义  
6) 可以链接google 搜索图片和对应解释
7) 可以录音跟读


## Structure of the project
```
DeepGloss/
├── .env                     # 🔐 存放 OPENAI_API_KEY
├── .gitignore               # 🚫 忽略 data/ 和 .env
├── requirements.txt         # 📦 依赖库 (streamlit, openai, pandas...)
├── README.md                # 📝 项目文档
├── main.py                  # 🚀 启动入口 (Streamlit 主页)
├── config.py                # ⚙️ 全局配置 (路径常量、模型名称)
│
├── app/                     # 🧠 核心代码库
│   ├── __init__.py
│   │
│   ├── database/            # 💾 数据库层
│   │   ├── __init__.py
│   │   ├── schema.sql       # SQL 建表语句
│   │   └── db_manager.py    # 封装所有 SQLite 操作 (增删改查)
│   │
│   ├── services/            # ⚡ 业务逻辑层 (最重要!)
│   │   ├── __init__.py
│   │   ├── ingestion.py     # 📥 核心算法: 文本分句 + 词汇匹配
│   │   ├── llm_client.py    # 🤖 封装 GPT-4o-mini (翻译/解释)
│   │   └── tts_manager.py   # 🗣️ 封装 TTS (含 MD5 哈希缓存机制)
│   │
│   ├── ui/                  # 🎨 界面组件
│   │   ├── __init__.py
│   │   ├── components.py    # 可复用的 UI 块 (如: 单词卡片, 音频播放器)
│   │   └── sidebar.py       # 侧边栏导航逻辑
│   │
│   └── utils/               # 🛠️ 工具函数
│       ├── __init__.py
│       ├── file_helper.py   # 处理 PDF/TXT 读取
│       └── text_helper.py   # 简单的文本清洗工具
│
└── pages/                   # 📑 Streamlit 多页面路由
    ├── 1_📥_Import_Data.py  # 导入词表 & 文章
    └── 2_📚_Study_Mode.py   # 核心学习界面
```

