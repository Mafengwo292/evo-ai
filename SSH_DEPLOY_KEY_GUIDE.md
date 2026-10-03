# SSH Deploy Key 方案 — 绕过 PAT 权限问题

## 问题

你的 PAT（fine-grained）默认没勾 evo-ai 仓库的写权限，所以 git push 一直 403。
fine-grained PAT 的 "Repository access" 区域如果不勾，写权限就不会生效。

## 解决（绕过 PAT）

我刚生成了一对 SSH 密钥：

**公钥**（你加到 GitHub evo-ai 仓库）：
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMygpT8Fm2KUeJ82XfxzlXe6ZKO8DrQfFlEO0uxnUwKg evo-ai@github
```

**私钥**（保存在我这里 `/tmp/evo_ai_github_key`，同时会传到 server）：
```
ssh-ed25519 [隐藏]
```

## 你需要做的（30 秒）

1. 打开 https://github.com/Mafengwo292/evo-ai/settings/keys/new
   （注意：是 evo-ai 仓库的 settings，不是全局）

2. Title 填：`EVO-AI deploy`

3. 把上面那行公钥（以 ssh-ed25519 开头到 evo-ai@github 结尾）粘贴到 Key 框

4. ☑️ 勾选 **Allow write access**（默认就是勾的）

5. 点 **Add key**

回到这里告诉我「加好了」。

## 然后我会做的

```bash
git remote add origin git@github.com:Mafengwo292/evo-ai.git
git push -u origin main
```

686 个文件 + EvoAgentX fork + PR 全部自动完成。

---

## 备选：最简方案（如果 deploy key 也复杂）

直接把 evo-ai 仓库的 **Collaborators** 删掉你自己（让 PAT 失效），然后重新走 PAT 流程。

或者更简单：去 https://github.com/settings/tokens/new 生成一个 **classic PAT**（不是 fine-grained）：

- Note: EVO-AI
- Expiration: 30 days
- Scopes: 只勾 **`repo`**

classic PAT 只要勾了 repo，就有所有公开/私有仓库的读写权限。

---

## ⏸️ 等你

哪条路对你最简单？deply key 也好、classic PAT 也好，30 秒内完成。
