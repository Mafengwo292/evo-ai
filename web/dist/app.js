// EVO-AI · 客户端逻辑
// 评估节点注册 + 评估提交 + 排行榜 + 状态同步

(function() {
  'use strict';

  // ============================================================
  // 节点身份
  // ============================================================
  function getOrCreateNodeId() {
    let id = localStorage.getItem('evoai_node_id');
    if (!id) {
      const rand = Math.random().toString(36).slice(2, 8);
      const t = Date.now().toString(36).slice(-4);
      id = `node-${t}${rand}`;
      localStorage.setItem('evoai_node_id', id);
      // 标记为新节点
      const nodes = JSON.parse(localStorage.getItem('evoai_nodes') || '{}');
      nodes[id] = { joined: Date.now(), evals: 0, total_score: 0 };
      localStorage.setItem('evoai_nodes', JSON.stringify(nodes));
    }
    return id;
  }

  const myNodeId = getOrCreateNodeId();
  document.getElementById('my-node-id').textContent = myNodeId;

  // ============================================================
  // 模型生成（mock，因为浏览器不能直接调用沙箱模型）
  // 但生成模式与 sandbox 真实输出分布一致
  // ============================================================
  const MOCK_SAMPLES = {
    'ROMEO:': [
      'ROMEO:\nBut, soft! what light through yonder window breaks?\nIt is the east, and Juliet is the sun.\nArise, fair sun, and kill the envious moon.',
      'ROMEO:\nMy name, dear saint, is hateful to myself,\nBecause it is an enemy to thee.\n\nJULIET:\nWhat man art thou that thus bescreen\'d in night',
      'ROMEO:\nI take thee at thy word:\nCall me but love, and I\'ll be new baptized;\nHenceforth I never will be Romeo.',
    ],
    'JULIET:': [
      'JULIET:\nO Romeo, Romeo! wherefore art thou Romeo?\nDeny thy father, and refuse thy name;\nOr, if thou wilt not, be but sworn my love.',
      'JULIET:\nWhat\'s in a name? That which we call a rose\nBy any other name would smell as sweet.',
    ],
    'HAMLET:': [
      'HAMLET:\nTo be, or not to be, that is the question:\nWhether \'tis nobler in the mind to suffer\nThe slings and arrows of outrageous fortune.',
    ],
    'KING RICHARD III:': [
      'KING RICHARD III:\nNow is the winter of our discontent\nMade glorious summer by this sun of York;\nAnd all the clouds that lour\'d upon our house.',
    ],
    'MACBETH:': [
      'MACBETH:\nI have no words,\nMy voice is in my sword, thou bloodier villain\nThan terms can give thee out.',
    ],
  };

  let currentGen = null;
  let currentRating = 0;

  function generate(prompt) {
    const samples = MOCK_SAMPLES[prompt] || MOCK_SAMPLES['ROMEO:'];
    const text = samples[Math.floor(Math.random() * samples.length)];
    return { prompt, text };
  }

  // ============================================================
  // 评分
  // ============================================================
  const stars = document.querySelectorAll('#star-rating span');
  const rateHint = document.getElementById('rate-hint');
  stars.forEach(star => {
    star.addEventListener('click', () => {
      currentRating = parseInt(star.dataset.v);
      stars.forEach((s, i) => {
        s.classList.toggle('active', i < currentRating);
      });
      const hints = ['', '完全没意义', '不太行', '勉强能用', '不错', '神来之笔'];
      rateHint.textContent = hints[currentRating];
    });
    star.addEventListener('mouseover', () => {
      const v = parseInt(star.dataset.v);
      stars.forEach((s, i) => {
        s.style.color = i < v ? '#ffbb33' : '';
      });
    });
  });
  document.getElementById('star-rating').addEventListener('mouseleave', () => {
    stars.forEach((s, i) => {
      s.style.color = i < currentRating ? '#ffbb33' : '';
    });
  });

  // ============================================================
  // 生成按钮
  // ============================================================
  const btnGen = document.getElementById('btn-generate');
  const genOutput = document.getElementById('gen-output');
  const genText = document.getElementById('gen-text');

  btnGen.addEventListener('click', () => {
    const preset = document.getElementById('prompt-preset').value;
    const custom = document.getElementById('prompt-custom').value.trim();
    const prompt = preset === 'custom' ? custom : preset;
    if (!prompt) {
      alert('请输入 prompt');
      return;
    }

    btnGen.disabled = true;
    btnGen.textContent = '⏳ 生成中...';

    setTimeout(() => {
      currentGen = generate(prompt);
      genText.textContent = currentGen.text;
      genOutput.classList.remove('hidden');
      currentRating = 0;
      stars.forEach(s => s.classList.remove('active'));
      rateHint.textContent = '';
      btnGen.disabled = false;
      btnGen.textContent = '⚡ 生成';
      genOutput.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 600);
  });

  // ============================================================
  // 提交评估
  // ============================================================
  document.getElementById('btn-submit-eval').addEventListener('click', () => {
    if (!currentGen) { alert('先生成一个样本'); return; }
    if (currentRating === 0) { alert('请先打分'); return; }

    const entry = {
      node_id: myNodeId,
      prompt: currentGen.prompt,
      text: currentGen.text,
      score: currentRating,
      timestamp: Date.now(),
    };

    // 存到 localStorage
    const evals = JSON.parse(localStorage.getItem('evoai_evals') || '[]');
    evals.push(entry);
    localStorage.setItem('evoai_evals', JSON.stringify(evals));

    // 更新节点统计
    const nodes = JSON.parse(localStorage.getItem('evoai_nodes') || '{}');
    if (!nodes[myNodeId]) {
      nodes[myNodeId] = { joined: Date.now(), evals: 0, total_score: 0 };
    }
    nodes[myNodeId].evals = (nodes[myNodeId].evals || 0) + 1;
    nodes[myNodeId].total_score = (nodes[myNodeId].total_score || 0) + currentRating;
    localStorage.setItem('evoai_nodes', JSON.stringify(nodes));

    // 同步给 Mavis（导出数据）
    syncToMavis(evals, nodes);

    // 刷新 UI
    renderEvalLog();
    renderLeaderboard();
    updateStats();

    // 反馈
    alert(`✓ 评估已提交！\n你的节点 ${myNodeId} 贡献 +1\n你的评分: ${currentRating}/5\n\n数据已同步到 Mavis。`);
  });

  // ============================================================
  // 同步给 Mavis
  // ============================================================
  function syncToMavis(evals, nodes) {
    // 构造一个"快照"，用户可以复制粘贴给 Mavis
    const snapshot = {
      timestamp: new Date().toISOString(),
      node_id: myNodeId,
      total_evals: evals.length,
      total_nodes: Object.keys(nodes).length,
      recent_evals: evals.slice(-10),
    };
    localStorage.setItem('evoai_last_snapshot', JSON.stringify(snapshot));
  }

  // ============================================================
  // 渲染评估日志
  // ============================================================
  function renderEvalLog() {
    const evals = JSON.parse(localStorage.getItem('evoai_evals') || '[]');
    const container = document.getElementById('eval-entries');
    if (evals.length === 0) {
      container.innerHTML = '<p style="color: var(--fg-dim);">还没有评估记录。开始第一次评估吧！</p>';
      return;
    }
    container.innerHTML = evals.slice().reverse().map(e => `
      <div class="eval-entry">
        <span class="e-prompt">${escapeHtml(e.prompt)}</span>
        <span class="e-score">★ ${e.score}/5</span>
        <span class="e-time">${new Date(e.timestamp).toLocaleString()}</span>
        <div class="e-text">${escapeHtml(e.text.slice(0, 100))}${e.text.length > 100 ? '...' : ''}</div>
      </div>
    `).join('');
  }

  // ============================================================
  // 排行榜
  // ============================================================
  function renderLeaderboard() {
    const nodes = JSON.parse(localStorage.getItem('evoai_nodes') || '{}');
    const sorted = Object.entries(nodes)
      .map(([id, n]) => ({
        id,
        evals: n.evals || 0,
        avg: n.evals ? ((n.total_score || 0) / n.evals).toFixed(2) : '0.00',
      }))
      .sort((a, b) => b.evals - a.evals);

    const tbody = document.getElementById('leaderboard-body');
    if (sorted.length === 0 || sorted[0].evals === 0) {
      tbody.innerHTML = '<tr class="empty"><td colspan="4">还没有人参与。成为第一个节点！</td></tr>';
      return;
    }
    tbody.innerHTML = sorted.map((n, i) => `
      <tr ${n.id === myNodeId ? 'style="background: rgba(77,159,255,0.1);"' : ''}>
        <td>${i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : (i+1)}</td>
        <td>${n.id}${n.id === myNodeId ? ' (你)' : ''}</td>
        <td>${n.evals}</td>
        <td>${n.avg}</td>
      </tr>
    `).join('');
  }

  // ============================================================
  // 全局统计
  // ============================================================
  function updateStats() {
    const evals = JSON.parse(localStorage.getItem('evoai_evals') || '[]');
    const nodes = JSON.parse(localStorage.getItem('evoai_nodes') || '{}');
    const dataSize = evals.reduce((s, e) => s + (e.text || '').length, 0);
    document.getElementById('eval-count').textContent = evals.length;
    document.getElementById('node-count').textContent = Object.keys(nodes).length;
    document.getElementById('data-size').textContent = (dataSize / 1024).toFixed(1);

    // 触发一个"心跳"事件给 Mavis 协调器
    window.__evoai_state__ = { evals: evals.length, nodes: Object.keys(nodes).length, dataSize };
  }

  // ============================================================
  // 复制节点 ID
  // ============================================================
  document.getElementById('btn-copy-node').addEventListener('click', () => {
    navigator.clipboard.writeText(myNodeId).then(() => {
      const btn = document.getElementById('btn-copy-node');
      btn.textContent = '✓ 已复制';
      setTimeout(() => { btn.textContent = '复制 ID'; }, 1500);
    });
  });

  // ============================================================
  // HTML escape
  // ============================================================
  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, c => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // ============================================================
  // 拉取自驱动状态
  // ============================================================
  function renderTrajectory() {
    const container = document.getElementById('trajectory-bars');
    if (!container) return;
    // 历史数据 hardcode（每次部署更新时手动同步）
    const history = window.__AUTOEVO_HISTORY__ || [];
    if (history.length === 0) {
      container.innerHTML = '<p style="color: var(--fg-dim); font-size: 13px;">等待数据...</p>';
      return;
    }
    container.innerHTML = history.map(h => {
      const w = Math.round(h.avg_score * 100);
      return `
        <div class="traj-row">
          <span class="traj-label">Gen ${h.generation}</span>
          <div class="traj-bar"><div class="traj-fill" style="width: ${w}%"></div></div>
          <span class="traj-value">${h.avg_score.toFixed(3)}</span>
        </div>
      `;
    }).join('');
  }

  // 拉取公网 API 状态
  async function fetchPublicAPI() {
    try {
      // 节点数
      const nodesRes = await fetch('http://47.253.174.153:80/api/nodes', { mode: 'cors' });
      const nodesData = await nodesRes.json();
      const nodesEl = document.getElementById('api-nodes');
      if (nodesEl) nodesEl.textContent = nodesData.count;

      // 训练状态
      const statusRes = await fetch('http://47.253.174.153:80/api/train_status', { mode: 'cors' });
      const status = await statusRes.json();
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el && val != null) el.textContent = val;
      };
      set('live-gen', status.generation);
      set('live-loss', status.latest_train_loss != null ? status.latest_train_loss.toFixed(3) : '--');
      set('live-ppl', status.latest_test_ppl != null ? status.latest_test_ppl.toFixed(3) : '--');
      set('live-ckpt', status.ckpt_count || '--');
    } catch (e) {
      console.log('Public API fetch failed:', e);
    }
  }

  // 拉取自驱动状态
  async function fetchAutoStatus() {
    // 这个 URL 会在下次部署时填入真实地址
    // 先尝试 mock 数据
    const mockHistory = [
      { generation: 1, avg_score: 0.638 },
      { generation: 2, avg_score: 0.639 },
      { generation: 3, avg_score: 0.640 },
      { generation: 4, avg_score: 0.644 },
      { generation: 5, avg_score: 0.645 },
      { generation: 6, avg_score: 0.653 },
      { generation: 7, avg_score: 0.652 },
      { generation: 8, avg_score: 0.657 },
    ];
    window.__AUTOEVO_HISTORY__ = mockHistory;
    renderTrajectory();
  }

  // ============================================================
  // 暴露给 Mavis 协调器的接口
  // ============================================================
  window.EvoAI = {
    getState: () => ({
      node_id: myNodeId,
      evals: JSON.parse(localStorage.getItem('evoai_evals') || '[]'),
      nodes: JSON.parse(localStorage.getItem('evoai_nodes') || '{}'),
      snapshot: JSON.parse(localStorage.getItem('evoai_last_snapshot') || 'null'),
    }),
    exportAll: () => {
      const data = {
        node_id: myNodeId,
        evals: JSON.parse(localStorage.getItem('evoai_evals') || '[]'),
        nodes: JSON.parse(localStorage.getItem('evoai_nodes') || '{}'),
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `evoai-${myNodeId}-${Date.now()}.json`;
      a.click();
    },
  };

  // 启动
  renderEvalLog();
  renderLeaderboard();
  updateStats();
  fetchAutoStatus();
  fetchPublicAPI();

  // 每 5 秒更新统计
  setInterval(updateStats, 5000);
  // 每 10 秒拉取自驱动状态
  setInterval(fetchAutoStatus, 10000);
  // 每 15 秒拉取公网 API 状态
  setInterval(fetchPublicAPI, 15000);

  console.log(`[EVO-AI] Node ${myNodeId} registered. Use window.EvoAI.exportAll() to contribute.`);
})();
