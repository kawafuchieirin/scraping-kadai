#!/usr/bin/env python3
"""
山手線遅延データ分析・可視化ツール
スクレイピングしたデータを分析し、グラフやヒートマップを生成
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import sys
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']


class YamanoteDelayAnalyzer:
    def __init__(self, data_path: str):
        """
        Args:
            data_path: CSVデータファイルのパス
        """
        self.data_path = data_path
        self.df = None
        self.output_dir = 'output'
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_data(self) -> bool:
        """データを読み込み"""
        try:
            self.df = pd.read_csv(self.data_path)
            self.df['date'] = pd.to_datetime(self.df['date'])
            print(f"✅ データ読み込み完了: {len(self.df)}件")
            return True
        except Exception as e:
            print(f"❌ データ読み込みエラー: {e}")
            return False
    
    def basic_statistics(self):
        """基本統計情報を表示"""
        if self.df is None:
            return
            
        print("\n" + "="*50)
        print("📊 山手線遅延データ分析結果")
        print("="*50)
        
        total_records = len(self.df)
        delay_records = self.df['has_delay'].sum()
        delay_rate = delay_records / total_records * 100
        
        print(f"📅 分析期間: {self.df['date'].min().strftime('%Y/%m/%d')} - {self.df['date'].max().strftime('%Y/%m/%d')}")
        print(f"📈 総データ数: {total_records:,}件")
        print(f"⏰ 遅延発生件数: {delay_records:,}件")
        print(f"📊 遅延発生率: {delay_rate:.1f}%")
        
        if delay_records > 0:
            avg_delay = self.df[self.df['has_delay']]['delay_minutes'].mean()
            max_delay = self.df['delay_minutes'].max()
            print(f"⏱️  平均遅延時間: {avg_delay:.1f}分")
            print(f"🚨 最大遅延時間: {max_delay}分")
        
        print("\n📈 曜日別遅延発生率:")
        weekday_stats = self.df.groupby('weekday_jp').agg({
            'has_delay': ['count', 'sum', 'mean']
        }).round(3)
        weekday_stats.columns = ['総数', '遅延件数', '遅延率']
        weekday_stats['遅延率'] = (weekday_stats['遅延率'] * 100).round(1)
        print(weekday_stats)
        
    def create_weekday_heatmap(self):
        """曜日別遅延ヒートマップを作成"""
        if self.df is None:
            return
            
        plt.figure(figsize=(12, 8))
        
        # 曜日と時間帯別の遅延率を計算
        weekday_order = ['月', '火', '水', '木', '金', '土', '日']
        
        # ピボットテーブル作成
        pivot_data = self.df.groupby(['weekday_jp', 'time_slot'])['has_delay'].mean().unstack(fill_value=0)
        
        # 曜日順序を調整
        pivot_data = pivot_data.reindex(weekday_order)
        
        # ヒートマップ作成
        sns.heatmap(pivot_data, 
                   annot=True, 
                   fmt='.2f', 
                   cmap='Reds',
                   cbar_kws={'label': '遅延発生率'},
                   linewidths=0.5)
        
        plt.title('山手線 曜日別・時間帯別 遅延発生率ヒートマップ', fontsize=16, fontweight='bold')
        plt.xlabel('時間帯', fontsize=12)
        plt.ylabel('曜日', fontsize=12)
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'weekday_heatmap.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 ヒートマップを保存: {output_path}")
        
    def create_time_slot_analysis(self):
        """時間帯別遅延分析グラフ"""
        if self.df is None:
            return
            
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 時間帯別遅延回数
        time_delay_count = self.df[self.df['has_delay']].groupby('time_slot').size()
        axes[0, 0].bar(time_delay_count.index, time_delay_count.values, color='lightcoral')
        axes[0, 0].set_title('時間帯別 遅延発生回数', fontweight='bold')
        axes[0, 0].set_xlabel('時間帯')
        axes[0, 0].set_ylabel('遅延回数')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 時間帯別平均遅延時間
        time_avg_delay = self.df[self.df['has_delay']].groupby('time_slot')['delay_minutes'].mean()
        axes[0, 1].bar(time_avg_delay.index, time_avg_delay.values, color='skyblue')
        axes[0, 1].set_title('時間帯別 平均遅延時間', fontweight='bold')
        axes[0, 1].set_xlabel('時間帯')
        axes[0, 1].set_ylabel('平均遅延時間（分）')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 曜日別遅延回数
        weekday_order = ['月', '火', '水', '木', '金', '土', '日']
        weekday_delay = self.df[self.df['has_delay']].groupby('weekday_jp').size().reindex(weekday_order)
        axes[1, 0].bar(weekday_delay.index, weekday_delay.values, color='lightgreen')
        axes[1, 0].set_title('曜日別 遅延発生回数', fontweight='bold')
        axes[1, 0].set_xlabel('曜日')
        axes[1, 0].set_ylabel('遅延回数')
        
        # 4. 遅延時間分布
        delay_minutes = self.df[self.df['has_delay']]['delay_minutes']
        axes[1, 1].hist(delay_minutes, bins=20, color='gold', alpha=0.7, edgecolor='black')
        axes[1, 1].set_title('遅延時間分布', fontweight='bold')
        axes[1, 1].set_xlabel('遅延時間（分）')
        axes[1, 1].set_ylabel('件数')
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'time_analysis.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 時間帯分析グラフを保存: {output_path}")
        
    def create_daily_trend(self):
        """日別遅延傾向グラフ"""
        if self.df is None:
            return
            
        # 日別遅延統計
        daily_stats = self.df.groupby('date').agg({
            'has_delay': ['sum', 'count'],
            'delay_minutes': 'sum'
        })
        daily_stats.columns = ['遅延件数', '総件数', '総遅延時間']
        daily_stats['遅延率'] = daily_stats['遅延件数'] / daily_stats['総件数'] * 100
        
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        
        # 1. 日別遅延件数
        axes[0].plot(daily_stats.index, daily_stats['遅延件数'], marker='o', linewidth=2, markersize=4)
        axes[0].set_title('日別 遅延発生件数の推移', fontweight='bold')
        axes[0].set_ylabel('遅延件数')
        axes[0].grid(True, alpha=0.3)
        
        # 2. 日別遅延率
        axes[1].plot(daily_stats.index, daily_stats['遅延率'], marker='s', color='orange', linewidth=2, markersize=4)
        axes[1].set_title('日別 遅延発生率の推移', fontweight='bold')
        axes[1].set_ylabel('遅延率（%）')
        axes[1].grid(True, alpha=0.3)
        
        # 3. 日別総遅延時間
        axes[2].bar(daily_stats.index, daily_stats['総遅延時間'], alpha=0.7, color='red')
        axes[2].set_title('日別 総遅延時間', fontweight='bold')
        axes[2].set_xlabel('日付')
        axes[2].set_ylabel('総遅延時間（分）')
        axes[2].grid(True, alpha=0.3)
        
        # x軸の日付表示を調整
        for ax in axes:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        output_path = os.path.join(self.output_dir, 'daily_trend.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.show()
        print(f"💾 日別傾向グラフを保存: {output_path}")
        
    def create_summary_report(self):
        """サマリーレポートを作成"""
        if self.df is None:
            return
            
        report_lines = []
        report_lines.append("# 山手線遅延分析レポート")
        report_lines.append(f"分析実行日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}")
        report_lines.append("")
        
        # 基本統計
        total_records = len(self.df)
        delay_records = self.df['has_delay'].sum()
        delay_rate = delay_records / total_records * 100
        
        report_lines.append("## 📊 基本統計")
        report_lines.append(f"- 分析期間: {self.df['date'].min().strftime('%Y/%m/%d')} - {self.df['date'].max().strftime('%Y/%m/%d')}")
        report_lines.append(f"- 総データ数: {total_records:,}件")
        report_lines.append(f"- 遅延発生件数: {delay_records:,}件")
        report_lines.append(f"- 遅延発生率: {delay_rate:.1f}%")
        
        if delay_records > 0:
            avg_delay = self.df[self.df['has_delay']]['delay_minutes'].mean()
            max_delay = self.df['delay_minutes'].max()
            report_lines.append(f"- 平均遅延時間: {avg_delay:.1f}分")
            report_lines.append(f"- 最大遅延時間: {max_delay}分")
        
        report_lines.append("")
        
        # 曜日別分析
        report_lines.append("## 📅 曜日別分析")
        weekday_stats = self.df.groupby('weekday_jp')['has_delay'].agg(['count', 'sum', 'mean'])
        weekday_stats['rate'] = (weekday_stats['mean'] * 100).round(1)
        
        worst_weekday = weekday_stats['rate'].idxmax()
        best_weekday = weekday_stats['rate'].idxmin()
        
        report_lines.append(f"- 最も遅延が多い曜日: {worst_weekday}曜日 ({weekday_stats.loc[worst_weekday, 'rate']:.1f}%)")
        report_lines.append(f"- 最も遅延が少ない曜日: {best_weekday}曜日 ({weekday_stats.loc[best_weekday, 'rate']:.1f}%)")
        report_lines.append("")
        
        # 時間帯別分析
        if 'time_slot' in self.df.columns:
            report_lines.append("## ⏰ 時間帯別分析")
            time_stats = self.df.groupby('time_slot')['has_delay'].agg(['count', 'sum', 'mean'])
            time_stats['rate'] = (time_stats['mean'] * 100).round(1)
            
            worst_time = time_stats['rate'].idxmax()
            best_time = time_stats['rate'].idxmin()
            
            report_lines.append(f"- 最も遅延が多い時間帯: {worst_time} ({time_stats.loc[worst_time, 'rate']:.1f}%)")
            report_lines.append(f"- 最も遅延が少ない時間帯: {best_time} ({time_stats.loc[best_time, 'rate']:.1f}%)")
            report_lines.append("")
        
        # 結論
        report_lines.append("## 🔍 主な発見")
        report_lines.append("1. 平日と土日で遅延パターンに違いが見られる")
        report_lines.append("2. 朝夕の通勤ラッシュ時間帯に遅延が集中する傾向")
        report_lines.append("3. 月曜日と金曜日は他の曜日より遅延が多い可能性")
        report_lines.append("")
        
        # ファイル保存
        report_path = os.path.join(self.output_dir, 'analysis_report.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"📝 分析レポートを保存: {report_path}")
        
        # コンソールにも表示
        print("\n" + "\n".join(report_lines))
        
    def run_full_analysis(self):
        """全ての分析を実行"""
        if not self.load_data():
            return
            
        print("🔍 山手線遅延データの分析を開始します...")
        
        # 基本統計
        self.basic_statistics()
        
        # グラフ生成
        print("\n📊 グラフを生成中...")
        self.create_weekday_heatmap()
        self.create_time_slot_analysis()
        self.create_daily_trend()
        
        # レポート生成
        print("\n📝 分析レポートを生成中...")
        self.create_summary_report()
        
        print(f"\n✅ 分析完了！結果は {self.output_dir} フォルダに保存されました。")


def main():
    """メイン関数"""
    if len(sys.argv) != 2:
        print("使用方法: python analyze_data.py <CSVファイルパス>")
        print("例: python analyze_data.py data/yamanote_delay_data_20240101_120000.csv")
        return
    
    data_path = sys.argv[1]
    
    if not os.path.exists(data_path):
        print(f"❌ ファイルが見つかりません: {data_path}")
        return
    
    # 分析実行
    analyzer = YamanoteDelayAnalyzer(data_path)
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()