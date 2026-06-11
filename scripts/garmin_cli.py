#!/usr/bin/env python3
"""
Garmin Data Analyzer CLI — 一键分析 Garmin 导出数据

用法:
    python garmin_cli.py <garmin_export.zip> [--output report.md] [--summary]

参数:
    garmin_export.zip   Garmin Connect 导出的 ZIP 文件路径
    --output, -o        输出文件路径（默认: garmin_report.md）
    --summary, -s       仅输出简要摘要
    --json, -j          输出 JSON 格式（供程序化使用）
"""

import argparse
import io
import json
import sys
import os

# 修复 Windows 控制台编码
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from garmin_parser import GarminDataParser
from garmin_analyzer import GarminAnalyzer
from garmin_report import GarminReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description="Garmin Data Analyzer - 分析 Garmin Connect 导出的运动/健康数据"
    )
    parser.add_argument("zip_path", help="Garmin Connect 导出的 ZIP 文件路径")
    parser.add_argument("--output", "-o", default="garmin_report.md",
                        help="输出文件路径（默认: garmin_report.md）")
    parser.add_argument("--summary", "-s", action="store_true",
                        help="仅输出简要摘要到控制台")
    parser.add_argument("--json", "-j", action="store_true",
                        help="输出 JSON 格式结果")

    args = parser.parse_args()

    if not os.path.exists(args.zip_path):
        print(f"[错误] 文件不存在: {args.zip_path}")
        sys.exit(1)

    print(f"[解析] 正在读取 Garmin 数据包: {args.zip_path}")

    try:
        with GarminDataParser(args.zip_path) as gparser:
            # 第一步: 解析数据
            dataset = gparser.parse_all()

            print(f"[完成] 解析完成:")
            print(f"  用户: {dataset.user_info.get('first_name', 'N/A')}")
            print(f"  数据范围: {dataset.data_date_range.get('start', 'N/A')} ~ {dataset.data_date_range.get('end', 'N/A')}")
            print(f"  每日汇总: {len(dataset.daily_summaries)} 条")
            print(f"  睡眠记录: {len(dataset.sleep_records)} 条")
            print(f"  体能年龄: {len(dataset.fitness_age_records)} 条")
            print(f"  跑步预测: {len(dataset.race_predictions)} 条")
            print(f"  训练状态: {len(dataset.training_status_records)} 条")

            # 第二步: 分析数据
            print()
            print("[分析] 正在生成洞察...")
            analyzer = GarminAnalyzer(dataset)
            report = analyzer.generate_full_report()

            # 第三步: 生成报告
            generator = GarminReportGenerator(report)

            if args.summary:
                # 简要摘要模式
                summary = generator.generate_summary()
                print()
                print("=" * 60)
                print(summary)
                print("=" * 60)
            elif args.json:
                # JSON 输出模式
                output = {
                    "user": report.user_name,
                    "data_range": report.data_range,
                    "overall_summary": report.overall_summary,
                    "modules": [],
                }
                for m in report.modules:
                    module_data = {
                        "name": m.module_name,
                        "title": m.title,
                        "key_metrics": m.key_metrics,
                        "insights": [
                            {
                                "indicator": i.indicator,
                                "trend": i.trend,
                                "severity": i.severity,
                                "summary": i.summary,
                                "detail": i.detail,
                                "recommendation": i.recommendation,
                            }
                            for i in m.insights
                        ],
                    }
                    output["modules"].append(module_data)

                output["top_insights"] = [
                    {
                        "indicator": i.indicator,
                        "severity": i.severity,
                        "summary": i.summary,
                        "detail": i.detail,
                    }
                    for i in report.top_insights
                ]

                json_str = json.dumps(output, ensure_ascii=False, indent=2)

                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                print(f"[完成] JSON 报告已保存: {args.output}")
            else:
                # Markdown 报告模式
                markdown = generator.generate()

                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(markdown)
                print(f"[完成] Markdown 报告已保存: {args.output}")

                # 同时输出简要摘要
                print()
                print("=" * 60)
                print(generator.generate_summary())
                print("=" * 60)

    except Exception as e:
        print(f"[错误] 分析失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
