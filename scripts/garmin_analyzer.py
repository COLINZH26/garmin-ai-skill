#!/usr/bin/env python3
"""
Garmin Data Analyzer — 分析 Garmin 数据，生成健康/运动洞察

配合 garmin_parser.py 使用，从 GarminDataset 中提取趋势、异常和可操作建议。

用法:
    from garmin_parser import GarminDataParser
    from garmin_analyzer import GarminAnalyzer

    parser = GarminDataParser("garmin_export.zip")
    dataset = parser.parse_all()
    analyzer = GarminAnalyzer(dataset)
    report = analyzer.generate_full_report()
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import statistics


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class Insight:
    """单条洞察"""
    category: str           # e.g. "daily_wellness", "sleep", "training"
    indicator: str          # e.g. "resting_heart_rate", "deep_sleep_ratio"
    trend: str              # "up", "down", "stable", "anomaly"
    severity: str           # "info", "warning", "critical", "positive"
    value_current: str      # 当前值（人类可读）
    value_previous: str     # 对比值（人类可读）
    summary: str            # 一句话总结
    detail: str             # 详细说明
    recommendation: str     # 建议


@dataclass
class ModuleReport:
    """单个分析模块的报告"""
    module_name: str
    title: str
    data_overview: dict         # 数据覆盖概况
    key_metrics: list           # 关键指标摘要 [{name, value, unit, trend}]
    insights: list              # Insight 列表
    period_comparison: dict     # 期间对比（最近30天 vs 之前30天）


@dataclass
class FullReport:
    """完整分析报告"""
    user_name: str
    data_range: dict
    modules: list               # ModuleReport 列表
    top_insights: list          # Top 5 最重要洞察
    overall_summary: str        # 总体评价


# ─── 辅助函数 ──────────────────────────────────────────────

def _avg(values: list, default=None):
    """安全计算平均值"""
    clean = [v for v in values if v is not None]
    if not clean:
        return default
    return statistics.mean(clean)


def _median(values: list, default=None):
    """安全计算中位数"""
    clean = [v for v in values if v is not None]
    if not clean:
        return default
    return statistics.median(clean)


def _trend_direction(current, previous, threshold_pct=0.05):
    """判断趋势方向"""
    if current is None or previous is None or previous == 0:
        return "stable"
    change = (current - previous) / abs(previous)
    if change > threshold_pct:
        return "up"
    elif change < -threshold_pct:
        return "down"
    return "stable"


def _pct_change(current, previous):
    """计算百分比变化"""
    if current is None or previous is None or previous == 0:
        return None
    return ((current - previous) / abs(previous)) * 100


def _format_duration(seconds):
    """格式化时长"""
    if seconds is None:
        return "N/A"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h{m}m"


def _format_bpm(value):
    """格式化心率"""
    if value is None:
        return "N/A"
    return f"{value} bpm"


def _split_recent(records, days=30):
    """
    将记录列表按日期分为"最近N天"和"之前N天"两组
    返回 (recent_records, previous_records, recent_start_date)
    """
    if not records:
        return [], [], None

    # 获取最新日期
    dates = []
    for r in records:
        date_str = getattr(r, 'calendar_date', None) or getattr(r, 'timestamp', None)
        if date_str:
            dates.append(date_str[:10])  # YYYY-MM-DD

    if not dates:
        return [], [], None

    dates.sort()
    latest = dates[-1]

    try:
        latest_dt = datetime.strptime(latest, "%Y-%m-%d")
    except ValueError:
        return records, [], latest

    recent_start = (latest_dt - timedelta(days=days)).strftime("%Y-%m-%d")
    previous_start = (latest_dt - timedelta(days=2 * days)).strftime("%Y-%m-%d")

    recent = []
    previous = []
    for r in records:
        date_str = getattr(r, 'calendar_date', None) or getattr(r, 'timestamp', None)
        if date_str:
            d = date_str[:10]
            if d >= recent_start:
                recent.append(r)
            elif d >= previous_start:
                previous.append(r)

    return recent, previous, recent_start


# ─── 分析器 ────────────────────────────────────────────────

class GarminAnalyzer:
    """
    Garmin 数据分析器

    用法:
        analyzer = GarminAnalyzer(dataset)
        report = analyzer.generate_full_report()
    """

    def __init__(self, dataset):
        self.dataset = dataset

    # ─── 模块 A: 日常健康概览 ───────────────────────────

    def analyze_daily_wellness(self) -> ModuleReport:
        """分析日常健康汇总数据"""
        records = self.dataset.daily_summaries
        recent, previous, period_start = _split_recent(records)

        # 计算最近期间指标
        r_steps = _avg([r.total_steps for r in recent])
        r_calories = _avg([r.total_kilocalories for r in recent])
        r_active_cal = _avg([r.active_kilocalories for r in recent])
        r_rhr = _avg([r.resting_heart_rate for r in recent])
        r_stress = _avg([r.average_stress_level for r in recent])
        r_bb_charged = _avg([r.body_battery_charged for r in recent])
        r_bb_drained = _avg([r.body_battery_drained for r in recent])
        r_spo2 = _avg([r.average_spo2 for r in recent])
        r_respiration = _avg([r.respiration for r in recent])

        # 对比期间指标
        p_steps = _avg([r.total_steps for r in previous])
        p_rhr = _avg([r.resting_heart_rate for r in previous])
        p_stress = _avg([r.average_stress_level for r in previous])
        p_bb_charged = _avg([r.body_battery_charged for r in previous])
        p_spo2 = _avg([r.average_spo2 for r in previous])

        # 关键指标摘要
        key_metrics = [
            {"name": "日均步数", "value": f"{r_steps:.0f}" if r_steps else "N/A", "unit": "步",
             "trend": _trend_direction(r_steps, p_steps)},
            {"name": "日均消耗", "value": f"{r_calories:.0f}" if r_calories else "N/A", "unit": "kcal",
             "trend": _trend_direction(r_calories, _avg([r.total_kilocalories for r in previous]))},
            {"name": "活动消耗", "value": f"{r_active_cal:.0f}" if r_active_cal else "N/A", "unit": "kcal",
             "trend": _trend_direction(r_active_cal, _avg([r.active_kilocalories for r in previous]))},
            {"name": "静息心率", "value": f"{r_rhr:.0f}" if r_rhr else "N/A", "unit": "bpm",
             "trend": _trend_direction(r_rhr, p_rhr)},
            {"name": "平均压力", "value": f"{r_stress:.1f}" if r_stress else "N/A", "unit": "分",
             "trend": _trend_direction(r_stress, p_stress)},
            {"name": "BB充电", "value": f"{r_bb_charged:.0f}" if r_bb_charged else "N/A", "unit": "",
             "trend": _trend_direction(r_bb_charged, p_bb_charged)},
            {"name": "SpO2", "value": f"{r_spo2:.1f}" if r_spo2 else "N/A", "unit": "%",
             "trend": _trend_direction(r_spo2, p_spo2)},
            {"name": "呼吸频率", "value": f"{r_respiration:.1f}" if r_respiration else "N/A", "unit": "次/分",
             "trend": "stable"},
        ]

        # 生成洞察
        insights = []

        # 静息心率洞察
        if r_rhr and p_rhr:
            rhr_change = _pct_change(r_rhr, p_rhr)
            if rhr_change and rhr_change > 5:
                insights.append(Insight(
                    category="daily_wellness", indicator="resting_heart_rate",
                    trend="up", severity="warning",
                    value_current=f"{r_rhr:.0f} bpm", value_previous=f"{p_rhr:.0f} bpm",
                    summary="静息心率上升",
                    detail=f"近期静息心率 {r_rhr:.0f} bpm，较之前 {p_rhr:.0f} bpm 上升 {rhr_change:.1f}%",
                    recommendation="可能存在过度训练、睡眠不足或压力过大，建议适当休息"
                ))
            elif rhr_change and rhr_change < -3:
                insights.append(Insight(
                    category="daily_wellness", indicator="resting_heart_rate",
                    trend="down", severity="positive",
                    value_current=f"{r_rhr:.0f} bpm", value_previous=f"{p_rhr:.0f} bpm",
                    summary="静息心率下降，体能改善",
                    detail=f"近期静息心率 {r_rhr:.0f} bpm，较之前 {p_rhr:.0f} bpm 下降 {abs(rhr_change):.1f}%",
                    recommendation="静息心率下降通常是有氧能力提升的标志，保持当前训练节奏"
                ))

        # 步数洞察
        if r_steps and p_steps:
            steps_change = _pct_change(r_steps, p_steps)
            if steps_change and steps_change > 20:
                insights.append(Insight(
                    category="daily_wellness", indicator="steps",
                    trend="up", severity="positive",
                    value_current=f"{r_steps:.0f} 步/天", value_previous=f"{p_steps:.0f} 步/天",
                    summary="日均步数显著增加",
                    detail=f"近期日均 {r_steps:.0f} 步，较之前增长 {steps_change:.1f}%",
                    recommendation="活动量增加是好事，注意逐步增加避免受伤"
                ))
            elif steps_change and steps_change < -20:
                insights.append(Insight(
                    category="daily_wellness", indicator="steps",
                    trend="down", severity="warning",
                    value_current=f"{r_steps:.0f} 步/天", value_previous=f"{p_steps:.0f} 步/天",
                    summary="日均步数明显下降",
                    detail=f"近期日均 {r_steps:.0f} 步，较之前下降 {abs(steps_change):.1f}%",
                    recommendation="活动量减少，建议增加日常步行或低强度运动"
                ))

        # Body Battery 洞察
        if r_bb_charged and r_bb_drained:
            net_bb = r_bb_charged - r_bb_drained
            if net_bb < -5:
                insights.append(Insight(
                    category="daily_wellness", indicator="body_battery",
                    trend="down", severity="warning",
                    value_current=f"充电{r_bb_charged:.0f} / 消耗{r_bb_drained:.0f}",
                    value_previous="",
                    summary="Body Battery 入不敷出",
                    detail=f"日均充电 {r_bb_charged:.0f}，消耗 {r_bb_drained:.0f}，净亏损 {abs(net_bb):.0f}",
                    recommendation="日间消耗大于夜间恢复，建议关注睡眠质量和日间压力管理"
                ))
            elif net_bb > 5:
                insights.append(Insight(
                    category="daily_wellness", indicator="body_battery",
                    trend="up", severity="positive",
                    value_current=f"充电{r_bb_charged:.0f} / 消耗{r_bb_drained:.0f}",
                    value_previous="",
                    summary="Body Battery 恢复良好",
                    detail=f"日均充电 {r_bb_charged:.0f}，消耗 {r_bb_drained:.0f}，净盈余 {net_bb:.0f}",
                    recommendation="恢复状态良好，可以适当增加训练强度"
                ))

        # 压力洞察
        if r_stress and p_stress:
            if r_stress > 50:
                insights.append(Insight(
                    category="daily_wellness", indicator="stress",
                    trend="up" if r_stress > p_stress else "stable", severity="warning",
                    value_current=f"{r_stress:.1f}", value_previous=f"{p_stress:.1f}",
                    summary="平均压力偏高",
                    detail=f"近期日均压力 {r_stress:.1f}（0-100分）",
                    recommendation="压力偏高，建议增加放松活动如冥想、深呼吸或散步"
                ))

        # SpO2 洞察
        if r_spo2 and r_spo2 < 95:
            insights.append(Insight(
                category="daily_wellness", indicator="spo2",
                trend="down" if p_spo2 and r_spo2 < p_spo2 else "stable", severity="warning",
                value_current=f"{r_spo2:.1f}%", value_previous=f"{p_spo2:.1f}%" if p_spo2 else "N/A",
                summary="血氧饱和度偏低",
                detail=f"近期日均 SpO2 {r_spo2:.1f}%，低于正常范围（95-100%）",
                recommendation="血氧偏低可能与睡眠呼吸问题有关，建议咨询医生"
            ))

        return ModuleReport(
            module_name="daily_wellness",
            title="日常健康概览 / Daily Wellness Overview",
            data_overview={"总记录天数": len(records), "分析期间": f"最近30天({len(recent)}天) vs 之前30天({len(previous)}天)"},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={
                "recent_avg_steps": r_steps,
                "previous_avg_steps": p_steps,
                "recent_avg_rhr": r_rhr,
                "previous_avg_rhr": p_rhr,
            }
        )

    # ─── 模块 B: 睡眠质量分析 ───────────────────────────

    def analyze_sleep(self) -> ModuleReport:
        """分析睡眠数据"""
        records = [r for r in self.dataset.sleep_records if r.total_sleep_seconds]
        recent, previous, period_start = _split_recent(records)

        # 最近期间
        r_total_sleep = _avg([r.total_sleep_seconds for r in recent])
        r_deep = _avg([r.deep_sleep_seconds for r in recent])
        r_light = _avg([r.light_sleep_seconds for r in recent])
        r_rem = _avg([r.rem_sleep_seconds for r in recent])
        r_awake = _avg([r.awake_sleep_seconds for r in recent])
        r_score = _avg([r.sleep_score_overall for r in recent])
        r_deep_pct = (r_deep / r_total_sleep * 100) if r_total_sleep and r_deep else None
        r_rem_pct = (r_rem / r_total_sleep * 100) if r_total_sleep and r_rem else None
        r_stress = _avg([r.avg_sleep_stress for r in recent])

        # 对比期间
        p_total_sleep = _avg([r.total_sleep_seconds for r in previous])
        p_score = _avg([r.sleep_score_overall for r in previous])
        p_deep_pct = None
        p_total_prev = _avg([r.total_sleep_seconds for r in previous])
        p_deep_prev = _avg([r.deep_sleep_seconds for r in previous])
        if p_total_prev and p_deep_prev:
            p_deep_pct = (p_deep_prev / p_total_prev * 100)

        key_metrics = [
            {"name": "平均睡眠时长", "value": _format_duration(r_total_sleep), "unit": "",
             "trend": _trend_direction(r_total_sleep, p_total_sleep)},
            {"name": "深睡占比", "value": f"{r_deep_pct:.1f}%" if r_deep_pct else "N/A", "unit": "",
             "trend": _trend_direction(r_deep_pct, p_deep_pct) if r_deep_pct and p_deep_pct else "stable"},
            {"name": "REM占比", "value": f"{r_rem_pct:.1f}%" if r_rem_pct else "N/A", "unit": "",
             "trend": "stable"},
            {"name": "睡眠评分", "value": f"{r_score:.0f}" if r_score else "N/A", "unit": "分",
             "trend": _trend_direction(r_score, p_score)},
            {"name": "睡眠压力", "value": f"{r_stress:.1f}" if r_stress else "N/A", "unit": "分",
             "trend": "stable"},
        ]

        insights = []

        # 深睡占比洞察
        if r_deep_pct is not None:
            if r_deep_pct < 15:
                insights.append(Insight(
                    category="sleep", indicator="deep_sleep_ratio",
                    trend="down" if p_deep_pct and r_deep_pct < p_deep_pct else "stable",
                    severity="warning",
                    value_current=f"{r_deep_pct:.1f}%", value_previous=f"{p_deep_pct:.1f}%" if p_deep_pct else "N/A",
                    summary="深睡比例偏低",
                    detail=f"深睡占总睡眠 {r_deep_pct:.1f}%，低于建议的15-20%",
                    recommendation="建议保持规律作息、避免睡前咖啡因和蓝光、保持卧室凉爽"
                ))
            elif r_deep_pct >= 20:
                insights.append(Insight(
                    category="sleep", indicator="deep_sleep_ratio",
                    trend="up" if p_deep_pct and r_deep_pct > p_deep_pct else "stable",
                    severity="positive",
                    value_current=f"{r_deep_pct:.1f}%", value_previous=f"{p_deep_pct:.1f}%" if p_deep_pct else "N/A",
                    summary="深睡比例良好",
                    detail=f"深睡占总睡眠 {r_deep_pct:.1f}%，处于健康范围",
                    recommendation="深睡充足有助于身体恢复，继续保持良好睡眠习惯"
                ))

        # 睡眠评分洞察
        if r_score and p_score:
            score_change = _pct_change(r_score, p_score)
            if r_score < 60:
                insights.append(Insight(
                    category="sleep", indicator="sleep_score",
                    trend="down", severity="warning",
                    value_current=f"{r_score:.0f}", value_previous=f"{p_score:.0f}",
                    summary="睡眠评分偏低",
                    detail=f"近期平均睡眠评分 {r_score:.0f}/100",
                    recommendation="睡眠质量不佳，建议关注睡眠环境和作息规律"
                ))

        # 睡眠时长洞察
        if r_total_sleep:
            r_hours = r_total_sleep / 3600
            if r_hours < 6:
                insights.append(Insight(
                    category="sleep", indicator="sleep_duration",
                    trend="down" if p_total_sleep and r_total_sleep < p_total_sleep else "stable",
                    severity="warning",
                    value_current=_format_duration(r_total_sleep), value_previous=_format_duration(p_total_sleep),
                    summary="睡眠时长不足",
                    detail=f"近期平均每晚 {r_hours:.1f} 小时，低于推荐的7-9小时",
                    recommendation="睡眠不足影响恢复和认知功能，建议提前入睡时间"
                ))

        # 睡眠压力关联
        if r_stress and r_stress > 25:
            insights.append(Insight(
                category="sleep", indicator="sleep_stress",
                trend="up", severity="info",
                value_current=f"{r_stress:.1f}", value_previous="",
                summary="睡眠期间压力偏高",
                detail=f"睡眠中平均压力 {r_stress:.1f}，可能影响深度恢复",
                recommendation="睡前进行放松练习（如冥想、4-7-8呼吸法）有助于降低睡眠压力"
            ))

        return ModuleReport(
            module_name="sleep",
            title="睡眠质量分析 / Sleep Quality Analysis",
            data_overview={"总睡眠记录": len(records), "分析期间": f"最近30天({len(recent)}天) vs 之前30天({len(previous)}天)"},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={
                "recent_avg_sleep_min": r_total_sleep / 60 if r_total_sleep else None,
                "previous_avg_sleep_min": p_total_sleep / 60 if p_total_sleep else None,
            }
        )

    # ─── 模块 C: 训练状态与负荷 ───────────────────────────

    def analyze_training(self) -> ModuleReport:
        """分析训练状态"""
        records = self.dataset.training_status_records
        recent, previous, period_start = _split_recent(records)

        # 统计最近期间各训练状态分布
        status_counts = {}
        for r in recent:
            status = r.training_status or "NO_STATUS"
            status_counts[status] = status_counts.get(status, 0) + 1

        # 对比期间
        prev_status_counts = {}
        for r in previous:
            status = r.training_status or "NO_STATUS"
            prev_status_counts[status] = prev_status_counts.get(status, 0) + 1

        # 主导状态
        dominant_status = max(status_counts, key=status_counts.get) if status_counts else "NO_STATUS"

        status_labels = {
            "PEAKING": "巅峰状态",
            "PRODUCTIVE": "高效训练",
            "MAINTAINING": "维持状态",
            "RECOVERY": "恢复中",
            "DETRAINING": "体能下降",
            "NO_STATUS": "无状态",
            "UNPRODUCTIVE": "低效训练",
            "OVERREACHING": "过度训练",
        }

        key_metrics = [
            {"name": "当前主导状态", "value": status_labels.get(dominant_status, dominant_status),
             "unit": "", "trend": "stable"},
        ]

        # 状态分布
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1])[:5]:
            key_metrics.append({
                "name": f"  {status_labels.get(status, status)}",
                "value": f"{count}天",
                "unit": f"({count/len(recent)*100:.0f}%)" if recent else "",
                "trend": "stable"
            })

        insights = []

        # 连续 DETRAINING 洞察
        if status_counts.get("DETRAINING", 0) > len(recent) * 0.5:
            insights.append(Insight(
                category="training", indicator="training_status",
                trend="down", severity="warning",
                value_current=status_labels.get(dominant_status, dominant_status),
                value_previous="",
                summary="训练不足导致体能下降",
                detail=f"近期 {status_counts['DETRAINING']} 天处于 DETRAINING 状态，占比超过50%",
                recommendation="训练量不足导致体能下降，建议逐步恢复规律训练"
            ))

        # OVERREACHING 洞察
        if status_counts.get("OVERREACHING", 0) > 3:
            insights.append(Insight(
                category="training", indicator="training_status",
                trend="up", severity="critical",
                value_current="过度训练", value_previous="",
                summary="可能过度训练",
                detail=f"近期 {status_counts['OVERREACHING']} 天处于 OVERREACHING 状态",
                recommendation="建议减少训练量和强度，增加恢复日，避免受伤"
            ))

        # PEAKING 洞察
        if dominant_status == "PEAKING":
            insights.append(Insight(
                category="training", indicator="training_status",
                trend="up", severity="positive",
                value_current="巅峰状态", value_previous="",
                summary="训练状态达到巅峰",
                detail="当前训练负荷与体能水平匹配，处于最佳状态",
                recommendation="巅峰状态难以长期维持，适合在近期参加比赛或测试"
            ))

        return ModuleReport(
            module_name="training",
            title="训练状态与负荷 / Training Status & Load",
            data_overview={"总训练记录": len(records), "分析期间": f"最近30天({len(recent)}天)"},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={"recent_status_dist": status_counts, "previous_status_dist": prev_status_counts}
        )

    # ─── 模块 D: 体能评估 ───────────────────────────────

    def analyze_fitness(self) -> ModuleReport:
        """分析体能年龄和VO2 Max"""
        records = self.dataset.fitness_age_records

        if not records:
            return ModuleReport(
                module_name="fitness",
                title="体能评估 / Fitness Assessment",
                data_overview={"总记录": 0}, key_metrics=[], insights=[],
                period_comparison={}
            )

        # 最新记录
        latest = records[-1]

        key_metrics = [
            {"name": "实际年龄", "value": f"{latest.chronological_age:.1f}" if latest.chronological_age else "N/A",
             "unit": "岁", "trend": "stable"},
            {"name": "体能年龄", "value": f"{latest.current_bio_age:.1f}" if latest.current_bio_age else "N/A",
             "unit": "岁", "trend": "stable"},
            {"name": "BMI", "value": f"{latest.bmi:.1f}" if latest.bmi else "N/A",
             "unit": "", "trend": "stable"},
            {"name": "VO2 Max", "value": f"{latest.vo2_max:.1f}" if latest.vo2_max else "N/A",
             "unit": "ml/kg/min", "trend": "stable"},
        ]

        insights = []

        # 体能年龄 vs 实际年龄
        if latest.current_bio_age and latest.chronological_age:
            age_diff = latest.current_bio_age - latest.chronological_age
            if age_diff > 5:
                insights.append(Insight(
                    category="fitness", indicator="fitness_age",
                    trend="down", severity="warning",
                    value_current=f"{latest.current_bio_age:.1f}岁",
                    value_previous=f"实际{latest.chronological_age:.1f}岁",
                    summary="体能年龄显著高于实际年龄",
                    detail=f"体能年龄 {latest.current_bio_age:.1f} 岁，比实际年龄大 {age_diff:.1f} 岁",
                    recommendation="建议增加有氧训练（跑步、游泳、骑行），逐步提升心肺功能"
                ))
            elif age_diff < -5:
                insights.append(Insight(
                    category="fitness", indicator="fitness_age",
                    trend="up", severity="positive",
                    value_current=f"{latest.current_bio_age:.1f}岁",
                    value_previous=f"实际{latest.chronological_age:.1f}岁",
                    summary="体能年龄远优于实际年龄",
                    detail=f"体能年龄 {latest.current_bio_age:.1f} 岁，比实际年龄年轻 {abs(age_diff):.1f} 岁",
                    recommendation="心肺功能优秀，继续保持当前运动习惯"
                ))
            elif age_diff < 0:
                insights.append(Insight(
                    category="fitness", indicator="fitness_age",
                    trend="up", severity="positive",
                    value_current=f"{latest.current_bio_age:.1f}岁",
                    value_previous=f"实际{latest.chronological_age:.1f}岁",
                    summary="体能年龄优于实际年龄",
                    detail=f"体能年龄比实际年轻 {abs(age_diff):.1f} 岁",
                    recommendation="保持规律运动，持续优化"
                ))

        # 趋势分析（首末对比）
        if len(records) >= 2:
            first = records[0]
            last = records[-1]
            if first.current_bio_age and last.current_bio_age:
                bio_age_trend = _trend_direction(last.current_bio_age, first.current_bio_age)
                if bio_age_trend == "down":
                    insights.append(Insight(
                        category="fitness", indicator="fitness_age_trend",
                        trend="down", severity="positive",
                        value_current=f"{last.current_bio_age:.1f}岁",
                        value_previous=f"{first.current_bio_age:.1f}岁",
                        summary="体能年龄呈下降趋势（改善中）",
                        detail=f"从 {first.current_bio_age:.1f} 岁降至 {last.current_bio_age:.1f} 岁",
                        recommendation="体能年龄持续改善，保持训练节奏"
                    ))
                elif bio_age_trend == "up":
                    insights.append(Insight(
                        category="fitness", indicator="fitness_age_trend",
                        trend="up", severity="warning",
                        value_current=f"{last.current_bio_age:.1f}岁",
                        value_previous=f"{first.current_bio_age:.1f}岁",
                        summary="体能年龄呈上升趋势（退化中）",
                        detail=f"从 {first.current_bio_age:.1f} 岁升至 {last.current_bio_age:.1f} 岁",
                        recommendation="体能水平下降，需要恢复规律训练"
                    ))

        return ModuleReport(
            module_name="fitness",
            title="体能评估 / Fitness Assessment",
            data_overview={"总记录": len(records), "时间跨度": f"首次: {records[0].timestamp or 'N/A'} ~ 最新: {records[-1].timestamp or 'N/A'}"},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={}
        )

    # ─── 模块 E: 跑步能力预测 ───────────────────────────

    def analyze_race_predictions(self) -> ModuleReport:
        """分析跑步比赛预测"""
        records = self.dataset.race_predictions

        if not records:
            return ModuleReport(
                module_name="race_predictions",
                title="跑步能力预测 / Running Race Predictions",
                data_overview={"总记录": 0}, key_metrics=[], insights=[],
                period_comparison={}
            )

        latest = records[-1]
        first = records[0]

        def _format_race_time(seconds):
            if seconds is None:
                return "N/A"
            h = seconds // 3600
            m = (seconds % 3600) // 60
            s = seconds % 60
            if h > 0:
                return f"{h}:{m:02d}:{s:02d}"
            return f"{m}:{s:02d}"

        key_metrics = [
            {"name": "5K预测", "value": _format_race_time(latest.race_time_5k), "unit": "",
             "trend": _trend_direction(latest.race_time_5k, first.race_time_5k, threshold_pct=0.02) if first.race_time_5k else "stable"},
            {"name": "10K预测", "value": _format_race_time(latest.race_time_10k), "unit": "",
             "trend": _trend_direction(latest.race_time_10k, first.race_time_10k, threshold_pct=0.02) if first.race_time_10k else "stable"},
            {"name": "半马预测", "value": _format_race_time(latest.race_time_half), "unit": "",
             "trend": _trend_direction(latest.race_time_half, first.race_time_half, threshold_pct=0.02) if first.race_time_half else "stable"},
            {"name": "全马预测", "value": _format_race_time(latest.race_time_marathon), "unit": "",
             "trend": _trend_direction(latest.race_time_marathon, first.race_time_marathon, threshold_pct=0.02) if first.race_time_marathon else "stable"},
        ]

        insights = []

        # 跑步能力变化（时间缩短 = 能力提升）
        if latest.race_time_5k and first.race_time_5k:
            change = _pct_change(latest.race_time_5k, first.race_time_5k)
            if change and change < -5:
                insights.append(Insight(
                    category="race_predictions", indicator="5k_time",
                    trend="down", severity="positive",
                    value_current=_format_race_time(latest.race_time_5k),
                    value_previous=_format_race_time(first.race_time_5k),
                    summary="5K预测时间显著缩短",
                    detail=f"5K预测从 {_format_race_time(first.race_time_5k)} 缩短至 {_format_race_time(latest.race_time_5k)}，改善 {abs(change):.1f}%",
                    recommendation="跑步能力提升明显，保持当前训练计划"
                ))
            elif change and change > 5:
                insights.append(Insight(
                    category="race_predictions", indicator="5k_time",
                    trend="up", severity="warning",
                    value_current=_format_race_time(latest.race_time_5k),
                    value_previous=_format_race_time(first.race_time_5k),
                    summary="5K预测时间增加",
                    detail=f"5K预测从 {_format_race_time(first.race_time_5k)} 增加至 {_format_race_time(latest.race_time_5k)}，退步 {change:.1f}%",
                    recommendation="跑步能力有所下降，建议恢复规律跑步训练"
                ))

        return ModuleReport(
            module_name="race_predictions",
            title="跑步能力预测 / Running Race Predictions",
            data_overview={"总记录": len(records)},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={}
        )

    # ─── 模块 F: 心率区间 ───────────────────────────────

    def analyze_hr_zones(self) -> ModuleReport:
        """分析心率区间设置"""
        records = self.dataset.heart_rate_zones

        if not records:
            return ModuleReport(
                module_name="hr_zones",
                title="心率区间分析 / Heart Rate Zones",
                data_overview={"总记录": 0}, key_metrics=[], insights=[],
                period_comparison={}
            )

        key_metrics = []
        insights = []

        for zone in records:
            zone_type_label = {"DEFAULT": "默认", "RUNNING": "跑步"}.get(zone.zone_type, zone.zone_type)
            key_metrics.append({
                "name": f"{zone_type_label}心率区间",
                "value": f"Z1:{zone.zone1_floor}-{zone.zone2_floor} Z2:{zone.zone2_floor}-{zone.zone3_floor} Z3:{zone.zone3_floor}-{zone.zone4_floor} Z4:{zone.zone4_floor}-{zone.zone5_floor} Z5:{zone.zone5_floor}+",
                "unit": "bpm",
                "trend": "stable"
            })
            if zone.max_heart_rate:
                key_metrics.append({
                    "name": f"  最大心率", "value": f"{zone.max_heart_rate}", "unit": "bpm", "trend": "stable"
                })

            # 区间合理性检查
            if zone.zone1_floor and zone.zone2_floor and zone.zone3_floor:
                z2_width = zone.zone2_floor - zone.zone1_floor
                z3_width = zone.zone3_floor - zone.zone2_floor
                if zone.zone4_floor:
                    z4_width = zone.zone4_floor - zone.zone3_floor
                    if z4_width > 25:
                        insights.append(Insight(
                            category="hr_zones", indicator="zone4_width",
                            trend="stable", severity="info",
                            value_current=f"Z3-Z4: {zone.zone3_floor}-{zone.zone4_floor}bpm",
                            value_previous="",
                            summary="Zone 4 区间较宽",
                            detail=f"Z4 宽度 {z4_width}bpm，阈值训练区间较大",
                            recommendation="如需精确阈值训练，建议通过乳酸阈值测试调整心率区间"
                        ))

        if not insights:
            insights.append(Insight(
                category="hr_zones", indicator="zones_config",
                trend="stable", severity="info",
                value_current="已配置", value_previous="",
                summary="心率区间已设置",
                detail=f"共 {len(records)} 组心率区间配置",
                recommendation="确保心率区间基于最近的心率测试结果设置，以获得准确的训练强度指导"
            ))

        return ModuleReport(
            module_name="hr_zones",
            title="心率区间分析 / Heart Rate Zones",
            data_overview={"配置数": len(records)},
            key_metrics=key_metrics,
            insights=insights,
            period_comparison={}
        )

    # ─── 综合报告 ──────────────────────────────────────

    def generate_full_report(self) -> FullReport:
        """生成完整分析报告"""
        modules = [
            self.analyze_daily_wellness(),
            self.analyze_sleep(),
            self.analyze_training(),
            self.analyze_fitness(),
            self.analyze_race_predictions(),
            self.analyze_hr_zones(),
        ]

        # 收集所有洞察，按严重程度排序
        all_insights = []
        for m in modules:
            all_insights.extend(m.insights)

        severity_order = {"critical": 0, "warning": 1, "positive": 2, "info": 3}
        all_insights.sort(key=lambda i: severity_order.get(i.severity, 99))

        top_insights = all_insights[:5]

        # 生成总体评价
        positive_count = sum(1 for i in all_insights if i.severity == "positive")
        warning_count = sum(1 for i in all_insights if i.severity in ("warning", "critical"))
        if warning_count > positive_count:
            overall = "需要关注：存在多个健康指标异常，建议针对性改善"
        elif positive_count > warning_count:
            overall = "状态良好：多项指标呈积极趋势，继续保持"
        else:
            overall = "总体平稳：各项指标基本稳定，注意维持健康习惯"

        return FullReport(
            user_name=self.dataset.user_info.get("first_name", "用户"),
            data_range=self.dataset.data_date_range,
            modules=modules,
            top_insights=top_insights,
            overall_summary=overall
        )
