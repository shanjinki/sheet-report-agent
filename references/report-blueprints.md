# Report Blueprints

Use this file after profiling a table. A blueprint is the analytical contract for the report: what questions to answer, which columns matter, which visuals to use, and what recommendations should look like.

The DevOps demand-pool sample is only one scenario. Always select the blueprint from the user's spreadsheet and request, not from the example files in this repository.

## Universal Report Frame

Every report, regardless of table type, should include:

1. **Executive summary**: 3-5 data-grounded conclusions.
2. **KPI row**: the few numbers the audience must remember.
3. **Structure / mix analysis**: where records, amount, risk, or quality concentrate.
4. **Trend or lifecycle analysis**: use date/status/stage fields when present.
5. **Exception / risk / opportunity list**: not just averages.
6. **Action recommendations**: what to do next, who should decide, what to verify.
7. **Assumptions**: field mapping, missing fields, filters, excluded rows.

If the table has no obvious business domain, use the generic table blueprint first, then suggest what extra fields would unlock deeper analysis.

## Domain Selection

Score a blueprint higher when the table contains the listed field signals.

| Blueprint | Strong signals |
| --- | --- |
| Ecommerce orders | `订单`, `支付金额`, `GMV`, `SKU`, `商品`, `店铺`, `平台`, `退款`, `地区`, `下单时间` |
| Ecommerce reviews | `评价`, `评分`, `星级`, `评论`, `差评`, `商品`, `门店`, `客服`, `售后` |
| CRM leads/opportunities | `客户`, `线索`, `商机`, `阶段`, `销售`, `预计金额`, `赢单`, `跟进`, `来源` |
| ERP inventory/procurement | `物料`, `库存`, `入库`, `出库`, `仓库`, `供应商`, `采购`, `周转`, `缺货` |
| Finance/expense/reconciliation | `费用`, `成本`, `收入`, `预算`, `实际`, `差异`, `发票`, `付款`, `部门`, `科目` |
| HR/attendance/performance | `员工`, `部门`, `岗位`, `考勤`, `绩效`, `工时`, `入职`, `离职`, `薪资` |
| Customer service/support tickets | `工单`, `客服`, `处理时长`, `满意度`, `投诉`, `问题类型`, `响应`, `解决` |
| Survey/offline collection | `问卷`, `选项`, `提交时间`, `姓名`, `部门`, `城市`, `满意度`, `反馈` |
| DevOps demand/project list | `需求`, `工作项`, `状态`, `优先级`, `经办人`, `产品负责人`, `迭代`, `版本`, `预计上线`, `一级分类`, `业务专项` |
| Generic table | none of the above dominates |

## Blueprint: Ecommerce Orders

### Field mapping

- Order ID: `订单号`, `订单ID`, `Order ID`
- Date: `下单时间`, `支付时间`, `日期`
- Amount: `支付金额`, `订单金额`, `GMV`, `实付金额`
- Refund: `退款金额`, `退款状态`, `售后状态`
- Product: `商品`, `SKU`, `SPU`, `品类`
- Channel: `平台`, `店铺`, `渠道`
- Region: `省份`, `城市`, `地区`
- Customer: `用户`, `会员`, `客户ID`

### Modules

1. GMV/order/customer/AOV KPI cards.
2. Daily or weekly order and GMV trend.
3. Product/category/channel/region contribution.
4. Refund or abnormal order analysis.
5. Top opportunities and high-risk products.
6. Action plan: promotion, assortment, pricing, inventory, service recovery.

### Insight patterns

- High revenue + high refund = urgent product/service risk.
- High order count + low AOV = bundling or upsell opportunity.
- Concentrated GMV by SKU/channel = dependency risk.
- Region growth divergence = localized campaign or logistics issue.

## Blueprint: Ecommerce Reviews

### Field mapping

- Rating: `评分`, `星级`, `rating`
- Text: `评论`, `评价内容`, `反馈`, `review`
- Product/store: `商品`, `SKU`, `店铺`, `门店`
- Date: `评价时间`, `创建时间`
- Issue/category: `问题类型`, `标签`, `差评原因`

### Modules

1. Review count, average rating, negative share.
2. Rating distribution.
3. Product/store issue ranking.
4. Negative-topic or keyword themes.
5. Representative excerpts when privacy-safe.
6. Product/service improvement actions.

## Blueprint: CRM Leads And Opportunities

### Field mapping

- Customer/account: `客户`, `公司`, `Account`
- Lead/opportunity: `线索`, `商机`, `Opportunity`
- Stage/status: `阶段`, `状态`, `Stage`
- Owner: `销售`, `负责人`, `Owner`
- Amount: `预计金额`, `合同金额`, `ARR`, `MRR`
- Source: `来源`, `渠道`
- Next action/date: `下次跟进`, `跟进时间`, `预计成交`

### Modules

1. Leads, opportunities, pipeline amount, win/conversion rate.
2. Stage funnel and leakage points.
3. Sales owner performance and load.
4. Source/channel quality.
5. Stale opportunities and no-next-step risks.
6. Forecast and follow-up recommendations.

## Blueprint: ERP Inventory Or Procurement

### Field mapping

- Item/SKU: `物料`, `SKU`, `商品编码`
- Inventory: `库存`, `可用库存`, `现存量`
- In/out: `入库`, `出库`, `销量`, `消耗`
- Warehouse: `仓库`, `库位`
- Supplier: `供应商`
- Cost/value: `成本`, `金额`, `库存金额`
- Date: `日期`, `入库时间`, `出库时间`

### Modules

1. SKU count, inventory value, stockout risk, overstock risk.
2. Warehouse/category/supplier concentration.
3. Inbound/outbound movement trend.
4. Exception list: negative stock, zero stock, long-tail overstock.
5. Action plan: replenish, clear stock, supplier follow-up, data correction.

## Blueprint: Finance / Expense / Reconciliation

### Field mapping

- Amount: `金额`, `费用`, `收入`, `成本`, `预算`, `实际`
- Category: `科目`, `费用类型`, `项目`, `部门`
- Date: `日期`, `月份`, `付款时间`
- Status: `状态`, `审批状态`, `付款状态`
- Owner/vendor: `供应商`, `员工`, `部门`, `负责人`

### Modules

1. Total amount, budget/actual variance, paid/unpaid, approval status.
2. Department/category/project mix.
3. Monthly trend.
4. Top variance and exception items.
5. Aging or overdue analysis if dates/status exist.
6. Actions: approve, reconcile, investigate, budget reallocate.

## Blueprint: HR / Attendance / Performance

### Field mapping

- Employee: `员工`, `姓名`, `工号`
- Department/role: `部门`, `岗位`, `职级`
- Date: `日期`, `月份`, `入职`, `离职`
- Metric: `考勤`, `工时`, `绩效`, `得分`, `产出`
- Status: `状态`, `异常`, `审批`

### Modules

1. Headcount/records, department mix, key HR metric.
2. Attendance/performance distribution.
3. Department or role comparison.
4. Exception list and repeated issues.
5. Actions: manager follow-up, process adjustment, data verification.

## Blueprint: Customer Service / Support Tickets

### Field mapping

- Ticket: `工单`, `单号`, `Case`
- Status: `状态`, `解决状态`
- Owner: `客服`, `处理人`, `负责人`
- Category: `问题类型`, `渠道`, `产品`
- Time: `创建时间`, `响应时间`, `解决时间`, `处理时长`
- Satisfaction: `满意度`, `评分`, `评价`

### Modules

1. Ticket volume, resolution rate, average response/handling time.
2. Category and channel mix.
3. SLA breach or aging analysis.
4. Owner workload and performance.
5. Top issue root causes.
6. Actions: staffing, knowledge base, product fix, escalation.

## Blueprint: Survey / Offline Collection

### Field mapping

- Respondent/segment: `姓名`, `部门`, `城市`, `人群`, `门店`
- Date: `提交时间`, `日期`
- Rating: `满意度`, `评分`, `NPS`
- Choice: option columns, multiple-choice answers
- Text: `反馈`, `建议`, `备注`, `原因`

### Modules

1. Response count and segment coverage.
2. Score / rating distribution.
3. Segment comparison.
4. Choice ranking.
5. Representative comments or themes when privacy-safe.
6. Actions: policy, product, service, communication improvements.

## Blueprint: DevOps Demand / Project List

Use this blueprint for requirement/task exports from DevOps, Jira, TAPD, ZenTao, Feishu project, or custom R&D systems. This is the repository's example scenario, not the whole product.

### Field mapping

- ID: `编号`, `ID`, `Key`, `工作项ID`
- Title: `标题`, `需求标题`, `Summary`, `Name`
- Description: `描述`, `需求描述`, `Description`
- Status: `状态`, `Status`
- Priority: `优先级`, `Priority`, `业务优先级`
- Category: `一级分类`, `业务线`, `模块`, `系统`, `需求分类`
- Subcategory: `二级分类`, `三级分类`, `业务专项`, `专题`
- Owner: `经办人`, `负责人`, `Assignee`
- Planned date: `预计上线时间`, `预计结束时间`, `计划完成时间`
- Created date: `创建时间`, `提出时间`

### Modules

1. Effective demand, released, backlog, in-progress, paused.
2. Lifecycle funnel.
3. Category health sorted by release rate.
4. Special-project drilldown.
5. Owner load and blocked-stage risks.
6. Actions: review resources, priority pruning, data hygiene, staffing.

## Blueprint: Generic Business Table

Use when no domain dominates or when the user asks for exploratory analysis.

### Modules

1. Dataset overview: rows, columns, date range, likely primary fields.
2. Data quality: missingness, duplicated-looking IDs, empty categories.
3. Key categorical distributions.
4. Numeric summaries and outliers.
5. Trend by detected date column if available.
6. Cross-tab between the strongest category and the strongest status/segment field.
7. Recommended next questions based on the table's fields.

### Insight patterns

- A category with high concentration may represent dependency or focus.
- A field with high missingness may invalidate downstream conclusions.
- A numeric outlier should be listed as an exception, not hidden in an average.
- A date range without recent records should be called out.
