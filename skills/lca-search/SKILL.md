---
name: lca-search
description: "Searches 12 LCA databases for carbon footprint data, emission factors, and environmental impact datasets. Triggers on specific material names ('304 stainless steel', 'HDPE', 'PA66-GF30', '热轧钢', '聚丙烯'), LCA terms ('carbon footprint', 'emission factor', 'GWP', '碳足迹', '排放因子', '碳排放'), or requests to find environmental data for materials or processes. Does NOT trigger for general web search or non-LCA tasks."
---

# LCA 数据库搜索

## 数据库是怎么组织的

LCA 数据库按**工艺过程**建模，不是按商品名索引。数据库里没有"热轧卷"这个条目——有的是"hot rolling, steel coil, blast furnace route"这样的工艺活动描述。搜索本质上是把用户说的"东西"翻译成数据库里的"工艺过程"。

每个数据集有两个名字：`name`（工艺活动名）和 `ref_product`（参考产品，即这个工艺的产出物）。两者经常不一样——"氢氧化钠,离子膜法"的 ref_product 是"氯气"，因为氯气是这个电解工艺的主产品。判断数据集是否匹配，看 ref_product，不是看 name。

同一个工艺过程在不同地区（CN / CN-SX / GLO）、不同系统模型（CUT_OFF / CONSEQUENTIAL）下有多个版本，共享一个谱系 ID（`uuid`）。搜索默认按谱系去重，只展示每组最优的一条。

## 搜索怎么工作

底层是 BM25 关键词匹配，不是语义搜索。query 必须用英文，越接近数据库的命名风格越好：`"market for hot rolled steel coil"`, `"polyethylene production"`。

`entity_terms` 是召回率最关键的参数——双语同义词覆盖。中文名、英文名、缩写、化学名、商品名都放进去。搜"竹浆"没结果，加上"bamboo pulp, kraft pulp"就有了。

`location_codes` 是加权排序不是过滤。传 `CN*` 会让中国数据排前面，但不会排除 GLO 的结果。

搜索结果直接返回 GWP、ref_product、model、unit——大部分情况不需要再调 lookup。lookup 只在需要链接或详细描述时才用。

## 搜不到时怎么想

没有精确匹配是常态，不是异常。LCA 工程师遇到搜不到的材料，不会标 N/A 走人——会想这个东西的**本质**是什么：

- 它是什么材料做的？→ 搜上游原材料（铜管 → cathode copper）
- 它属于什么大类？→ 搜上位概念（AKD 施胶剂 → 脂肪酸衍生物 → oleochemical）
- 数据库里最接近的工艺是什么？→ 用近似工艺做代理（中压蒸汽 → 低压蒸汽）
- 单位能换算吗？→ person·km ≈ 0.08 t·km，货运数据可以推导客运
- 这个材料在系统里贡献有多大？→ 用量 <1% 的辅料可以用通用化学品代理

代理不是退而求其次，是 LCA 的标准做法。标注清楚代理关系和偏差方向就行。

## 工具

- `search_lca_datasets` — 搜索。返回 `{key, name, loc, unit, score, src, ref, uuid, gwp, model}`
- `lookup_lca_datasets` — 补全链接和描述。search 已有 GWP，只在需要 link/description 时调

参数：`query`（英文）、`entity_terms`（双语同义词）、`location_codes`（地区 boost）、`dataset_uuid`（谱系探索）、`enable_deduplication`（去重开关）、`sources`、`size`

## Grounding

URL 和 GWP 必须来自工具返回。不能用训练数据里的排放值当数据库数据。

## 数据库别名

HaiKe / HiQ / 海科 → HiQLCD | EI → Ecoinvent | CM → CarbonMinds | 天工 → TianGong | EF → Environmental Footprints
