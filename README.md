
# EPLAN PDF I/O 表提取 — 配置驱动框架

## 设计理念

不同项目的 EPLAN 图纸结构各异（页眉、地址格式、页面布局），但提取 I/O 的逻辑是通用的。
本框架将 **变化的参数** 抽到 YAML 配置文件中，**不变的逻辑** 留在 Python 脚本里。
新项目只需改配置，不动脚本。

```
                 ┌─────────────────────────┐
                 │  project_config.yaml    │  ← 改这里适配新项目
                 │  (关键词/布局/地址规则)  │
                 └──────────┬──────────────┘
                            ▼
                 ┌─────────────────────────┐
                 │  extract_io.py          │  ← 永远不用改
                 │  (通用解析引擎)          │
                 └──────────┬──────────────┘
                            ▼
                 ┌─────────────────────────┐
                 │  PLC_IO_Table.xlsx      │  ← 输出格式统一
                 └─────────────────────────┘
```

## 配置文件结构

新项目来了，你只需要告诉我图纸关键词，我帮你生成这个配置：

```yaml
# project_config.yaml
project:
  name: "徐工模组&PACK装配线"  # 仅用于标识

# ========== 页面类型判定 ==========
page_detect:
  DI: ["数字量输入模块", "DI"]
  DQ: ["数字量输出模块", "DQ"]
  IOLINK: ["IOLINK_数字量可分配模块"]
  AI: ["模拟量输入", "PIW"]
  VALVE: ["亚德客阀岛", "阀岛", "Q17"]

# ========== 地址格式 ==========
address_patterns:
  DI: "I\\d{4}\\.\\d"          # I1000.0
  DQ: "Q\\d{4}\\.\\d"          # Q1000.0
  IOLINK_IN: "I\\d{4}\\.\\d"   # I4000.0
  IOLINK_OUT: "Q\\d{4}\\.\\d"  # Q4008.0
  VALVE: "Q17\\d{3}\\.\\d"     # Q17000.0
  AI: "PIW\\d{4}"              # PIW4110

# ========== 信号名格式 ==========
signal_patterns:
  IOLINK: "S\\d{4}_.+"         # S1006_感应托盘到位
  VALVE: "C\\d{4}_.+"          # C2052_夹爪气缸夹紧

# ========== 页面布局参数 ==========
# 每个页面的 I/O 表在 PDF 中的坐标特征
page_layout:
  DI:
    bit_label_y: 571        # "DI Bit X" 标签的 Y 坐标
    address_offset: 18      # 地址在 Bit 标签下方多少像素
    desc_offset: 110        # 描述在 Bit 标签下方多少像素
    columns: 8              # 每页几列
    col_width: 113          # 列宽（像素）
    start_x: 222            # 第一列的 X 中心位置
    bit_label: "DI Bit"     # Bit 标签文字

  DQ:
    bit_label_y: 178        # DQ 的 Bit 标签在上方
    address_offset: -22     # 地址在 Bit 标签上方
    desc_offset: 510        # 描述在 Bit 标签下方较远处
    columns: 8
    col_width: 113
    start_x: 222
    bit_label: "DO Bit"

# ========== 页眉噪声清洗 ==========
noise_patterns:
  - "日期\\s+设计\\s+审核\\s+批准\\s*"
  - "[\\u4e00-\\u9fff]{2,}基地\\s+[\\u4e00-\\u9fff]{2,}\\s*"
  - "项目编号:\\s*[^\\n]*"
  - "项目描述:\\s*[^\\n]*"
  - "页描述:\\s*图纸号:\\s*"
  - "数字量(输入|输出)模块 16位\\s+(DI|DQ)\\d+\\.0-(DI|DQ)\\d+\\.7\\s*"

# ========== 页码范围（可选，用于加速） ==========
# 留空则全 PDF 搜索
page_ranges:
  DI_start: 73
  DI_end: 88
  DQ_start: 90
  # ...
```

## 新项目适配标准流程

```
收到新图纸 PDF
       │
       ▼
Step 1 ─── 我打开前几页，看结构
           ├─ 页眉长什么样？ → 更新 noise_patterns
           ├─ DI/DQ 页文字是什么？ → 更新 page_detect
           ├─ 地址格式？ → 更新 address_patterns
           ├─ Bit标签在哪？ → 更新 page_layout
           └─ 阀岛信号名？ → 更新 signal_patterns
       │
       ▼
Step 2 ─── 我运行提取，给你看部分结果
       │
       ▼
Step 3 ─── 你检查，反馈问题 → 我调整配置
       │
       ▼
Step 4 ─── 确认无误 → 导出 Excel + 保存配置
```

## 引擎脚本结构（通用，永远不改）

```python
# extract_io.py - 通用提取引擎
import yaml, pymupdf, re, json
from openpyxl import Workbook

# 1. 加载配置
with open("project_config.yaml") as f:
    cfg = yaml.safe_load(f)

doc = pymupdf.open("drawing.pdf")

# 2. 页面分类 → 根据 cfg["page_detect"] 中的关键词匹配
for i in range(doc.page_count):
    text = doc[i].get_text()
    page_type = classify_page(text, cfg["page_detect"])

    # 3. 按类型调度到对应的解析器
    if page_type == "DI":
        records += parse_di_dq(page, i+1, "DI", cfg["page_layout"]["DI"], 
                               cfg["address_patterns"], cfg["noise_patterns"])
    elif page_type == "VALVE":
        records += parse_valve(page, i+1, cfg)

# 4. 生成 Excel（格式固定）
generate_excel(records, cfg)
```

## 适用场景

- 拿到 EPLAN 导出的矢量 PDF（非扫描件）
- 中文/英文/德文图纸均可（换关键词就行）
- 包含 DI、DQ、IOLINK、阀岛、AI 模块

## 已知局限

| 问题 | 说明 |
|------|------|
| 扫描件 PDF 不支持 | 需要用 OCR 引擎（marker-pdf），框架暂不覆盖 |
| 阀岛奇偶位仍需手动修正 | 奇数位"打开"文本提取受限 |
| AI 描述可能缺失 | 依赖图纸文本层质量 |

## 引用文件

### Step 3: 提取 DI/DQ（主控柜 + 远程IO）

**核心思路**：用 `page.get_text("dict")` 获取每个文本元素的 (x,y) 坐标，找到 "DI Bit X" / "DO Bit X" 标签作为列锚点，按列采集地址和设备描述。

```python
def parse_di_dq(page, page_num, is_di):
    """解析DI/DQ模块页"""
    items = get_text_items(page)  # (text, x0, y0, x1, y1)
    
    # 1. 找到所有 "DI Bit X" 或 "DO Bit X" 作为列锚点
    anchors = []
    for text, x0, y0, x1, y1 in items:
        m = re.match(r"^(DI|DO)\s+Bit\s+(\d+)$", text)
        if m:
            cx = (x0 + x1) / 2
            anchors.append((cx, int(m.group(2))))
    
    # 2. 按列分界（取相邻锚点中点）
    anchors.sort()
    cols = []
    for idx, (cx, bit) in enumerate(anchors):
        left = (anchors[idx-1][0] + cx)/2 if idx > 0 else cx - 55
        right = (anchors[idx+1][0] + cx)/2 if idx < len(anchors)-1 else cx + 55
        cols.append((left, right, cx, bit))
    
    # 3. 每列收集地址、设备标签、描述
    io_type = "DI" if is_di else "DQ"
    for left, right, cx, bit in cols:
        col_items = [(t, x0, y0) for t, x0, y0, x1, y1 in items
                     if left <= (x0+x1)/2 <= right]
        # 从col_items中提取 address, device_tag, description
```

**关键差异**：DI 和 DQ 页面的布局不同
- DI 页：Bit 标签在 y≈571，地址在 Bit 下方 y≈589，描述在 y≈681-701
- DQ 页：Bit 标签在 y≈178，地址在 Bit 上方 y≈156，描述在 y≈650-710

### Step 4: 提取 IOLINK DI 输入

IOLINK 页面（页码约 303~426）传感器信号分布在复杂插头图中：

```python
def parse_iolink_di(page, page_num):
    items = get_text_items(page)
    # 找到 I4xxx.x 地址
    addr_items = [(t, x0, y0) for t, x0, y0, x1, y1 in items
                  if re.match(r"^I\d{4}\.\d$", text) and x0 > 100]
    # 对每个地址，向右搜索信号名 SXXXX_ 和中文字符
    for addr_text, ax, ay in addr_items:
        nearby = [(t, x) for t, x0, y0, x1, y1 in items
                  if ax < (x0+x1)/2 < ax + 300 and abs(y0 - ay) < 60]
        # 从 nearby 中提取 S1006_感应托盘到位 等信号名
```

### Step 5: 提取阀岛 Q 输出

亚德客阀岛页面（约 427~442）结构更清晰，包含 CXXXX 信号名：

```python
def parse_valve_q(page, page_num):
    # 使用 sorted text 保留阅读顺序
    lines = page.get_text("text", sort=True).split("\n")
    # 寻找 Q17xxx 地址和 CXXXX_描述 对
    # 偶数位 = 夹紧/下降/旋转, 奇数位 = 打开/伸出
    for line in lines:
        q_addrs = re.findall(r"\bQ17\d{3}\.\d\b", line)
        sigs = re.findall(r"\b(C\d{4})_(\S+)", line)
        # 匹配 Q 地址到最近的 C 信号名
```

### Step 6: 合并数据并生成 Excel

```python
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = Workbook()
ws = wb.active
ws.title = "PLC IO 总表"

# 表头样式
header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
cat_fills = {
    "DI": PatternFill(start_color="D6E4F0", ...),  # 蓝色
    "DQ": PatternFill(start_color="E2EFDA", ...),  # 绿色
    "DQ (IOLINK)": PatternFill(start_color="C6EFCE", ...),
    "DQ (阀岛)": PatternFill(start_color="C6EFCE", ...),
    "DIO (IOLINK)": PatternFill(start_color="FFF2CC", ...),  # 黄色
    "AI": PatternFill(start_color="F2DCDB", ...),  # 红色
}

headers = ["序号", "IO类型", "地址(Address)", "符号名(Signal Name)",
           "描述(Description)", "所属模块", "机柜/区域", "图纸页码"]

# 按类型分组，每组插入分隔行
# 添加筛选器、冻结表头
```

### Step 7: 描述清洗

EPLAN 页眉页脚文字会混入描述中，需要正则清洗：

```python
noise_patterns = [
    (r"日期\s+设计\s+审核\s+批准\s*", ""),
    (r"徐工基地\s+徐工\s*", ""),
    (r"项目编号:\s*[^:]*", ""),
    (r"项目描述:\s*[^.]*\.0\s*", ""),
    (r"页描述:\s*图纸号:\s*", ""),
    (r"数字量(输入|输出)模块 16位\s+(DI|DQ)\d+\.0-(DI|DQ)\d+\.7\s*", ""),
    (r"页\s+", ""),
    (r"\s+", " "),
]
```

## 参考脚本

完整提取脚本位于项目目录下，主要包含：

| 脚本 | 功能 |
|------|------|
| `extract_di_dq.py` | 解析 DI/DQ 模块页面 |
| `extract_iolink.py` | 解析 IOLINK 分布式 IO |
| `extract_valve.py` | 解析亚德客阀岛 Q 输出 |
| `extract_ai.py` | 解析模拟量输入 |
| `generate_excel.py` | 合并数据生成带格式 Excel |

## ⚠️ 关键坑点（每次必查）

| # | 坑点 | 后果 | 检查方法 |
|---|------|------|---------|
| 1 | **阀岛 Q 点易遗漏** ⭐ | IOLINK 页面同时包含 I 和 Q 地址，但 Q 地址在单独的列或不同的页面上。**首次提取时用户验证发现 126 个阀岛 Q 点完全缺失**，这是真实的漏采事故 | 必须执行两遍全页扫描：① `re.findall(r"\bQ\d{4}\.\d\b", text)` 扫 IOLINK 页的 Q 输出通道（Q4xxx/Q5xxx）；② `r"\bQ17\d{3}\.\d\b"` 扫阀岛页（Q17xxx） |
| 2 | **DI 与 DQ 页面布局相反** | DI 的 Bit 标签在下方（y≈571），DQ 的 Bit 标签在上方（y≈178），统一 code 会导致数据全空 | 打印前几页 `(y0, text)` 确认布局位置后再写解析逻辑 |
| 3 | **IOLINK 文本碎片化** | S1006_感应托盘到位 被拆成 "S1006_感应托" 和 "盘到位" 两行 | 使用 `sort=True` 排序文本并跨行拼接 |
| 4 | **页眉噪声混入描述** | "日期 设计 审核 批准 徐工基地" 等页眉文字被当作设备描述 | 必须用 `noise_patterns` 正则清洗 |

## 验证清单（生成 Excel 后逐项检查）

- [ ] 总点数 ≈ 预期（根据图纸页数估算）
- [ ] 所有 DI 地址都有描述（非空）
- [ ] 所有 DQ 地址都有描述（非空）
- [ ] **阀岛 Q 点已包含**（搜索 Q17xxx 地址是否存在）
- [ ] IOLINK 输入有符号名（至少部分有）
- [ ] "预留"/"备用" 通道识别正确（不是空字段）
- [ ] 描述中没有 "日期 设计 审核 批准" 等页眉残留
- [ ] Excel 按 I/O 类型分组、颜色区分、可筛选

## 已知局限

| 问题 | 原因 | 建议 |
|------|------|------|
| IOLINK 信号名截断 | EPLAN 文本元素独立定位，SXXXX_后文本可能被分割 | 对照图纸手动补充完整符号名 |
| 阀岛奇偶位描述混同 | 奇数位"打开"文本与偶数位"夹紧"文本可能在同一行被合并 | 手动修正 Q17000.1 等为"夹爪气缸打开" |
| AI 模拟量描述缺失 | PIW 地址的描述以图形方式关联，文本层不可见 | 手动填写传感器名称 |
| 备用通道误标 | "预留"文本可能与相邻通道的描述混合 | 检查描述中包含"预留"的行 |

## 效果参考

处理 557 页 EPLAN PDF 产出：
- DI: 240 点, DQ: 96 点, IOLINK DI: 776 点, 阀岛 Q: 126 点, AI: 24 点
- 总计: 1,320 个 I/O 点
- Excel 文件大小: ~47KB

## ⚠️ 离线脚本的边界（重要！）

提取脚本 `scripts/extract_all_io.py` 是**静态规则匹配器**，它只能处理：
- 已经调好的、**同类型模板**的图纸
- 关键词、坐标范围、正则规则固定的场景

**以下场景必须联网找 Hermes 重新适配：**

| 场景 | 原因 |
|------|------|
| 图纸语言不同（英文/日文/德文） | 关键词（`数字量输入模块`→`Digital Input Module`）需重写 |
| I/O 地址格式不同（`%IW0.0` / `AI0`） | 正则匹配规则需调整 |
| 每页通道数不同（8位/16位/32位） | 列锚点逻辑需重算 |
| 阀岛型号/命名规则不同 | CXXXX/SXXXX 前缀可能不同 |
| 页面布局变化（Bit 标签位置偏移） | 坐标范围需重新标定 |
| 提取结果不全 / 描述错乱 | 规则有遗漏，需人工介入修正 |

### 正确工作流

```
新EPLAN图纸到手
       │
       ▼
  🔗 找 Hermes（需联网）
     分析图纸结构 → 调整脚本 → 运行验证 → 你验收
       │
       ▼
  ✅ 确认无误
       │
       ▼
  导出脚本到本地
  后续同类图纸可离线批量跑
       │
       ▼
  遇到不同模板／遗漏数据
       │
       ▼
  🔗 再找 Hermes 重新适配
```

> **核心原则：** 新模板找 AI 适配，批量重复用离线脚本。不要指望离线脚本能自动处理没见过的新图纸格式。

## 多项目适配

不同项目的 EPLAN 图纸可能有差异：

1. **页眉文字不同**：在 `noise_patterns` 中增加新的清洗规则
2. **I/O 地址范围不同**：调整正则表达式中的数字范围
3. **阀岛型号不同**：调整信号名匹配模式（SXXXX, CXXXX 等前缀可能不同）
4. **页面布局差异**：先打印几页的位置数据，调整 column bounds 参数

## 运行环境注意事项

### Windows / PowerShell 5.1 兼容

本 Hermes Desktop CN 环境运行在 PowerShell 5.1 上，有以下限制：

| 限制 | 表现 | 替代方案 |
|------|------|---------|
| **不支持 `&&`** | 管道链式操作符不可用 | 用 `;` 分隔命令 |
| **Python f-string 在 -c 参数中报错** | 花括号 `{}` 被 PowerShell 解释 | 写 `.py` 文件执行，或用 `%` 格式化 |
| **Set-Content 写入含中文路径的 Python 文件乱码** | 默认 ANSI 编码破坏 UTF-8 中文 | 加 `-Encoding UTF8` |
| **SSL 证书问题** | `urllib.urlopen` 连 GitHub 失败 | 用 `curl -sk` 替代，或 `context=ssl._create_unverified_context()` |

推荐做法：将 Python 代码写成 `.py` 文件（用 `Set-Content -Encoding UTF8`），再执行：

```powershell
Set-Content -Path "$env:TEMP\script.py" -Encoding UTF8 -Value @'
import pymupdf
# ...
'@
python3.14 "$env:TEMP\script.py"
```

### GitHub 无 git/gh 环境上传

当系统没有安装 git/gh CLI 时，通过 GitHub Contents API 上传。参考 `references/github-api-upload.md`。


## GitHub 仓库

本技能已发布到公开仓库，方便多设备同步和版本管理：

```
https://github.com/MSS-CMD/eplan-pdf-io-extraction
```

仓库内容：
- `README.md` — 项目文档（即本 SKILL.md 去掉 YAML 头的版本）
- `scripts/extract_all_io.py` — 完整提取脚本
- `docs/reference.md` — 速查表（与本地 `references/extract_iq.md` 同步）

**更新流程**：本地 skill 完善后，通过 GitHub Contents API 将对应文件同步到仓库。

## 引用文件

- `references/extract_iq.md` — 页面类型判定、地址范围、阀岛命名规则速查表
- `references/github-api-upload.md` — 无 git/gh 环境下通过 GitHub API 上传文件到仓库的方法
- `scripts/extract_all_io.py` — 完整可运行提取脚本（修改 `pdf_path` 即可用）