# LINE Bot Webhook (FastAPI版本)

这是一个使用FastAPI框架实现的LINE Bot Webhook服务。

## 功能特性

- 处理LINE Bot的webhook事件
- 支持文本消息、图片消息等
- 提供推送消息API
- 支持营业数据、赠退菜记录、短信额度等业务模板

## 环境要求

- Python 3.10+
- FastAPI
- uvicorn
- line-bot-sdk

## 安装和运行

### 本地开发

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置环境变量：
```bash
export LINE_CHANNEL_SECRET=your_channel_secret
export LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token
```

3. 运行应用：
```bash
python app.py
```

或者使用uvicorn直接运行：
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Docker部署

1. 构建镜像：
```bash
docker build -t line-bot-webhook .
```

2. 运行容器：
```bash
docker run -p 8000:8000 \
  -e LINE_CHANNEL_SECRET=your_channel_secret \
  -e LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token \
  line-bot-webhook
```

### Kubernetes部署

1. 设置环境变量
2. 应用部署配置：
```bash
kubectl apply -f deploy/deploy.yaml
```

## API端点

- `POST /callback` - LINE Bot webhook回调
- `POST /push` - 推送消息API
- `GET /static/{path}` - 静态文件服务

## 推送消息API

`POST /push` 端点支持以下action类型：

- `business_data` - 营业数据模板
- `gift_cancel` - 赠退菜记录模板  
- `quota` - 短信额度模板

请求参数：
- `res` - JSON格式的数据
- `user_id` - 用户ID
- `shop` - 店铺名称
- `action` - 动作类型（可选，默认为default）

## 从Flask迁移

主要变化：
- 使用FastAPI替代Flask
- 使用uvicorn替代uwsgi
- 异步处理请求
- 更新了依赖项和部署配置
- 端口从5000改为8000 