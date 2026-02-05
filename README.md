# AI Beauty Muse Backend

AI 美學繆斯後端服務 - 基於 FastAPI 的智能美學分析 API

## 功能特點

### 🎨 深度美學分析
- **面部分析 (L1)**: 臉型識別、五官分析、髮型推薦、妝容建議、面相解讀
- **色彩診斷 (L2)**: 四季色彩類型判定、最佳用色、禁忌色、妝容配色
- **身材分析 (L3)**: 身材類型判定（H/X/O/A/V型）、穿搭建議、廓形推薦

### 💇 AI 髮型實驗室
- **髮型生成**: 根據臉型和偏好生成髮型效果圖
- **髮色實驗**: 預覽不同髮色效果
- **理髮師卡**: 生成專業溝通卡片

### 🔮 命理色譜
- **八字分析**: 計算四柱八字、五行分布
- **喜用神**: 判定個人喜用神
- **能量色彩**: 補能色、平衡色、禁忌色推薦

### ☀️ 每日能量
- **干支能量**: 每日干支五行分析
- **幸運色**: 每日幸運色推薦
- **穿搭建議**: 場合穿搭方案

### 💬 AI 聊天助手
- **多模態對話**: 支持文字和圖片
- **專業建議**: 髮型、妝容、穿搭全方位諮詢

## 技術棧

- **框架**: FastAPI 0.109.0
- **Python**: 3.11+
- **AI**: OpenAI GPT-4o / DALL-E 3
- **數據驗證**: Pydantic 2.5
- **異步**: asyncio + httpx

## 項目結構

```
ai-beauty-muse-backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 應用入口
│   ├── config.py            # 配置管理
│   ├── api/                  # API 路由
│   │   ├── analysis.py      # 面部/色彩/身材分析
│   │   ├── hairstyle.py     # 髮型生成
│   │   ├── destiny.py       # 命理分析
│   │   ├── daily.py         # 每日能量
│   │   └── chat.py          # AI 聊天
│   ├── models/
│   │   └── schemas.py       # Pydantic 數據模型
│   ├── services/            # 業務邏輯
│   │   ├── openai_service.py
│   │   ├── face_analysis_service.py
│   │   ├── color_diagnosis_service.py
│   │   ├── body_analysis_service.py
│   │   ├── hairstyle_service.py
│   │   ├── destiny_service.py
│   │   ├── daily_energy_service.py
│   │   └── chat_service.py
│   └── utils/
├── tests/                    # 測試文件
├── docs/                     # 文檔
├── requirements.txt          # 依賴
└── README.md
```

## 快速開始

### 1. 安裝依賴

```bash
cd ai-beauty-muse-backend
pip install -r requirements.txt
```

### 2. 配置環境變量

創建 `.env` 文件：

```env
# OpenAI 配置（必需）
OPENAI_API_KEY=your-openai-api-key

# 可選配置
OPENAI_MODEL=gpt-4o
OPENAI_VISION_MODEL=gpt-4o
OPENAI_IMAGE_MODEL=dall-e-3

# 服務器配置
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 3. 啟動服務

```bash
# 開發模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生產模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 訪問 API 文檔

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端點

### 分析 API

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/analysis/face` | POST | 面部分析 |
| `/api/v1/analysis/color` | POST | 色彩診斷 |
| `/api/v1/analysis/body` | POST | 身材分析 |

### 髮型 API

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/hairstyle/generate` | POST | 髮型生成 |
| `/api/v1/hairstyle/color` | POST | 髮色實驗 |
| `/api/v1/hairstyle/stylist-card` | POST | 理髮師卡 |

### 命理 API

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/destiny/analyze` | POST | 八字分析 |

### 每日能量 API

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/daily/energy` | POST | 每日能量 |
| `/api/v1/daily/quick` | GET | 快速查詢 |

### 聊天 API

| 端點 | 方法 | 描述 |
|------|------|------|
| `/api/v1/chat/` | POST | AI 對話 |
| `/api/v1/chat/suggestions` | GET | 對話建議 |

## 使用示例

### 面部分析

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/analysis/face",
        json={"image_url": "https://example.com/face.jpg"}
    )
    result = response.json()
    print(f"臉型: {result['face_shape_cn']}")
    print(f"髮型推薦: {result['hairstyle_recommendations']}")
```

### 每日能量

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/daily/energy",
        json={
            "occasion": "面試",
            "user_birth_year": 1990,
            "user_birth_month": 5,
            "user_birth_day": 15
        }
    )
    result = response.json()
    print(f"今日干支: {result['daily_stem_branch']}")
    print(f"幸運色: {result['lucky_colors']}")
```

### AI 聊天

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/chat/",
        json={
            "message": "我是圓臉，適合什麼髮型？",
            "image_url": "https://example.com/my-photo.jpg"  # 可選
        }
    )
    result = response.json()
    print(f"回覆: {result['reply']}")
```

## 測試

```bash
# 運行所有測試
pytest tests/ -v

# 運行特定測試
pytest tests/test_destiny.py -v

# 生成覆蓋率報告
pytest tests/ --cov=app --cov-report=html
```

## 部署

### Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t ai-beauty-muse-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key ai-beauty-muse-backend
```

## 注意事項

1. **OpenAI API Key**: 必須配置有效的 OpenAI API Key 才能使用 AI 功能
2. **圖片 URL**: 所有圖片分析功能需要提供可公開訪問的圖片 URL
3. **速率限制**: 請注意 OpenAI API 的速率限制
4. **費用**: AI 功能會產生 OpenAI API 調用費用

## 許可證

MIT License

## 聯繫方式

如有問題或建議，請提交 Issue 或 Pull Request。
