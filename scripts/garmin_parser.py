#!/usr/bin/env python3
"""
Garmin Data Parser — 解析 Garmin Connect 导出的 ZIP 数据包

从 Garmin 官网导出的 ZIP 压缩包中提取并结构化运动/健康数据。
仅使用 Python 标准库，跨平台兼容。

用法:
    from garmin_parser import GarminDataParser
    parser = GarminDataParser("path/to/garmin_export.zip")
    dataset = parser.parse_all()
"""

import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional


# ─── 数据模型 ──────────────────────────────────────────────

@dataclass
class DailySummary:
    """每日健康汇总 (UDSFile)"""
    calendar_date: str
    total_steps: Optional[int] = None
    total_kilocalories: Optional[float] = None
    active_kilocalories: Optional[float] = None
    resting_heart_rate: Optional[int] = None
    min_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    average_stress_level: Optional[float] = None
    stress_low_duration: Optional[int] = None      # seconds
    stress_medium_duration: Optional[int] = None    # seconds
    stress_high_duration: Optional[int] = None      # seconds
    body_battery_charged: Optional[int] = None
    body_battery_drained: Optional[int] = None
    body_battery_highest: Optional[int] = None
    body_battery_lowest: Optional[int] = None
    average_spo2: Optional[float] = None
    respiration: Optional[float] = None
    floors_ascended_meters: Optional[float] = None
    floors_descended_meters: Optional[float] = None
    intensity_minutes: Optional[int] = None         # seconds
    moderate_intensity_minutes: Optional[int] = None
    vigorous_intensity_minutes: Optional[int] = None


@dataclass
class SleepRecord:
    """睡眠记录"""
    calendar_date: str
    deep_sleep_seconds: Optional[int] = None
    light_sleep_seconds: Optional[int] = None
    rem_sleep_seconds: Optional[int] = None
    awake_sleep_seconds: Optional[int] = None
    unmeasurable_seconds: Optional[int] = None
    total_sleep_seconds: Optional[int] = None
    sleep_score_overall: Optional[int] = None
    sleep_score_quality: Optional[int] = None
    sleep_score_duration: Optional[int] = None
    sleep_score_recovery: Optional[int] = None
    sleep_score_deep: Optional[int] = None
    sleep_score_rem: Optional[int] = None
    sleep_score_light: Optional[int] = None
    sleep_score_awakenings: Optional[int] = None
    sleep_score_awake_time: Optional[int] = None
    sleep_score_restfulness: Optional[int] = None
    sleep_score_interruptions: Optional[int] = None
    avg_sleep_stress: Optional[float] = None
    nap: Optional[bool] = None
    nap_count: Optional[int] = None
    feedback: Optional[str] = None
    insight: Optional[str] = None
    avg_respiration: Optional[float] = None
    lowest_respiration: Optional[float] = None
    highest_respiration: Optional[float] = None
    spo2_avg: Optional[float] = None
    spo2_lowest: Optional[int] = None
    sleep_start_gmt: Optional[str] = None
    sleep_end_gmt: Optional[str] = None
    restless_moment_count: Optional[int] = None


@dataclass
class FitnessAgeRecord:
    """体能年龄"""
    timestamp: Optional[str] = None
    chronological_age: Optional[float] = None
    current_bio_age: Optional[float] = None
    bmi: Optional[float] = None
    resting_heart_rate: Optional[float] = None
    vo2_max: Optional[float] = None


@dataclass
class RacePrediction:
    """跑步比赛预测"""
    timestamp: Optional[str] = None
    race_time_5k: Optional[int] = None        # seconds
    race_time_10k: Optional[int] = None
    race_time_half: Optional[int] = None
    race_time_marathon: Optional[int] = None


@dataclass
class TrainingStatusRecord:
    """训练状态"""
    timestamp: Optional[str] = None
    training_status: Optional[str] = None      # e.g. PEAKING, PRODUCTIVE, RECOVERY, DETRAINING
    fitness_level_trend: Optional[str] = None


@dataclass
class HeartRateZone:
    """心率区间配置"""
    zone_type: str                              # DEFAULT, RUNNING, etc.
    zone1_floor: Optional[int] = None
    zone2_floor: Optional[int] = None
    zone3_floor: Optional[int] = None
    zone4_floor: Optional[int] = None
    zone5_floor: Optional[int] = None
    max_heart_rate: Optional[int] = None
    training_method: Optional[str] = None


@dataclass
class HydrationRecord:
    """饮水记录"""
    calendar_date: str
    value_in_ml: Optional[float] = None
    goal_in_ml: Optional[float] = None


@dataclass
class GarminDataset:
    """Garmin 数据集（所有解析结果）"""
    user_info: dict = field(default_factory=dict)
    daily_summaries: list = field(default_factory=list)
    sleep_records: list = field(default_factory=list)
    fitness_age_records: list = field(default_factory=list)
    race_predictions: list = field(default_factory=list)
    training_status_records: list = field(default_factory=list)
    heart_rate_zones: list = field(default_factory=list)
    hydration_records: list = field(default_factory=list)
    data_date_range: dict = field(default_factory=dict)  # {"start": "...", "end": "..."}
    parse_errors: list = field(default_factory=list)


# ─── 辅助函数 ──────────────────────────────────────────────

def _safe_get(data: dict, *keys, default=None):
    """安全获取嵌套字典值"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def _safe_int(value, default=None):
    """安全转换为整数"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _safe_float(value, default=None):
    """安全转换为浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def _parse_timestamp(ts) -> Optional[str]:
    """解析时间戳为 ISO 格式字符串"""
    if ts is None:
        return None
    if isinstance(ts, (int, float)):
        # Garmin 使用毫秒时间戳
        try:
            if ts > 1e12:  # 毫秒
                ts = ts / 1000
            return datetime.fromtimestamp(ts).isoformat()
        except (ValueError, OSError):
            return None
    return str(ts)


def _seconds_to_human(seconds: int) -> str:
    """将秒数转为人类可读格式"""
    if seconds is None:
        return "N/A"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    return f"{minutes}m {secs}s"


# ─── 核心解析器 ────────────────────────────────────────────

class GarminDataParser:
    """
    Garmin 数据解析器

    用法:
        parser = GarminDataParser("garmin_export.zip")
        dataset = parser.parse_all()
        print(f"解析了 {len(dataset.daily_summaries)} 天的数据")
    """

    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self._temp_dir = None
        self._extract_root = None
        self._file_map = {}  # category -> [file_paths]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def extract(self) -> dict:
        """
        解压 ZIP 并分类文件

        返回:
            文件分类映射 {"daily_summary": [...], "sleep": [...], ...}
        """
        if not os.path.exists(self.zip_path):
            raise FileNotFoundError(f"ZIP 文件不存在: {self.zip_path}")

        self._temp_dir = tempfile.mkdtemp(prefix="garmin_parse_")

        with zipfile.ZipFile(self.zip_path, 'r') as zf:
            zf.extractall(self._temp_dir)

        # 找到实际根目录（可能有多层）
        self._extract_root = self._temp_dir
        entries = os.listdir(self._temp_dir)
        if len(entries) == 1 and os.path.isdir(os.path.join(self._temp_dir, entries[0])):
            self._extract_root = os.path.join(self._temp_dir, entries[0])

        # 按类别分类文件
        self._file_map = {
            "customer": [],
            "daily_summary": [],
            "hydration": [],
            "fitness": [],
            "sleep": [],
            "fitness_age": [],
            "heart_rate_zones": [],
            "abnormal_hr": [],
            "vo2max": [],
            "endurance_score": [],
            "hill_score": [],
            "acute_training_load": [],
            "max_met": [],
            "race_predictions": [],
            "training_history": [],
            "training_readiness": [],
            "calendar_items": [],
            "user_goal": [],
            "events": [],
            "golf": [],
            "autosport": [],
            "other": [],
        }

        for root, dirs, files in os.walk(self._extract_root):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, self._extract_root)

                if fname == "customer.json":
                    self._file_map["customer"].append(fpath)
                elif fname.startswith("UDSFile_"):
                    self._file_map["daily_summary"].append(fpath)
                elif fname.startswith("HydrationLogFile_"):
                    self._file_map["hydration"].append(fpath)
                elif fname.endswith("_sleepData.json") or fname.startswith("sleepData_"):
                    self._file_map["sleep"].append(fpath)
                elif "fitnessAgeData" in fname:
                    self._file_map["fitness_age"].append(fpath)
                elif "heartRateZones" in fname:
                    self._file_map["heart_rate_zones"].append(fpath)
                elif fname.endswith("_AbnormalHrEvents.json") or "AbnormalHrEvents" in fname:
                    self._file_map["abnormal_hr"].append(fpath)
                elif "ActivityVo2Max" in fname:
                    self._file_map["vo2max"].append(fpath)
                elif "EnduranceScore" in fname:
                    self._file_map["endurance_score"].append(fpath)
                elif "HillScore" in fname:
                    self._file_map["hill_score"].append(fpath)
                elif "MetricsAcuteTrainingLoad" in fname:
                    self._file_map["acute_training_load"].append(fpath)
                elif "MetricsMaxMetData" in fname:
                    self._file_map["max_met"].append(fpath)
                elif "RunRacePredictions" in fname:
                    self._file_map["race_predictions"].append(fpath)
                elif "TrainingHistory" in fname:
                    self._file_map["training_history"].append(fpath)
                elif "TrainingReadinessDTO" in fname:
                    self._file_map["training_readiness"].append(fpath)
                elif "CalendarItems" in fname:
                    self._file_map["calendar_items"].append(fpath)
                elif "UserGoal" in fname:
                    self._file_map["user_goal"].append(fpath)
                elif fname == "events.json":
                    self._file_map["events"].append(fpath)
                elif "DI-GOLF" in rel_path:
                    self._file_map["golf"].append(fpath)
                elif "DI_BOOT_AUTOSPORT" in rel_path:
                    self._file_map["autosport"].append(fpath)
                else:
                    self._file_map["other"].append(fpath)

        return self._file_map

    def _load_json(self, filepath: str) -> Any:
        """加载 JSON 文件，处理异常"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            # 尝试其他编码
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return json.load(f)
            except:
                return None
        except Exception as e:
            return None

    def parse_customer(self) -> dict:
        """解析用户基本信息"""
        if not self._file_map.get("customer"):
            return {}

        data = self._load_json(self._file_map["customer"][0])
        if not data:
            return {}

        return {
            "first_name": data.get("firstName", ""),
            "username": data.get("username", ""),
            "email": data.get("email", ""),
            "locale": data.get("locale", ""),
            "display_name": data.get("displayName", ""),
        }

    def parse_daily_summary(self) -> list:
        """
        解析每日健康汇总 (UDSFile)

        每个文件包含约 3 个月的日数据（JSON 数组）。
        """
        records = []

        for filepath in sorted(self._file_map.get("daily_summary", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                # 跳过空记录或仅含 retro 标记的记录
                if not item or (isinstance(item, dict) and set(item.keys()) == {"retro"}):
                    continue

                try:
                    stress = item.get("allDayStress", {})
                    bb = item.get("bodyBatteryChargedValueAndDrainedValue", {})

                    record = DailySummary(
                        calendar_date=item.get("calendarDate", ""),
                        total_steps=_safe_int(item.get("totalSteps")),
                        total_kilocalories=_safe_float(item.get("totalKilocalories")),
                        active_kilocalories=_safe_float(item.get("activeKilocalories")),
                        resting_heart_rate=_safe_int(item.get("restingHeartRate")),
                        min_heart_rate=_safe_int(item.get("minHeartRate")),
                        max_heart_rate=_safe_int(item.get("maxHeartRate")),
                        average_stress_level=_safe_float(stress.get("averageStressLevel")),
                        stress_low_duration=_safe_int(stress.get("lowDuration")),
                        stress_medium_duration=_safe_int(stress.get("mediumDuration")),
                        stress_high_duration=_safe_int(stress.get("highDuration")),
                        body_battery_charged=_safe_int(bb.get("chargedValue")),
                        body_battery_drained=_safe_int(bb.get("drainedValue")),
                        body_battery_highest=_safe_int(bb.get("HIGHEST")),
                        body_battery_lowest=_safe_int(bb.get("LOWEST")),
                        average_spo2=_safe_float(item.get("averageSpo2Value")),
                        respiration=_safe_float(item.get("respiration")),
                        floors_ascended_meters=_safe_float(item.get("floorsAscendedInMeters")),
                        floors_descended_meters=_safe_float(item.get("floorsDescendedInMeters")),
                        intensity_minutes=_safe_int(item.get("intensityMinutes")),
                        moderate_intensity_minutes=_safe_int(item.get("moderateIntensityMinutes")),
                        vigorous_intensity_minutes=_safe_int(item.get("vigorousIntensityMinutes")),
                    )
                    records.append(record)
                except Exception:
                    continue

        # 按日期排序
        records.sort(key=lambda r: r.calendar_date)
        return records

    def parse_sleep(self) -> list:
        """解析睡眠数据"""
        records = []

        for filepath in sorted(self._file_map.get("sleep", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                # 跳过仅含 retro 标记的空记录
                if not item or (isinstance(item, dict) and set(item.keys()) == {"retro"}):
                    continue

                try:
                    scores = item.get("sleepScores", {})
                    spo2 = item.get("spo2SleepSummary", {})
                    nap_list = item.get("napList", [])

                    # 计算总睡眠时间（如无显式字段则累加各阶段）
                    total_sleep = _safe_int(item.get("sleepTimeSeconds"))
                    if total_sleep is None:
                        ds = _safe_int(item.get("deepSleepSeconds")) or 0
                        ls = _safe_int(item.get("lightSleepSeconds")) or 0
                        rs = _safe_int(item.get("remSleepSeconds")) or 0
                        total_sleep = ds + ls + rs

                    record = SleepRecord(
                        calendar_date=item.get("calendarDate", ""),
                        deep_sleep_seconds=_safe_int(item.get("deepSleepSeconds")),
                        light_sleep_seconds=_safe_int(item.get("lightSleepSeconds")),
                        rem_sleep_seconds=_safe_int(item.get("remSleepSeconds")),
                        awake_sleep_seconds=_safe_int(item.get("awakeSleepSeconds")),
                        unmeasurable_seconds=_safe_int(item.get("unmeasurableSeconds")),
                        total_sleep_seconds=total_sleep,
                        sleep_score_overall=_safe_int(scores.get("overallScore")),
                        sleep_score_quality=_safe_int(scores.get("qualityScore")),
                        sleep_score_duration=_safe_int(scores.get("durationScore")),
                        sleep_score_recovery=_safe_int(scores.get("recoveryScore")),
                        sleep_score_deep=_safe_int(scores.get("deepScore")),
                        sleep_score_rem=_safe_int(scores.get("remScore")),
                        sleep_score_light=_safe_int(scores.get("lightScore")),
                        sleep_score_awakenings=_safe_int(scores.get("awakeningsCountScore")),
                        sleep_score_awake_time=_safe_int(scores.get("awakeTimeScore")),
                        sleep_score_restfulness=_safe_int(scores.get("restfulnessScore")),
                        sleep_score_interruptions=_safe_int(scores.get("interruptionsScore")),
                        avg_sleep_stress=_safe_float(item.get("avgSleepStress")),
                        nap=len(nap_list) > 0 if isinstance(nap_list, list) else item.get("nap", False),
                        nap_count=len(nap_list) if isinstance(nap_list, list) else None,
                        feedback=scores.get("feedback", ""),
                        insight=scores.get("insight", ""),
                        avg_respiration=_safe_float(item.get("averageRespiration")),
                        lowest_respiration=_safe_float(item.get("lowestRespiration")),
                        highest_respiration=_safe_float(item.get("highestRespiration")),
                        spo2_avg=_safe_float(spo2.get("averageSPO2")),
                        spo2_lowest=_safe_int(spo2.get("lowestSPO2")),
                        sleep_start_gmt=item.get("sleepStartTimestampGMT", ""),
                        sleep_end_gmt=item.get("sleepEndTimestampGMT", ""),
                        restless_moment_count=_safe_int(item.get("restlessMomentCount")),
                    )
                    records.append(record)
                except Exception:
                    continue

        records.sort(key=lambda r: r.calendar_date)
        return records

    def parse_fitness_age(self) -> list:
        """解析体能年龄数据"""
        records = []

        for filepath in sorted(self._file_map.get("fitness_age", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                if not item:
                    continue
                try:
                    record = FitnessAgeRecord(
                        timestamp=_parse_timestamp(item.get("timestamp")),
                        chronological_age=_safe_float(item.get("chronologicalAge")),
                        current_bio_age=_safe_float(item.get("currentBioAge")),
                        bmi=_safe_float(item.get("bmi")),
                        resting_heart_rate=_safe_float(item.get("rhr")),
                        vo2_max=_safe_float(item.get("biometricVo2Max")),
                    )
                    records.append(record)
                except Exception:
                    continue

        return records

    def parse_race_predictions(self) -> list:
        """解析跑步比赛预测"""
        records = []

        for filepath in sorted(self._file_map.get("race_predictions", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                if not item:
                    continue
                try:
                    record = RacePrediction(
                        timestamp=_parse_timestamp(item.get("timestamp")),
                        race_time_5k=_safe_int(item.get("raceTime5K")),
                        race_time_10k=_safe_int(item.get("raceTime10K")),
                        race_time_half=_safe_int(item.get("raceTimeHalf")),
                        race_time_marathon=_safe_int(item.get("raceTimeMarathon")),
                    )
                    records.append(record)
                except Exception:
                    continue

        return records

    def parse_training_history(self) -> list:
        """解析训练状态历史"""
        records = []

        for filepath in sorted(self._file_map.get("training_history", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                if not item:
                    continue
                try:
                    record = TrainingStatusRecord(
                        timestamp=_parse_timestamp(item.get("timestamp")),
                        training_status=item.get("trainingStatus", ""),
                        fitness_level_trend=item.get("fitnessLevelTrend", ""),
                    )
                    records.append(record)
                except Exception:
                    continue

        return records

    def parse_hr_zones(self) -> list:
        """解析心率区间配置"""
        records = []

        for filepath in sorted(self._file_map.get("heart_rate_zones", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                if not item:
                    continue
                try:
                    record = HeartRateZone(
                        zone_type=item.get("sport", item.get("zoneType", "UNKNOWN")),
                        zone1_floor=_safe_int(item.get("zone1Floor")),
                        zone2_floor=_safe_int(item.get("zone2Floor")),
                        zone3_floor=_safe_int(item.get("zone3Floor")),
                        zone4_floor=_safe_int(item.get("zone4Floor")),
                        zone5_floor=_safe_int(item.get("zone5Floor")),
                        max_heart_rate=_safe_int(item.get("maxHeartRateUsed")),
                        training_method=item.get("trainingMethod", ""),
                    )
                    records.append(record)
                except Exception:
                    continue

        return records

    def parse_hydration(self) -> list:
        """解析饮水记录"""
        records = []

        for filepath in sorted(self._file_map.get("hydration", [])):
            data = self._load_json(filepath)
            if not data:
                continue

            if not isinstance(data, list):
                data = [data]

            for item in data:
                if not item:
                    continue
                try:
                    record = HydrationRecord(
                        calendar_date=item.get("calendarDate", ""),
                        value_in_ml=_safe_float(item.get("valueInML")),
                        goal_in_ml=_safe_float(item.get("goalInML")),
                    )
                    records.append(record)
                except Exception:
                    continue

        records.sort(key=lambda r: r.calendar_date)
        return records

    def parse_all(self) -> GarminDataset:
        """
        一键解析所有 P0 数据

        返回:
            GarminDataset 对象，包含所有解析结果
        """
        # 确保已解压
        if not self._file_map:
            self.extract()

        dataset = GarminDataset()

        # 解析用户信息
        dataset.user_info = self.parse_customer()

        # 解析各类数据
        dataset.daily_summaries = self.parse_daily_summary()
        dataset.sleep_records = self.parse_sleep()
        dataset.fitness_age_records = self.parse_fitness_age()
        dataset.race_predictions = self.parse_race_predictions()
        dataset.training_status_records = self.parse_training_history()
        dataset.heart_rate_zones = self.parse_hr_zones()
        dataset.hydration_records = self.parse_hydration()

        # 计算数据日期范围
        all_dates = []
        for r in dataset.daily_summaries:
            if r.calendar_date:
                all_dates.append(r.calendar_date)
        for r in dataset.sleep_records:
            if r.calendar_date:
                all_dates.append(r.calendar_date)

        if all_dates:
            all_dates.sort()
            dataset.data_date_range = {
                "start": all_dates[0],
                "end": all_dates[-1],
                "total_days": len(set(all_dates)),
            }

        return dataset

    def cleanup(self):
        """清理临时解压目录"""
        if self._temp_dir and os.path.exists(self._temp_dir):
            import shutil
            shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def get_file_summary(self) -> dict:
        """获取文件分类摘要（不解析内容）"""
        if not self._file_map:
            self.extract()

        return {
            category: len(files)
            for category, files in self._file_map.items()
            if files
        }


# ─── 独立运行 ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import io

    # 修复 Windows 控制台编码
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    if len(sys.argv) < 2:
        print("用法: python garmin_parser.py <garmin_export.zip>")
        sys.exit(1)

    zip_path = sys.argv[1]
    parser = GarminDataParser(zip_path)

    try:
        # 文件分类摘要
        file_summary = parser.get_file_summary()
        print("=" * 60)
        print("[文件分类] Garmin 数据包")
        print("=" * 60)
        for category, count in sorted(file_summary.items()):
            print(f"  {category}: {count} 个文件")

        # 解析全部数据
        dataset = parser.parse_all()

        print()
        print("=" * 60)
        print("[解析结果] 数据概览")
        print("=" * 60)
        print(f"  用户: {dataset.user_info.get('first_name', 'N/A')}")
        print(f"  数据范围: {dataset.data_date_range.get('start', 'N/A')} ~ {dataset.data_date_range.get('end', 'N/A')}")
        print(f"  总天数: {dataset.data_date_range.get('total_days', 'N/A')}")
        print()
        print(f"  每日汇总记录: {len(dataset.daily_summaries)}")
        print(f"  睡眠记录: {len(dataset.sleep_records)}")
        print(f"  体能年龄记录: {len(dataset.fitness_age_records)}")
        print(f"  跑步预测记录: {len(dataset.race_predictions)}")
        print(f"  训练状态记录: {len(dataset.training_status_records)}")
        print(f"  心率区间配置: {len(dataset.heart_rate_zones)}")
        print(f"  饮水记录: {len(dataset.hydration_records)}")

        if dataset.parse_errors:
            print(f"\n  [!] 解析错误: {len(dataset.parse_errors)}")

    finally:
        parser.cleanup()
