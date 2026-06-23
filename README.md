# excel-to-html-slides

> **一句话：把 Excel/CSV 丢进来，出来一份可以直接拿去汇报的 HTML 幻灯片。**
>
> **One sentence: Drop a spreadsheet in, get a presentation-ready HTML slide deck out.**

---

## 这到底解决了什么问题？

企业在做数据汇报时永远卡在这里：

```
老板说："把上个月的订单/销售/库存数据整理一下，下午开会用。"
你：  导出 Excel → 调格式 → 做图表 → 贴 PPT → 调颜色 → 导出 PDF
结果：两小时过去了，格式还不对。
```

**excel-to-html-slides 把这个流程变成 30 秒。**

---

## 为什么不直接让 AI Agent 生成？

好问题。答案是：**你可以，但 excel-to-html-slides 解决了 Agent 做不好的几件事。**

### 壁垒 1：反 AI 同质化设计 🎨

直接让 Agent 生成 HTML 报告，100 次里有 95 次是同一个样子：

> 紫色渐变 + 白色卡片 + 圆角 + 无衬线字体 = **所有 AI 生成的报告看起来都一样**

excel-to-html-slides 内置 **18 种经过策划的独特视觉风格**，覆盖：

| 风格 | 适合场景 |
|------|----------|
| `retail-pulse` | 电商运营、销售日报 |
| `boardroom-light` | 董事会、高管汇报 |
| `command-center` | 风险管控、运维复盘 |
| `ops-ledger` | 采购、库存、财务流水 |
| `ink-wash` | 水墨留白，中国风高管汇报 |
| `terminal-green` | 终端绿屏，极客/运维感 |
| `neon-noir` | 霓虹夜市，消费/电商品牌 |
| `swiss-grid` | 瑞士国际主义，咨询/战略 |
| `corporate-navy` | 财富 500 董事会风格 |
| `data-ink` | Tufte 高密度，数据分析师专属 |
| *（共 18 种，详见 style-presets.md）* | |

每种风格都有独立的配色系统、字体层级、图表语言和排版节奏——**不是换色那么简单**。

### 壁垒 2：企业级口径确定性 📐

Agent 每次对"毛利率"的理解可能不一样。excel-to-html-slides 的 Python 脚本把企业常用口径**写死在代码里**：

- 退货率 = 退款订单数 / 总订单数（不含取消）
- 完成率 = 已完成 / (总订单 - 已取消)
- 预算差异率 = (实际 - 预算) / 预算 × 100%

同一份 Excel，跑 1000 遍，出来的数字一模一样。**这是审计级需求，不是效率需求。**

### 壁垒 3：零 Token 批量自动化 🔄

| 场景 | Agent 直接做 | excel-to-html-slides |
|------|--------------|---------------------|
| 偶尔分析一份数据 | ✅ 更灵活 | ⚠️ 够用 |
| 每周一自动出 50 个分公司报告 | ❌ 成本和一致性扛不住 | ✅ 一行脚本 cron 跑 |
| 固定口径周期性报告 | ❌ 每次口径可能漂 | ✅ 确定性输出 |
| 离线环境/内网 | ❌ 需要 API | ✅ 纯本地 Python |

### 壁垒 4：渐进式工作流，省 70% 上下文 🧠

excel-to-html-slides 的 `SKILL.md` 采用**渐进式披露**架构——Agent 只在需要时才加载对应参考文件，避免把 10 个参考文档一次性塞进上下文窗口。

---

## 支持哪些业务场景？

| 数据域 | 谁用 | 输出什么 |
|--------|------|----------|
| `ecommerce-orders` | 电商/运营专员 | GMV 趋势、品类贡献、渠道分析、退货预警 |
| `finance-expense` | 财务专员 | 营收利润、预算差异、主体排行、风险暴露 |
| `crm-pipeline` | 销售专员 | 管线漏斗、销售业绩、来源质量、僵尸商机 |
| `erp-inventory` | 仓储/采购专员 | SKU 分析、缺货预警、出入库趋势 |
| `hr-attendance` | 人事专员 | 部门对比、考勤分布、绩效分析 |
| `support-tickets` | 客服专员 | 工单量、解决率、SLA、满意度 |
| `survey-feedback` | 市场专员 | 评分分布、群体对比、NPS、选择题统计 |
| `devops-demand-pool` | 研发 PM | 需求漏斗、分类健康度、负责人负载 |
| `generic-table` | 数据专员 | 交叉分析、异常检测、趋势、结构贡献 |

---

## 快速开始

### 安装

```bash
# WorkBuddy
/plugin marketplace install excel-to-html-slides

# 或手动安装
git clone https://github.com/shanjinki/excel-to-html-slides.git ~/.workbuddy/skills/excel-to-html-slides/
```

### 使用

**方式一：脚本直出（最快）**

```bash
python3 scripts/generate_report.py 订单数据.xlsx \
  --requirement "分析电商订单，突出GMV趋势和退货风险" \
  --style retail-pulse \
  --output 报告.html
```

**方式二：让 AI Agent 帮你**

> "用 excel-to-html-slides skill，分析 `/path/to/数据.xlsx`，生成管理层汇报 HTML，风格选 retail-pulse。"

Agent 会自动：profile → 识别业务域 → 选风格 → 生成报告 → 质量检查。

---

## 技术特性

- ✅ **零依赖输出**：生成的 HTML 是自包含单文件，内联 CSS/JS，无需构建
- ✅ **离线可用**：纯本地 Python，不需要任何 API 调用
- ✅ **跨 Agent 兼容**：支持 WorkBuddy、Claude Code、Codex、Gemini CLI
- ✅ **响应式**：桌面和移动端均可浏览
- ✅ **质量检查内置**：输出前自动检查空值、口径、图表、行动建议

---

## 示例

`examples/` 目录包含真实场景的示例报告（使用合成数据）：
- `sample_demand_report.html` — DevOps 需求池分析报告
- `sample_finance_report.html` — 财务多主体对比报告
- `sample_ecommerce_report.html` — 电商订单分析报告

---

## 开源协议

MIT License — 免费使用，也欢迎提 PR 补充更多业务域分析器。

---

**excel-to-html-slides** — *Spreadsheets in, presentation-ready HTML out.*

