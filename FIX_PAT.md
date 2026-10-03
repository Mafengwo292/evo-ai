# 修复 PAT 权限 - 精确步骤

你的仓库 `Mafengwo292/evo-ai` 已经建好了（我刚才用 API 确认了）。
但当前 PAT 还没有这个仓库的写入权限。

## 精确步骤（30 秒）

1. 打开 https://github.com/settings/personal-access-tokens
   （这是 **PAT 列表页**，不是新建页）

2. 在列表里找到你的 PAT（我看到的 ID 是 `11CAZEA2A0CpuAFEh4AUNq_L8AFhPizjEZLNhDurYv02qKTF73LsiFrnD8QhjEPVFsFHHW42NUqMi2o3Zr`）

3. 点右侧的 **Configure** 按钮（如果过期了要先 **Regenerate**）

4. 在配置页里找到 **Repository access** 部分

   默认可能是 **No repositories** 或 **Only select repositories**

5. **关键**：改成 **All repositories**（或者 **Public Repositories (read-only)** 改成 **Public Repositories (read and write)**）

   - 如果选 **Only select repositories**，下面会出现 **Select repositories** 按钮
   - 点它，选中你的 `evo-ai` 仓库

6. 在 **Permissions** → **Repository permissions** 里：
   - **Contents**: 改选 **Read and write**（默认是 Read-only）
   - **Pull requests**: 改选 **Read and write**（要 EvoAgentX PR 用）
   - **Actions**: **Read and write**（要 workflows 用）
   - **Issues**: **Read and write**

7. 滚动到顶部点 **Update token**

8. （可选）刷新页面，确认设置已保存

9. 回来告诉我「更新好了」

## 验证方式

如果想先验证，看我这里：
- 我会测 `POST /repos/Mafengwo292/evo-ai/contents/test.md`
- 返回 201 = 可以写入 ✓
- 返回 403 = 还是没有

## 备用方案

如果上面的 UI 操作很复杂（GitHub 改版后 UI 可能不一样），也可以：
- 重新生成一个 **classic PAT**：勾选 `repo` scope（自动包含所有仓库权限）
- 把新 token 发我

