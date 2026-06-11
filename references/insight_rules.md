# Insight Rules Reference / 洞察生成规则参考

This document describes the rules used by the Garmin Data Analyzer to generate health and fitness insights.

本文档描述 Garmin 数据分析器生成健康与运动洞察所使用的规则。

---

## Rule Categories / 规则类别

### A. Daily Wellness / 日常健康

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| A1 | Resting HR | RHR increased >5% vs previous 30 days | Warning | 静息心率上升 | 可能过度训练或恢复不足，建议适当休息 |
| A2 | Resting HR | RHR decreased >3% vs previous 30 days | Positive | 静息心率下降 | 有氧能力提升标志，保持当前节奏 |
| A3 | Steps | Steps increased >20% vs previous 30 days | Positive | 日均步数显著增加 | 活动量增加是好事，注意逐步增加避免受伤 |
| A4 | Steps | Steps decreased >20% vs previous 30 days | Warning | 日均步数明显下降 | 建议增加日常步行或低强度运动 |
| A5 | Body Battery | Avg daily net BB < -5 | Warning | Body Battery 入不敷出 | 关注睡眠质量和日间压力管理 |
| A6 | Body Battery | Avg daily net BB > +5 | Positive | Body Battery 恢复良好 | 恢复良好，可以适当增加训练强度 |
| A7 | Stress | Avg stress > 50 | Warning | 平均压力偏高 | 建议增加放松活动 |
| A8 | SpO2 | Avg SpO2 < 95% | Warning | 血氧饱和度偏低 | 可能与睡眠呼吸问题有关，建议咨询医生 |

### B. Sleep Quality / 睡眠质量

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| B1 | Deep sleep % | Deep < 15% of total | Warning | 深睡比例偏低 | 保持规律作息，避免睡前咖啡因和蓝光 |
| B2 | Deep sleep % | Deep >= 20% of total | Positive | 深睡比例良好 | 继续保持良好睡眠习惯 |
| B3 | Sleep score | Score < 60/100 | Warning | 睡眠评分偏低 | 关注睡眠环境和作息规律 |
| B4 | Sleep duration | Avg < 6 hours | Warning | 睡眠时长不足 | 建议提前入睡时间 |
| B5 | Sleep stress | Avg > 25 | Info | 睡眠期间压力偏高 | 睡前放松练习有助于降低睡眠压力 |

### C. Training Status / 训练状态

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| C1 | Training status | DETRAINING > 50% of recent period | Warning | 训练不足导致体能下降 | 建议逐步恢复规律训练 |
| C2 | Training status | OVERREACHING > 3 days | Critical | 可能过度训练 | 减少训练量，增加恢复日 |
| C3 | Training status | Dominant = PEAKING | Positive | 训练状态达到巅峰 | 适合在近期参加比赛或测试 |

### D. Fitness Assessment / 体能评估

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| D1 | Fitness age | Bio age > chronological + 5 | Warning | 体能年龄显著高于实际年龄 | 增加有氧训练，提升心肺功能 |
| D2 | Fitness age | Bio age < chronological - 5 | Positive | 体能年龄远优于实际年龄 | 继续保持当前运动习惯 |
| D3 | Fitness age | Bio age < chronological | Positive | 体能年龄优于实际年龄 | 保持规律运动 |
| D4 | Fitness age trend | Bio age decreasing over time | Positive | 体能年龄呈下降趋势（改善中） | 保持训练节奏 |
| D5 | Fitness age trend | Bio age increasing over time | Warning | 体能年龄呈上升趋势（退化中） | 需要恢复规律训练 |

### E. Race Predictions / 跑步预测

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| E1 | 5K time | Time improved > 5% vs first record | Positive | 5K预测时间显著缩短 | 保持当前训练计划 |
| E2 | 5K time | Time worsened > 5% vs first record | Warning | 5K预测时间增加 | 建议恢复规律跑步训练 |

### F. Heart Rate Zones / 心率区间

| # | Indicator | Condition | Severity | Insight | Recommendation |
|---|-----------|-----------|----------|---------|----------------|
| F1 | Zone width | Zone 4 width > 25 bpm | Info | Zone 4 区间较宽 | 建议通过乳酸阈值测试调整心率区间 |
| F2 | Zones config | Zones configured | Info | 心率区间已设置 | 确保基于最新测试结果设置 |

---

## Trend Detection / 趋势检测

### Period Comparison
- **Recent period**: Last 30 days of data
- **Comparison period**: 30 days before the recent period
- **Threshold**: >5% change = significant trend

### Trend Icons
- 🔺 **Up**: Value increased significantly
- 🔻 **Down**: Value decreased significantly
- ➡️ **Stable**: No significant change
- ⚠️ **Anomaly**: Unusual pattern detected

### Special Cases
- For running race predictions, time **decreasing** = performance **improving** (trend is inverted)
- For fitness age, bio age **decreasing** = **improving** (trend is inverted)
- For resting heart rate, RHR **decreasing** = **improving** (trend is inverted)

---

## Adding Custom Rules / 添加自定义规则

To add new insight rules:

1. Add the detection logic in the corresponding `analyze_*` method in `garmin_analyzer.py`
2. Create an `Insight` object with proper category, severity, and recommendations
3. Update this reference document with the new rule

添加新洞察规则：
1. 在 `garmin_analyzer.py` 对应的 `analyze_*` 方法中添加检测逻辑
2. 创建 `Insight` 对象，设置正确的类别、严重程度和建议
3. 更新本文档记录新规则
