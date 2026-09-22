# 🎉 服务器恢复 v2 - Sep 22 09:32 UTC+8

## 故障 → 恢复
- **故障开始**: Sep 21 ~12:00 UTC+8
- **用户强制重启**: Sep 22 09:32 UTC+8
- **故障持续**: ~21.5 小时
- **原因**: 同上次 - 1.8GB VPS OOM 反复触发

## 自动恢复（systemd 救命）
- ✅ evo-api (Flask 8765)
- ✅ evo-pub (publisher)
- ✅ evo-test (test node)
- ✅ crond (24 jobs)
- ✅ 早期 evolution state 保留

## 手动恢复（我跑的）
- ✅ iptables 80→8765 NAT 重加
- ✅ tmux pinggy + serveo 隧道重启
- ✅ GitHub Pages URL 同步

## Evolution 接续（完美）
- Sep 21 13:00: Gen 569, fit 0.1639
- Sep 22 09:32: **Gen 575, fit 0.1657** （重启后自动跑了 6 代）
- 训练数据保留（50K chars）
- Vocab 112 (扩大了！)
- Memory 1523MB available (充足)

## 教训 (这次更确定)
- 1.8GB 真的不够用
- Evolution 24h 不停跑 + 24 cron + A2A + watchdog = OOM 必崩
- 必须升级到 2GB+ 或减并发
