---
name: garmin-data-analyzer
version: 0.1.0
description: Analyze Garmin Connect export data and generate health/fitness insights
author: Colin
license: MIT
repository: https://github.com/COLINZH26/garmin-ai-skill
cross_platform: true
supported_platforms:
  - WorkBuddy
  - Claude Code
  - ChatGPT
  - Cursor
  - GitHub Copilot
---

# Garmin Data Analyzer Skill / Garmin 数据分析技能

Analyze your Garmin Connect export data to generate personalized health and fitness insights.
解析 Garmin Connect 导出数据，生成个性化健康与运动洞察。

## When to Use / 使用时机

Trigger this skill when the user:
- Mentions Garmin data, fitness tracking, or health data analysis
- Provides a Garmin Connect export ZIP file
- Asks about their health/fitness trends, sleep quality, training status, etc.
- Says "analyze my Garmin data", "解读我的 Garmin 数据", "分析运动数据"

当用户提及以下情况时触发：
- Garmin 数据、运动追踪、健康数据分析
- 提供了 Garmin Connect 导出的 ZIP 文件
- 询问健康/运动趋势、睡眠质量、训练状态等
- 说"分析我的 Garmin 数据"、"解读运动数据"

## Prerequisites / 前置条件

- Python 3.8+ (uses only standard library, no external dependencies)
- The scripts/ directory from this skill must be accessible
- User must have a Garmin Connect export ZIP file

## Steps / 执行步骤

### Step 1: Identify the ZIP File / 识别 ZIP 文件

Locate the user's Garmin Connect export ZIP file. It typically has a UUID-like name (e.g., `691cec90-d190-4e41-94f6-b90002a8b15a_1.zip`) and is 10-100MB in size.

确认用户的 Garmin Connect 导出 ZIP 文件路径。文件名通常为 UUID 格式，大小约 10-100MB。

### Step 2: Run the Analysis / 运行分析

Execute the CLI tool to parse and analyze the data:

```bash
python scripts/garmin_cli.py <path_to_zip> --output garmin_report.md
```

For a quick summary only:
```bash
python scripts/garmin_cli.py <path_to_zip> --summary
```

For JSON output (programmatic use):
```bash
python scripts/garmin_cli.py <path_to_zip> --json --output garmin_report.json
```

运行分析命令，生成报告。

### Step 3: Review the Report / 审查报告

Read the generated Markdown report file and present key findings to the user.

The report contains 6 analysis modules:
1. **Daily Wellness Overview** — Steps, calories, heart rate, stress, Body Battery, SpO2
2. **Sleep Quality Analysis** — Sleep stages, scores, duration, stress during sleep
3. **Training Status & Load** — Training status distribution, overtraining detection
4. **Fitness Assessment** — Fitness age vs chronological age, VO2 Max, BMI
5. **Running Race Predictions** — 5K/10K/Half/Marathon predictions and trends
6. **Heart Rate Zones** — Current zone configuration and recommendations

阅读生成的报告并向用户展示关键发现。

### Step 4: Present Insights / 展示洞察

Present the top insights to the user in a conversational manner. Focus on:
- The most important findings (critical/warning severity)
- Positive trends worth celebrating
- Actionable recommendations

Use the trend icons:
- 🔺 Rising / 上升
- 🔻 Falling / 下降
- ➡️ Stable / 稳定
- ⚠️ Anomaly / 异常

以对话方式向用户展示最重要的洞察，聚焦关键发现、积极趋势和可操作建议。

### Step 5: Answer Follow-up Questions / 回答后续问题

The user may ask deeper questions about specific metrics. You can:
- Re-run the CLI with `--summary` for quick reference
- Use `--json` output for programmatic analysis
- Directly analyze the parsed data for custom queries

用户可能会追问特定指标，可以用 `--json` 输出做程序化分析或直接分析解析后的数据。

## Data Format Reference / 数据格式参考

The Garmin Connect export ZIP contains JSON files organized as:

```
{zip_root}/
├── customer_data/customer.json              # User profile
├── DI_CONNECT/DI-Connect-Aggregator/
│   ├── UDSFile_*.json                       # Daily wellness summary
│   └── HydrationLogFile_*.json              # Hydration tracking
├── DI_CONNECT/DI-Connect-Wellness/
│   ├── *_sleepData.json                     # Sleep records
│   ├── *_AbnormalHrEvents.json              # Abnormal HR events
│   ├── *_fitnessAgeData.json                # Fitness age tracking
│   ├── *_heartRateZones.json                # HR zone config
│   └── *_powerZones.json                    # Power zones
├── DI_CONNECT/DI-Connect-Metrics/
│   ├── RunRacePredictions_*.json            # Race predictions
│   ├── TrainingHistory_*.json               # Training status
│   ├── TrainingReadinessDTO_*.json          # Training readiness
│   ├── ActivityVo2Max_*.json                # VO2 Max per activity
│   ├── EnduranceScore_*.json                # Endurance score
│   ├── HillScore_*.json                     # Hill score
│   └── MetricsAcuteTrainingLoad_*.json      # Acute training load
├── DI_CONNECT/DI-Connect-Fitness/           # Workout FIT files (not parsed in v0.1)
├── DI_CONNECT/DI-Connect-User/
│   ├── CalendarItems_*.json                 # Calendar events
│   └── UserGoal_*.json                      # User goals
└── IT_GLOBAL_EVENT/events.json              # System events (not parsed)
```

## Supported Data / 支持的数据

| Priority | Category | Description |
|----------|----------|-------------|
| P0 | UDSFile | Daily steps, calories, HR, stress, Body Battery, SpO2, respiration |
| P0 | sleepData | Sleep stages, scores, nap, sleep SpO2, respiration |
| P0 | fitnessAgeData | Fitness age, chronological age, BMI, VO2 Max |
| P0 | RunRacePredictions | 5K/10K/half marathon/marathon predictions |
| P0 | TrainingHistory | Training status (PEAKING/PRODUCTIVE/DETRAINING etc.) |
| P0 | heartRateZones | HR zone configuration by sport |
| P1 | HydrationLogFile | Daily water intake |
| P1 | TrainingReadinessDTO | Training readiness score |
| P1 | ActivityVo2Max | Per-activity VO2 Max |
| P1 | EnduranceScore | Endurance score trend |
| P1 | HillScore | Hill score trend |
| P1 | MetricsAcuteTrainingLoad | Acute training load |
| P2 | DI-Connect-Fitness | FIT workout files (planned for v2) |

## Cross-Platform Notes / 跨平台说明

This skill is designed to work on any AI platform that can execute Python scripts:

- **WorkBuddy**: Full support with Bash tool + optional SVG Widget visualization
- **Claude Code**: Run via Bash, display Markdown report directly
- **ChatGPT**: Run via Code Interpreter, generate matplotlib charts optionally
- **Cursor/Copilot**: Run via terminal, display in chat

The scripts use **only Python standard library** — no pip install needed.

本技能设计为跨平台兼容，仅依赖 Python 标准库，无需安装额外包。

## WorkBuddy Enhancement / WorkBuddy 增强

On WorkBuddy, after generating the Markdown report, you can optionally create SVG Widget visualizations for key trends:

- Daily steps trend chart
- Sleep score trend chart
- Resting heart rate trend chart
- Training status timeline

Use the `show_widget` tool with Chart.js or SVG to render inline visualizations.

## Limitations / 限制

- FIT file parsing (workouts) is not supported in v0.1 — planned for v2
- Golf and auto-sport data are not analyzed
- Insight rules are general guidelines, not medical advice
- Very large ZIP files (>200MB) may take longer to extract

## Changelog / 变更日志

- **v0.1.0** (2026-06-11): Initial release — P0 data parsing, 6 analysis modules, Markdown/JSON report
