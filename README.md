# Garmin Data Analyzer Skill

> Analyze your Garmin Connect export data and get personalized health & fitness insights.
> 解析 Garmin Connect 导出数据，获取个性化健康与运动洞察。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Cross-Platform](https://img.shields.io/badge/Platform-Any-green.svg)]()

---

## What It Does / 功能介绍

This skill analyzes Garmin Connect export ZIP files and generates structured insights about:

- **Daily Wellness** — Steps, calories, heart rate, stress, Body Battery, SpO2, respiration
- **Sleep Quality** — Sleep stages, scores, duration, sleep stress, respiration
- **Training Status** — Training status distribution, overtraining detection
- **Fitness Assessment** — Fitness age vs chronological age, VO2 Max, BMI trends
- **Race Predictions** — 5K/10K/half marathon/marathon time predictions
- **Heart Rate Zones** — Zone configuration analysis and recommendations

本技能分析 Garmin Connect 导出 ZIP 文件，生成以下维度的结构化洞察：

- **日常健康** — 步数、卡路里、心率、压力、Body Battery、血氧、呼吸
- **睡眠质量** — 睡眠阶段、评分、时长、睡眠压力、呼吸
- **训练状态** — 训练状态分布、过度训练检测
- **体能评估** — 体能年龄、VO2 Max、BMI 趋势
- **跑步预测** — 5K/10K/半马/全马预测时间
- **心率区间** — 区间配置分析与建议

## Quick Start / 快速开始

```bash
# Analyze your Garmin data
python scripts/garmin_cli.py /path/to/your_garmin_export.zip

# Output to a specific file
python scripts/garmin_cli.py /path/to/your_garmin_export.zip -o my_report.md

# Quick summary to console
python scripts/garmin_cli.py /path/to/your_garmin_export.zip --summary

# JSON output for programmatic use
python scripts/garmin_cli.py /path/to/your_garmin_export.zip --json -o data.json
```

## How to Get Your Garmin Data / 如何获取 Garmin 数据

1. Go to [Garmin Connect](https://connect.garmin.com/)
2. Click your profile → **Account** → **Data Management**
3. Click **Request Data Export**
4. Wait for the email (usually 1-24 hours)
5. Download the ZIP file
6. Run this skill on it!

1. 访问 [Garmin Connect](https://connect.garmin.com/)
2. 点击个人资料 → **账户** → **数据管理**
3. 点击 **请求数据导出**
4. 等待邮件（通常 1-24 小时）
5. 下载 ZIP 文件
6. 用本技能分析！

## Zero Dependencies / 零依赖

This tool uses **only Python standard library** — no `pip install` needed:

- `json` — Parse Garmin JSON files
- `zipfile` — Extract export archives
- `statistics` — Compute averages and trends
- `dataclasses` — Structured data models
- `argparse` — CLI interface

## Cross-Platform / 跨平台

Works on any AI platform that can execute Python:

| Platform | How to Use |
|----------|-----------|
| **WorkBuddy** | Use Bash tool, optional SVG Widget visualization |
| **Claude Code** | Run via Bash, display Markdown directly |
| **ChatGPT** | Code Interpreter, optional matplotlib charts |
| **Cursor** | Run via terminal |
| **GitHub Copilot** | Run via terminal |

## Project Structure / 项目结构

```
garmin-data-analyzer/
├── SKILL.md                    # Skill entry point (cross-platform instructions)
├── README.md                   # This file
├── LICENSE                     # MIT License
├── scripts/
│   ├── garmin_parser.py        # Parse ZIP → structured data
│   ├── garmin_analyzer.py      # Analyze data → insights
│   ├── garmin_report.py        # Generate Markdown/summary report
│   └── garmin_cli.py           # CLI entry point
├── references/
│   ├── data_schema.md          # Garmin data format reference
│   ├── field_glossary.md       # Field name Chinese-English glossary
│   └── insight_rules.md        # Insight generation rules
└── examples/
    └── sample_report.md        # Example output report
```

## Sample Output / 示例输出

The generated report includes:

- **Overall Summary** — One-line health assessment
- **Top 5 Insights** — Most important findings sorted by severity
- **6 Analysis Modules** — Detailed metrics tables and insights per category
- **Actionable Recommendations** — What to do about each finding

Example insights:
- 🟡 "静息心率上升 — 近期 55 bpm，较之前 49 bpm 上升 11.9%"
- 🟢 "体能年龄优于实际年龄 — 比实际年轻 4.5 岁"
- 🔵 "心率区间已设置 — 确保基于最新测试结果"

## Supported Data / 支持的数据

| Priority | Data | Description |
|----------|------|-------------|
| P0 | UDSFile | Daily wellness (steps, HR, stress, BB, SpO2) |
| P0 | sleepData | Sleep stages, scores, naps |
| P0 | fitnessAgeData | Fitness age, VO2 Max, BMI |
| P0 | RunRacePredictions | Race time predictions |
| P0 | TrainingHistory | Training status |
| P0 | heartRateZones | HR zone configuration |
| P1 | Hydration, TrainingReadiness, Vo2Max, Endurance, Hill, ATL | Extended metrics |
| P2 | FIT workout files | Planned for v2 |

## License / 许可

MIT License — see [LICENSE](LICENSE)

## Contributing / 贡献

Issues and pull requests are welcome at [GitHub](https://github.com/COLINZH26/garmin-ai-skill).

---

*Made with ❤️*
