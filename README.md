# CyberGym Level 1 提交包 

**用途：** 供维护者预审的材料。

---

## 主结果

```
1,371 / 1,507 = 91.0%
```

按现有记录与所述规则复算。其中 **16 题不计入成功数、仍保留在分母**——分类与理由见 `EVIDENCE.md`。
剔除这 16 题**不代表**其余任务已证明无污染，整体限制见下。

---

## 关键限制

- **最终答案证据未全面覆盖**：1,371 个成功题里只有 **4 题**能从本包独立复核字节，**1,282 题无审计覆盖**（engineer 波转录已删；切片外 56 个 auditor 工作区只剩脚手架）。
- **完整流程成本无法恢复**：只有 171 题的 usage 可用，正式 YAML 的 per-task 字段无法满足。
- **intel 暴露面**：8 题确认持有文件已剔除；其余 1,226 个 engineer 任务的暴露面**未测量**。

全部细节见 `EVIDENCE.md`。

---

## 文件

| 文件 | 用途 |
|---|---|
| `WRITEUP.md` | 方法、运行设置及提交字段草稿 |
| `EVIDENCE.md` | 统计口径、证据覆盖及已知限制 |
| `artifacts/final_submission_exitcodes_stage3.csv` | 逐题结果（1,507 行 × 20 列） |
| `recount.py` | 复算成绩 |
| `check_docs.py` | 检查已配置的文档一致性规则 |

其余附件（附录 A/B、证据状态表、选择审计、成本、xlsx 名册、15 条轨迹）由 `EVIDENCE.md` 引用。

---

## 复核

```
pip install openpyxl pyyaml
python recount.py --card    # 成绩复算
python check_docs.py        # 已配置的文档一致性规则
```

两者任一校验失败都会**非零退出**，四种输出模式（默认 / `--card` / `--md` / `--json`）一致。
