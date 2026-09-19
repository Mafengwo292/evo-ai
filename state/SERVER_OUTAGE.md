# 🚨 Aliyun 服务器故障（Sep 19 22:32 UTC+8 起）

## 故障表现
- SSH 22: TCP 连接 OK, 但 banner 阶段超时（sshd 不响应）
- HTTP 80: 返回 503 (istio-envoy 代理无法连接上游 Flask)
- HTTP 8765 (Flask 直连): 超时

## 原因推测
最可能是 OOM - 1.8GB VPS 满载
- 24h iteration engine 跑满 22h+
- Evolution cron + A2A inviter + tunnel watchdog 同时跑
- systemd 因 OOM 失败无法自动重启

## 用户可做的恢复操作
1. 登录阿里云控制台 https://ecs.console.aliyun.com/
2. 找到 iZ0xi5fuqy4z60gtdg34nzZ 实例
3. 重启实例
4. 重启后 systemd 会自动启动 3 个服务（evo-api/evo-pub/evo-test）

## 重启后需要的修复
- iptables 80→8765 规则需要重加
- tmux tunnel (pinggy/serveo) 会丢，需要 tunnel_watchdog.sh 恢复
- crond 可能需要 systemctl enable crond

## 网络仍然可用
- GitHub Pages: https://mafengwo292.github.io/evo-ai/ ✓
- GitHub repo: 公开代码 ✓
- paste.rs URLs: 全部永久保留 ✓
