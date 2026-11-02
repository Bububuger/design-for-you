# Design For You

为本地技能 `/find-design-for-this` 维护的**设计灵感站点池**。结构化清单 + 席位制 + Issue 投喂闭环，替代「只靠 Chrome 书签字符串匹配」。

## 架构一览

```
STATUS.md 悬赏单 ──► Grok Bot / PA / 手机投喂
                         │
                         ▼  开 Issue [inbox]（标题=URL；正文可写 track: video）
                   GitHub Issues
                         │
                         ▼  inbox.yml
                   triage.py 初筛（按 track 分轨）
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   sites.yaml      videos.yaml      graveyard
   (web 轨)         (video 轨)      (共用墓碑)
         │               │
         └───────┬───────┘
                 ▼  pool.py select --track web|video（各 4+1）
              logs/*.jsonl
                 │
                 ▼  health.yml 每周
        晋升 / 清退 / 探活 / 刷新 STATUS.md（双表）
```

- **Web Core**（`sites.yaml`）：分类席位制，合计建议 ≤30；单次检索最多取 4 个。  
- **Web Candidate**：上限 20；单次检索最多搭车 1 个（4+1）。  
- **Video Core**（`videos.yaml`）：`ui-motion`≤4、`launch-demo`≤6、`storyboard`≤4、`gen-style`≤4（合计 ≤18）；与 web **互不抢席**。  
- **Video Candidate**：上限 12；检索仍 4+1，但只从 `videos.yaml` 取。  
- **logs/**：只追加回执，避免与配置写冲突。  
- **graveyard.yaml**：拒收/清退墓碑（web/video 共用；video 拒收原因可用 `video_*` 前缀）。  
- **版权**：池内多为外链学习参考，不提供免版权再分发素材。

## 席位配额

### Web

| 分类 | 上限 | 说明 |
| :--- | ---: | :--- |
| product-flow | 10 | 真实产品界面与动线 |
| component | 12 | 单部件 / 模式画廊 |
| landing | 8 | 整站/营销落地页（当前超配，**冻结纯新增**；仅 web） |
| system | 4 | DESIGN.md / token / 规范层 |
| candidate | 20 | 待 4+1 实测转正 |

### Video

| 分类 | 上限 | 说明 |
| :--- | ---: | :--- |
| ui-motion | 4 | 界面动效 / micro-interaction 实录 |
| launch-demo | 6 | 产品发布 / demo 成片灵感 |
| storyboard | 4 | 分镜 / 叙事结构参考 |
| gen-style | 4 | 生成视频风格参考 |
| candidate | 12 | 待 4+1 实测转正 |

## PA 投喂协议（外部助理只做这件事）

1. 读根目录 [`STATUS.md`](./STATUS.md)：看哪个品类缺站、悬赏词、是否冻结 landing。  
2. 开 Issue：  
   - **标题**：完整 URL（如 `https://example.com/`）  
   - **标签**：`inbox`  
   - **正文**：推荐原因；可选写观察到的 `covers`（如 `data-table, filter-builder`）  
   - **视频轨**：正文加 `track: video` 与 `kind: launch-demo`（或 `ui-motion` / `storyboard` / `gen-style`）；无 `track` 默认 web  
3. 只需仓库 **Issues: Read & Write**（公开仓）；不要直接改 YAML。  
4. Actions 会评论结论并关单。非白名单作者的 Issue 会被拒绝关闭。

## 白名单与 Secrets

| 名称 | 用途 |
| :--- | :--- |
| `INBOX_ALLOWLIST` | 逗号分隔的 GitHub login；默认始终含 `Bububuger`。可配为 Actions **Variable** 或 Secret。 |
| `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY` | 可选。有则 `triage.py` 用轻量模型生成 `covers` / `search_hint`；无则规则打标并标 `needs_human`。 |

工作流权限：`inbox.yml` / `health.yml` 需能 `contents: write` 与 `issues: write`（仓库 Settings → Actions → Workflow permissions）。

## 升降级规则（摘要）

- **晋升**：candidate 在近 N 次 4+1 实测中命中达标 → core（且对应 kind 有空席）。  
- **清退**：core 长期零命中或死链连续 3 周失败 → graveyard（`dead_site` / `low_signal`）。  
- **landing**：新站默认拒收；存量超配靠命中率末位淘汰。  
- 细则与 stub 见 `scripts/` 与 `.github/workflows/health.yml` 注释。

## 本地脚本

```bash
pip install -r requirements.txt

# 按查询选 4+1（默认 web；视频轨加 --track video）
python scripts/pool.py select --query "data-table filter"
python scripts/pool.py select --track video --query "launch-demo motion"

# 写回执
python scripts/pool.py log --query "..." --hits id1,id2 --misses "data-table"

# 刷新 STATUS.md（同时扫 sites.yaml + videos.yaml）
python scripts/triage.py refresh-status

# 初筛单个 URL（本地调试；视频轨可 --track video 或正文写 track: video）
python scripts/triage.py triage --url https://example.com/ --reason "..."
python scripts/triage.py triage --track video --url https://example.com/ --reason "kind: launch-demo"
```

Chrome 书签差量导入：见 `pool.py` 中 `scan_chrome_bookmarks_diff` stub（路径约定写在函数文档串）。

## 关联

- 本地技能：`~/.agents/skills/find-design-for-this/SKILL.md`（数据源将切到本仓本地克隆）  
- 上游索引：`upstreams.yaml`（如 347 Design Inspiration Sites）
