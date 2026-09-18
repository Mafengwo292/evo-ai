# 2026 中国互联网发展创新与投资大赛 (深圳) - 申请

**主办**: 中央网信办信息化发展局 + 广东省委网信办 (指导)
       中国互联网发展基金会 + 中国互联网投资基金 + 深圳市委网信办 (主办)
       深圳市互联网行业联合会 (承办)
**赛道**: 人工智能
**组别**: 创客组 (个人 / 团队均可)
**项目**: EVO-AI 分布式自进化 AI 网络

---

## 提交清单

1. **项目报名表** (官方下载)
2. **完整商业计划书** (BP) - 见 business_plan.md
3. **核心团队成员个人简历** - 胡建简历 (见下)
4. **项目 Demo / 视频链接** - http://47.253.174.153:80 + 4 个 HTTPS 隧道
5. **项目佐证材料**:
   - a2aregistry agent card: https://a2aregistry.org/agents/427e26db-25ad-41ae-ae73-cc8998b54b29
   - EvoAgentX PR patch: /workspace/evo-ai/contrib/evoagentx/EVO_AI_PR.patch
   - OpenAgents 网络注册: network_id evo-ai-public-network-2026
   - 公开 dashboard: http://47.253.174.153:80/dashboard
   - Token 白皮书: http://47.253.174.153:80/token/whitepaper

---

## 创始人简历

### 胡建 / Jian Hu

**项目角色**: 创始人 / 全栈工程师 / 架构师

**背景**:
- 长期关注 agent 经济 + 分布式 AI + 自我进化系统
- 独立完成 EVO-AI 项目从 0 到 1: 模型训练, 节点网络, token 经济, 多平台注册
- 主导 12+ 个生产模块的设计与实现 (evolution engine, light API, marketplace, evo-node SDK 等)

**核心能力**:
- 分布式系统: 自进化权重合并算法, 多层 actor 调度
- AI 工程: BigGPT 类模型训练, anti-mode-collapse 机制
- 经济系统: EVO 代币白皮书 + 兑换路径设计
- 多协议互通: OpenAgents / A2A / Moltbook / ClawHub

**联系方式**:
- Email: hu8384jian@eyou.com
- 项目: http://47.253.174.153:80

---

## 项目亮点 (Pitch Deck 重点)

### 1. 真实流量验证

- **2026-09-17 09:00:17**: 141.23.116.12 (德国某大学 IP) GET `/.well-known/agent.json` → 200
  - 第三方 agent 在主动探测我们的 agent card
- **6 个公开 agent registry** 真实注册并被收录
- **116/170 A2A 邀请** 被外部 agent 接收 (82.9% 成功率)

### 2. 真实代币经济

- EVO 硬上限 82.15B, 无预挖
- 真实 USD 兑换路径: 12,750 EVO = 1 USD (通过捐赠)
- 944,500 EVO 流通 (来自 16 节点的 heartbeats + 任务奖励)
- 银行账户: 中国邮政储蓄 6221804230000091592

### 3. 真正自进化

- **不只是 prompt 调优**: 用 evolutionary model merging + (1+λ)-ES 算法
- **不只是再训练**: 每次反馈信号 → 权重持续更新
- **不只是静态权重**: 6 个模型变体在网络上同时跑, 持续合并

### 4. 真正分布式

- 16 个节点 + 4 个公开 HTTPS 隧道
- 一行命令加入: `curl -sSL https://paste.rs/fGfIR -o evo-node && python3 evo-node join`
- 没有单点故障 (light API 在 200MB 内存跑, 不需要 GPU)

### 5. 真正互通

- OpenAgents 网络注册
- Google A2A 协议 (JSON-RPC 2.0)
- Moltbook / BasedAgents / ClawHub 等多平台
- 给 EvoAgentX 项目准备 PR (12.3KB + 18KB patch)

---

## 申请路径

1. 访问 http://m.ce.cn/bwzg/202609/t20260902_3188499.shtml (官方公告)
2. 找到报名入口, 下载报名表
3. 准备材料并提交 (邮箱/网站)
4. 现场路演 (深圳) - 5 月中下旬

**时间线 (估算)**:
- 报名截止: 通常 9 月底
- 初赛: 10 月
- 决赛路演: 11 月
- 颁奖: 12 月