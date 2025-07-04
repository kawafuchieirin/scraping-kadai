#!/usr/bin/env python3
"""
山手線遅延証明書データスクレイピングツール
JR東日本の遅延証明書履歴ページから1ヶ月分のデータを取得
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os


class YamanoteDelayScraper:
    def __init__(self):
        self.base_url = "https://traininfo.jreast.co.jp/train_info/line.aspx?gid=1&lineid=yamanoteline"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_delay_history_data(self) -> List[Dict]:
        """
        山手線の遅延履歴データを取得（過去45日分）
        
        Returns:
            遅延データのリスト
        """
        try:
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 遅延履歴テーブルを探す
            delay_data = []
            
            # 遅延履歴のテーブルを特定（複数のテーブルがある可能性）
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # ヘッダー行から時間帯情報を取得
                header_row = None
                for row in rows:
                    cells = row.find_all(['th', 'td'])
                    header_text = ''.join([cell.get_text(strip=True) for cell in cells])
                    if '始発' in header_text and '終電' in header_text:
                        header_row = row
                        break
                
                if not header_row:
                    continue
                
                # 時間帯情報を抽出
                time_slots = []
                header_cells = header_row.find_all(['th', 'td'])
                for cell in header_cells[1:]:  # 最初のセル（日付列）をスキップ
                    time_slot = cell.get_text(strip=True)
                    if time_slot and ('時' in time_slot or '始発' in time_slot or '終電' in time_slot):
                        time_slots.append(time_slot)
                
                # データ行を処理
                for row in rows:
                    if row == header_row:
                        continue
                        
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:
                        continue
                    
                    # 日付を抽出
                    date_cell = cells[0]
                    date_text = date_cell.get_text(strip=True)
                    
                    # 日付形式を変換（例：「7月3日」→「2025-07-03」）
                    parsed_date = self._parse_date(date_text)
                    if not parsed_date:
                        continue
                    
                    # 各時間帯のデータを処理
                    for i, time_slot in enumerate(time_slots):
                        if i + 1 < len(cells):
                            delay_cell = cells[i + 1]
                            delay_info = delay_cell.get_text(strip=True)
                            
                            # 遅延時間を抽出
                            delay_minutes = self._extract_delay_minutes(delay_info)
                            
                            delay_data.append({
                                'date': parsed_date,
                                'time_slot': time_slot,
                                'delay_info': delay_info,
                                'delay_minutes': delay_minutes,
                                'has_delay': delay_minutes > 0
                            })
            
            print(f"✅ 遅延履歴データを取得: {len(delay_data)}件")
            return delay_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ ネットワークエラー: {e}")
            return []
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")
            return []
    
    def _parse_date(self, date_text: str) -> Optional[str]:
        """日付テキストをYYYY-MM-DD形式に変換"""
        try:
            # 現在の年を取得
            current_year = datetime.now().year
            
            # 「7月3日」形式をパース
            match = re.search(r'(\d{1,2})月(\d{1,2})日', date_text)
            if match:
                month = int(match.group(1))
                day = int(match.group(2))
                
                # 年を推定（現在の月より未来の月なら前年とする）
                current_month = datetime.now().month
                if month > current_month:
                    year = current_year - 1
                else:
                    year = current_year
                
                return f"{year:04d}-{month:02d}-{day:02d}"
            
            return None
        except Exception:
            return None
    
    def _extract_delay_minutes(self, delay_info: str) -> int:
        """遅延情報から遅延時間（分）を抽出"""
        if not delay_info or delay_info == "-" or delay_info.strip() == "":
            return 0
        
        # 「61分以上」の場合
        if '61分以上' in delay_info or '60分以上' in delay_info:
            return 61
            
        # 「10分」「20分」などの数値を抽出
        match = re.search(r'(\d+)分', delay_info)
        if match:
            return int(match.group(1))
        
        # 「遅延」という文字があれば最小遅延として5分とする
        if '遅延' in delay_info:
            return 5
            
        return 0
    
    def scrape_delay_history(self) -> pd.DataFrame:
        """
        山手線の遅延履歴データを取得（過去45日分）
        
        Returns:
            遅延データのDataFrame
        """
        print("🚆 山手線の遅延履歴データを取得開始...")
        
        # 履歴データを取得
        all_data = self.get_delay_history_data()
        
        # 曜日情報を追加
        for data in all_data:
            try:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
                data['weekday'] = date_obj.strftime('%A')
                data['weekday_jp'] = self._get_japanese_weekday(date_obj.weekday())
            except Exception:
                data['weekday'] = 'Unknown'
                data['weekday_jp'] = '不明'
        
        df = pd.DataFrame(all_data)
        
        if not df.empty:
            # データ型を調整
            df['date'] = pd.to_datetime(df['date'])
            df['delay_minutes'] = df['delay_minutes'].astype(int)
            
            print(f"✅ 合計 {len(df)} 件のデータを取得完了")
            
            # データの期間を表示
            min_date = df['date'].min().strftime('%Y/%m/%d')
            max_date = df['date'].max().strftime('%Y/%m/%d')
            print(f"📅 データ期間: {min_date} ～ {max_date}")
        else:
            print("❌ データが取得できませんでした")
        
        return df
    
    def _get_japanese_weekday(self, weekday: int) -> str:
        """曜日番号を日本語に変換"""
        weekdays = ['月', '火', '水', '木', '金', '土', '日']
        return weekdays[weekday]
    
    def save_data(self, df: pd.DataFrame, filename: str = None) -> str:
        """データをCSVファイルに保存"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'yamanote_delay_data_{timestamp}.csv'
        
        # dataディレクトリに保存
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        filepath = os.path.join(data_dir, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"💾 データを保存しました: {filepath}")
        
        return filepath


def main():
    """メイン関数 - 使用例"""
    scraper = YamanoteDelayScraper()
    
    print("📊 山手線の遅延履歴データ（過去45日分）を取得・分析します")
    
    # データ取得
    df = scraper.scrape_delay_history()
    
    if not df.empty:
        # データ保存
        filepath = scraper.save_data(df)
        
        # 簡単な統計情報を表示
        print("\n📈 データ概要:")
        print(f"・総データ数: {len(df)}件")
        print(f"・遅延発生件数: {df['has_delay'].sum()}件")
        print(f"・遅延発生率: {df['has_delay'].mean():.1%}")
        if df['has_delay'].sum() > 0:
            print(f"・平均遅延時間: {df[df['has_delay']]['delay_minutes'].mean():.1f}分")
        
        print(f"\n次のステップ: python src/analyze_data.py {filepath}")
    else:
        print("❌ データが取得できませんでした。URLやページ構造を確認してください。")


if __name__ == "__main__":
    main()