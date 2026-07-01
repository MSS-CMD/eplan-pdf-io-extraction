# EPLAN PDF I/O 表提取

从 EPLAN 生成的电气图纸 PDF（557页级）中，自动提取全部 PLC I/O 点，生成结构化 Excel 表格，用于 TIA Portal / 汇川 / 三菱 等 PLC 编程。

## 适用场景

- 电气调试工程师拿到 EPLAN PDF 图纸，需要整理 I/O 表用于编程
- PDF 为 EPLAN 导出的矢量 PDF（非扫描件），每页包含 8 或 16 个 I/O 通道
- 图纸结构包含：主控柜 DI/DQ、远程 IO DI/DQ、IOLINK 分布式 IO、亚德客阀岛、模拟量输入

## 工作流程

### Step 1: 环境准备

```bash
pip install pymupdf openpyxl
```

### Step 2: PDF 探索与页面分类

先快速了解 PDF 结构：

```python
import pymupdf
doc = pymupdf.open("path/to/your.pdf")
print("总页数:", doc.page_count)

# 搜索 I/O 模块页面
for i in range(doc.page_count):
    text = doc[i].get_text()
    if "数字量输入模块 16位" in text:
        print(f"  DI模块: 第{i+1}页")
    elif "数字量输出模块 16位" in text:
        print(f"  DQ模块: 第{i+1}页")
    elif "IOLINK_数字量可分配模块" in text:
        print(f"  IOLINK DIO: 第{i+1}页")
    elif "亚德客阀岛" in text or "阀岛" in text:
        print(f"  阀岛: 第{i+1}页")
    elif "模拟量输入" in text:
        print(f"  AI模块: 第{i+1}页")
```

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
| 1 | **阀岛 Q 点易遗漏** | IOLINK 页面同时包含 I 和 Q 地址，但 Q 地址（Q4xxx/Q17xxx）不在同一位置 | 运行 `re.findall(r"\bQ\d{4}\.\d\b", text)` 和 `r"\bQ17\d{3}\.\d\b"` 全页扫描 |
| 2 | **DI 与 DQ 页面布局相反** | DI 的 Bit 标签在下方（y≈571），DQ 的 Bit 标签在上方（y≈178），统一code会全空 | 打印前几页 `(y0, text)` 确认位置后再写解析逻辑 |
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

## 多项目适配

不同项目的 EPLAN 图纸可能有差异：

1. **页眉文字不同**：在 `noise_patterns` 中增加新的清洗规则
2. **I/O 地址范围不同**：调整正则表达式中的数字范围
3. **阀岛型号不同**：调整信号名匹配模式（SXXXX, CXXXX 等前缀可能不同）
4. **页面布局差异**：先打印几页的位置数据，调整 column bounds 参数


## 引用文件

- `references/extract_iq.md` — 页面类型判定、地址范围、阀岛命名规则速查表
- `scripts/extract_all_io.py` — 完整可运行提取脚本（修改 `pdf_path` 即可用）
