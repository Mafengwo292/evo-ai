# 🚨 Aliyun 服务器第二次故障 - Sep 21 17:15 UTC+8 起

## 时间线
- **正常运行**: Sep 20 13:50 → Sep 21 ~12:00 (~22h)
- **故障开始**: Sep 21 17:00 ish UTC+8 (Load avg 6.52 时还在但压力高)
- **发现**: Sep 21 17:15 SSH banner hang
- **当前**: ~5h+ 持续 503 + SSH hang

## 症状
- HTTP 80: 503 (Flask 后端连接被拒)
- HTTP 8765: TimeoutError
- SSH 22: TCP 连接 OK 但 banner hang
- 所有端口 TCP 仍可达

## 原因推测（更高概率是同一原因）
**1.8GB VPS 长期内存压力累积**：
- Evolution 24h 不停跑（11 代/小时）
- 24+ cron jobs 并发
- Load avg 6.52+ 时已经接近崩溃阈值
- OOM killer 周期性 kill Flask
- sshd fork() 失败 → banner 阶段 hang
- 这次和上次一样，但持续时间更长

## 还没恢复的可能原因
- OOM 频繁触发 → 系统一直在 low memory 状态
- 关键进程被杀后 systemd 重启但资源不足
- sshd 可能已经被 kill 多次

## 你需要做的（继续像上次一样）
1. https://ecs.console.aliyun.com/
2. 找 iZ0xi5fuqy4z60gtdg34nzZ (47.253.174.153)
3. **强制重启**（Force Reboot）
4. 起来后 systemd 会自动拉起 evo-api/evo-pub/evo-test
5. 我会立即接管恢复

## 长期解决（待你回来决策）
- 升级到 2GB+ VPS（阿里云约 ¥30/月）
- 或砍掉一些 cron job 减少并发
- 或降低 evolution 频率（每 2h 而不是每小时）

## 系统当前状态（快照于 08:30 早晨）
- Generation: 527
- Fitness: 0.1509
- A2A contacts: 223
- 所有数据已保存到 GitHub
- 离线备份完整
