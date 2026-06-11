# Garmin Connect Export Data Schema / Garmin 数据格式参考

## Overview / 概述

Garmin Connect allows users to export their personal data as a ZIP archive. The archive contains JSON files organized by data category. This document describes the schema of each data type.

Garmin Connect 允许用户导出个人数据为 ZIP 压缩包，内含按类别组织的 JSON 文件。

---

## File Naming Patterns / 文件命名模式

Garmin uses two naming patterns:

1. **Prefix pattern**: `{TypeName}_{StartDate}_{EndDate}_{UserID}.json`
   - Example: `UDSFile_20240101_20240401_9229716.json`
   - Used by: UDSFile, HydrationLogFile, RunRacePredictions, TrainingHistory, etc.

2. **Suffix pattern**: `{StartDate}_{EndDate}_{UserID}_{TypeName}.json`
   - Example: `2024-01-01_2024-04-01_9229716_sleepData.json`
   - Used by: sleepData, AbnormalHrEvents

3. **Single file pattern**: `{UserID}_{TypeName}.json`
   - Example: `9229716_fitnessAgeData.json`
   - Used by: fitnessAgeData, heartRateZones, powerZones

---

## UDSFile — Daily Wellness Summary / 每日健康汇总

**Location**: `DI_CONNECT/DI-Connect-Aggregator/UDSFile_*.json`
**Format**: JSON Array (each element = one day)
**Frequency**: ~3 months per file

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `calendarDate` | string | Date in YYYY-MM-DD | 日历日期 |
| `totalSteps` | int | Total daily steps | 日总步数 |
| `totalKilocalories` | float | Total calories burned | 日总消耗(千卡) |
| `activeKilocalories` | float | Active calories | 活动消耗(千卡) |
| `restingHeartRate` | int | Resting heart rate | 静息心率(bpm) |
| `minHeartRate` | int | Minimum heart rate | 最低心率 |
| `maxHeartRate` | int | Maximum heart rate | 最高心率 |
| `averageSpo2Value` | float | Average SpO2 | 平均血氧(%) |
| `respiration` | float | Average respiration rate | 平均呼吸频率(次/分) |
| `floorsAscendedInMeters` | float | Floors climbed (meters) | 爬楼(米) |
| `intensityMinutes` | int | Weekly intensity minutes | 周强度分钟数 |
| `allDayStress.averageStressLevel` | float | Avg stress (0-100) | 日均压力 |
| `allDayStress.lowDuration` | int | Low stress duration (s) | 低压力时长(秒) |
| `allDayStress.mediumDuration` | int | Medium stress duration (s) | 中压力时长(秒) |
| `allDayStress.highDuration` | int | High stress duration (s) | 高压力时长(秒) |
| `bodyBatteryChargedValueAndDrainedValue.chargedValue` | int | BB charged | BB充电值 |
| `bodyBatteryChargedValueAndDrainedValue.drainedValue` | int | BB drained | BB消耗值 |
| `bodyBatteryChargedValueAndDrainedValue.HIGHEST` | int | BB highest | BB最高值 |
| `bodyBatteryChargedValueAndDrainedValue.LOWEST` | int | BB lowest | BB最低值 |

### Notes
- Empty days may contain only `{"retro": false}` — skip these
- Some fields may be null for early data periods (pre-2019)
- Body Battery and Stress data availability depends on device model

---

## sleepData — Sleep Records / 睡眠记录

**Location**: `DI_CONNECT/DI-Connect-Wellness/*_sleepData.json`
**Format**: JSON Array (each element = one sleep session)

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `calendarDate` | string | Date | 日历日期 |
| `sleepStartTimestampGMT` | string | Sleep start time | 入睡时间(GMT) |
| `sleepEndTimestampGMT` | string | Sleep end time | 起床时间(GMT) |
| `deepSleepSeconds` | int | Deep sleep duration | 深睡时长(秒) |
| `lightSleepSeconds` | int | Light sleep duration | 浅睡时长(秒) |
| `remSleepSeconds` | int | REM sleep duration | REM时长(秒) |
| `awakeSleepSeconds` | int | Awake duration | 清醒时长(秒) |
| `unmeasurableSeconds` | int | Unmeasurable time | 不可测量时长(秒) |
| `sleepScores.overallScore` | int | Overall sleep score (0-100) | 睡眠总分 |
| `sleepScores.qualityScore` | int | Quality subscore | 质量子分 |
| `sleepScores.durationScore` | int | Duration subscore | 时长子分 |
| `sleepScores.recoveryScore` | int | Recovery subscore | 恢复子分 |
| `sleepScores.deepScore` | int | Deep sleep subscore | 深睡子分 |
| `sleepScores.remScore` | int | REM subscore | REM子分 |
| `sleepScores.feedback` | string | Feedback code | 反馈代码 |
| `avgSleepStress` | float | Average stress during sleep | 睡眠压力 |
| `averageRespiration` | float | Avg respiration | 平均呼吸频率 |
| `spo2SleepSummary.averageSPO2` | float | Avg SpO2 during sleep | 睡眠血氧 |
| `spo2SleepSummary.lowestSPO2` | int | Lowest SpO2 during sleep | 最低血氧 |
| `spo2SleepSummary.averageHR` | float | Avg HR during sleep | 睡眠心率 |
| `napList` | array | Nap entries | 午睡列表 |
| `restlessMomentCount` | int | Restless moments | 翻身次数 |

### Sleep Score Feedback Codes

| Code | Meaning |
|------|---------|
| `POSITIVE_OPTIMAL_STRUCTURE` | 睡眠结构优秀 |
| `POSITIVE_GOOD_DURATION` | 睡眠时长良好 |
| `NEUTRAL` | 一般 |
| `NEGATIVE_SHORT_SLEEP` | 睡眠不足 |
| `NEGATIVE_POOR_STRUCTURE` | 睡眠结构不佳 |

---

## fitnessAgeData — Fitness Age / 体能年龄

**Location**: `DI_CONNECT/DI-Connect-Wellness/{UserID}_fitnessAgeData.json`
**Format**: JSON Array (each element = one measurement)

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `timestamp` | long | Measurement timestamp (ms) | 测量时间戳 |
| `chronologicalAge` | float | Actual age | 实际年龄 |
| `currentBioAge` | float | Bio age (fitness age) | 体能年龄 |
| `bmi` | float | Body Mass Index | BMI |
| `rhr` | float | Resting heart rate | 静息心率 |
| `biometricVo2Max` | float | Estimated VO2 Max | 估计最大摄氧量 |

---

## heartRateZones — Heart Rate Zones / 心率区间

**Location**: `DI_CONNECT/DI-Connect-Wellness/{UserID}_heartRateZones.json`
**Format**: JSON Array (each element = one zone config)

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `sport` | string | Sport type (DEFAULT/RUNNING) | 运动类型 |
| `trainingMethod` | string | Method (HR_MAX/LTHR) | 训练方法 |
| `zone1Floor` | int | Zone 1 lower bound | Z1下限(bpm) |
| `zone2Floor` | int | Zone 2 lower bound | Z2下限(bpm) |
| `zone3Floor` | int | Zone 3 lower bound | Z3下限(bpm) |
| `zone4Floor` | int | Zone 4 lower bound | Z4下限(bpm) |
| `zone5Floor` | int | Zone 5 lower bound | Z5下限(bpm) |
| `maxHeartRateUsed` | int | Max HR used | 使用的最大心率 |
| `restingHeartRateUsed` | int | Resting HR used | 使用的静息心率 |
| `lactateThresholdHeartRateUsed` | int | LTHR used | 乳酸阈值心率 |

---

## RunRacePredictions — Race Predictions / 跑步预测

**Location**: `DI_CONNECT/DI-Connect-Metrics/RunRacePredictions_*.json`
**Format**: JSON Array

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `timestamp` | long | Prediction timestamp (ms) | 预测时间戳 |
| `raceTime5K` | int | 5K predicted time (s) | 5K预测时间(秒) |
| `raceTime10K` | int | 10K predicted time (s) | 10K预测时间(秒) |
| `raceTimeHalf` | int | Half marathon time (s) | 半马预测时间(秒) |
| `raceTimeMarathon` | int | Marathon time (s) | 全马预测时间(秒) |

---

## TrainingHistory — Training Status / 训练状态

**Location**: `DI_CONNECT/DI-Connect-Metrics/TrainingHistory_*.json`
**Format**: JSON Array

### Key Fields

| Field | Type | Description | 中文说明 |
|-------|------|-------------|---------|
| `timestamp` | long | Status timestamp (ms) | 状态时间戳 |
| `trainingStatus` | string | Current status code | 训练状态代码 |
| `fitnessLevelTrend` | string | Trend direction | 体能水平趋势 |

### Training Status Codes

| Status | Meaning | 中文 |
|--------|---------|------|
| `PEAKING` | At peak fitness | 巅峰状态 |
| `PRODUCTIVE` | Improving | 高效训练 |
| `MAINTAINING` | Maintaining | 维持 |
| `RECOVERY` | Recovering | 恢复中 |
| `DETRAINING` | Losing fitness | 体能下降 |
| `OVERREACHING` | Overtraining risk | 过度训练 |
| `UNPRODUCTIVE` | Training but not improving | 低效训练 |
| `NO_STATUS` | No data | 无状态 |

---

## Common Patterns / 通用模式

### Timestamps
- Garmin uses **millisecond Unix timestamps** for most fields
- Some fields use **ISO 8601 strings** (e.g., `sleepStartTimestampGMT`)
- Always check type before parsing

### Empty Records
- Some records contain only `{"retro": false}` — these are placeholder entries with no actual data
- Skip these during parsing

### Data Gaps
- Data availability depends on device model and user behavior
- Early periods (pre-2019) may have fewer metrics
- Not all users have all data categories (e.g., no golf data for non-golfers)
