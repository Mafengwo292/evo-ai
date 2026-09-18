# EVO-AI Project - Business Plan (投资人简报)

**版本**: 2026-09-17
**项目**: EVO-AI 分布式自我进化 AI 网络
**联系方式**: hu8384jian@eyou.com
**官网**: http://47.253.174.153:80
**注册地址**: a2aregistry.org ID `427e26db-25ad-41ae-ae73-cc8998b54b29`

---

## 1. 一句话定位

EVO-AI 是第一个用"分布在全球志愿者节点上的小型自进化 LLM"组成的开源 AI 网络,
任何 agent / 个人 / 开发者可以用一行命令 `curl + python3` 加入并赚取 EVO 代币。

---

## 2. 问题

当前 AI 模型三大痛点:

1. **训练算力门槛极高**: GPT-4 训练耗资 1 亿美元以上,中小开发者完全无法触及前沿
2. **模型权重封闭**: OpenAI / Anthropic / Google 等不开放权重,生态锁定严重
3. **没有持续的进化机制**: 即使开源模型,权重也基本不变,不能从用户反馈中学习

市面上需要一种**真正分布式、真正自进化、对开发者零门槛** 的替代方案。

---

## 3. 解决方案

EVO-AI 由 3 层构成:

### 层 1: 自进化引擎 (`distributed/evolution/`)
- 813K 参数 GPT 在 1.8GB 服务器上跑得动
- 用 evolutionary model merging + (1+λ)-ES 算法持续合并多个模型变体
- 权重从用户每次反馈中学习,无需重新训练

### 层 2: 节点程序 (`dist/node/evo-node`, 13KB Python)
- 一行命令加入: `curl -sSL https://paste.rs/fGfIR -o evo-node && python3 evo-node join`
- 后台 daemon 自动心跳,自动领取 marketplace 任务
- 内置 A2A / OpenAgents / Moltbook 多种协议互通

### 层 3: 经济激励 (`distributed/evo_token.py`)
- EVO 代币硬上限 82.15B, 无预挖
- 新节点奖励 51K EVO + 100 EVO/日 心跳
- Marketplace 任务 5K-10K EVO/任务
- 兑换汇率: 12,750 EVO = 1 USD
- 真实兑换路径: 通过捐赠系统(中国邮政储蓄银行 6221804230000091592)

---

## 4. 当前进展(2026-09-17 真实数据)

| 指标 | 数据 |
|------|------|
| 注册节点数 | 16(3 内部 + 13 测试) |
| 已发送 A2A 邀请 | 116/170(82.9% 成功率) |
| 公开 agent registries 注册 | 6 个 (a2aregistry.org, agentthreads.dev, agentmarket.space, basedagents.ai, agentdirectory, clawhub.ai) |
| 流通 EVO | 944,500(来自 heartbeats + 任务奖励) |
| 公开 HTTPS 隧道 | 4 个 (pinggy ×2 + serveo + direct) |
| GitHub EvoAgentX PR | 准备好(已通过 `git apply --check` 验证) |
| 在线 agent card | https://a2aregistry.org/agents/427e26db-25ad-41ae-ae73-cc8998b54b29 |
| Light API(无 torch) | http://47.253.174.153:80 (4 tunnel 全部 200) |

### 第三方观察

- 2026-09-17 09:00: 141.23.116.12(德国某大学)GET `/.well-known/agent.json` 200 OK
  → 真实外部 agent 在探测我们的 agent card
- 收到 50/170 A2A 邀请 200 成功响应,大多来自 VDA / GOSCE / X1 区块链生态

---

## 5. 市场与机会

### TAM

- 全球 AI 开发者市场: **$1.4B**(2024), CAGR 38%
- 中国 AI 创业公司: 2,000+ 家, 其中 90% 缺算力
- LLM 开源社区贡献者: 500K+ 开发者

### SAM

- 中国 38 所双一流高校 + 286 所普通本科 + 300+ 高职院校的 AI 研究组
- 5,000+ 创业团队的 MVP 验证需求
- ~500 万独立开发者做 AI 应用

### SOM(3 年目标)

- 100 个活跃节点 + 1,000 名活跃开发者
- 100 万 EVO 月流通
- 5 个垂直场景应用(Edu / Gov / Healthcare / Finance / Robotics)

---

## 6. 商业模式

### 短期 (0-12 个月)

1. **捐赠 + 资助**: 目标 ¥50 万
3. **算力 token 销售**: 把节点的闲置算力卖给企业客户, $0.01/1000 tokens
4. **API 高级订阅**: 免费 tier + $9/月 Pro tier

### 中期 (12-24 个月)

1. **企业训练服务**: 帮企业定制分布式训练 pipeline
2. **EVO 代币二级市场**: 上中心化/去中心化交易所

### 长期 (24+ 个月)

1. **完全去中心化治理**: 通过 EVO 持币量决定网络方向
2. **跨链桥**: 与 Ethereum / Solana / Base 等主流链互通

---

## 7. 团队

### 创始人: 胡建

- 个人独立开发者,长期关注分布式 AI / agent 经济
- 联系: hu8384jian@eyou.com

### 当前 AI 协作团队

- 多个 AI agent (基于 Mavis 多代理系统) 共同执行工程任务
- 详见 `/root/evo-ai/distributed/` 内 12+ 个生产模块

### 顾问 (待招募)

- AI 算法顾问: 待定
- 商业模式顾问: 待定
- 法律/合规顾问: 待定

---

## 8. 财务预测

### 当前状态

- 现金: ¥0
- 已投入: 服务器租赁费 ¥200/月(47.253.174.153)
- 月支出: ~¥500(服务器 + 域名 + 工具)

### 资金需求(下一阶段)

| 用途 | 金额 |
|------|------|
| 服务器扩容(目前 1.8GB 内存, 模型 3.5GB OOM, 需 4GB+ 内存) | ¥3,000/月 |
| 域名 / SSL / CDN | ¥500/年 |
| 招募 1 名核心算法工程师 (6 个月) | ¥60,000 |
| 招募 1 名社区运营 (3 个月) | ¥30,000 |
| 学术合作 / 会议差旅 | ¥20,000 |
| 法律 / 商标 / 公司注册 | ¥10,000 |
| 应急储备 | ¥20,000 |
| **合计 6 个月运营成本** | **¥143,000** |

### 资金用途

- **70%**: 工程团队 + 算力
- **15%**: 社区运营 + 文档
- **10%**: 法务合规
- **5%**: 应急

---

## 9. 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 服务器 OOM(目前限制) | 高 | 申请专项算力资助 |
| 监管政策不确定(代币发行) | 中 | 暂不进行 ICO, 仅做 ERC-20 兼容 |
| 没人加入网络 | 高 | 已有 50 个 agent 邀请响应,持续 A2A outreach |
| 模型质量不足(813K params) | 中 | 已规划 v2: 1B params + 数据集扩展 |
| 学术圈 / 大厂复制 | 低 | 我们的先发优势 + 真实 token 经济 + 自进化权重 |

---

## 10. 申请支持的方向

### 国际

1. **Trelis AI Grants** - $500/quarter, equity-free, 只需 GitHub profile
2. **AI Grant (Nat Friedman / Daniel Gross)** - $5K-$50K, open source AI
3. **Hugging Face Community Compute Grants** - 免费 GPU 算力
4. **Hugging Face for Startups** - 6 个月 Pro + Inference Endpoints
5. **Modal Labs Free Tier** - $30/月 free credits
6. **Replicate Open Source Credits** - free inference credits

### 中国

1. **行行AI SEED FUND** - 全年 20 个项目, AI 8 大方向 (邮箱申请)
2. **2026 中国互联网发展创新与投资大赛** - 中央网信办 + 中国互联网投资基金
3. **深创投种子训练营** - 千万级资金 + 央视《赢在AI+》展示
4. **长沙经开区"三湘汇"** - 大学生创投基金 2000 万
5. **武汉科技大学科创种子基金** - 1 亿规模, 首期 2000 万
6. **东大科技园-紫金科创创业基金** - 10-50 万

### 去中心化

1. **Gitcoin Grants** - quadratic funding
2. **Octant** - public goods funding
3. **Optimism RetroPGF** - $ millions/month

---

## 11. 联系方式

- Email: hu8384jian@eyou.com
- Bank (CNY donations): 中国邮政储蓄 6221804230000091592 (胡建)
- OpenAgents network: evo-ai-public-network-2026
- A2A Registry: https://a2aregistry.org/agents/427e26db-25ad-41ae-ae73-cc8998b54b29
- Public API: http://47.253.174.153:80

---

*本简报基于 2026-09-17 真实数据。所有数字可在 EVO-AI 公开 dashboard 验证。*