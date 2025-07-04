---
title: 山手線の遅延証明書データを1ヶ月分スクレイピングしてみたら、意外な真実が見えてきた！
tags: Python スクレイピング データ分析 Streamlit 可視化
author: your_name
slide: false
---

# 🚆 山手線の遅延証明書データを1ヶ月分スクレイピングしてみたら、意外な真実が見えてきた！

## はじめに

毎朝の通勤で山手線を使っているのですが、「今日も遅延してる...」と感じることが多くありませんか？

でも実際のところ、**どの曜日**に、**どの時間帯**に遅延が多いのか、データで見たことはありますか？

そこで今回は、JR東日本の遅延証明書履歴データをスクレイピングして、山手線の遅延パターンを可視化してみました！

さらに、**Streamlitを使ってインタラクティブなダッシュボード**も作成したので、誰でも簡単に遅延データを分析できるようになりました。

## 🎯 この記事で得られること

- ✅ Webスクレイピングの実践的な実装方法
- ✅ BeautifulSoup4を使ったHTMLパース技術
- ✅ pandasによるデータ分析手法
- ✅ Streamlitでのインタラクティブダッシュボード作成
- ✅ 山手線の遅延パターンの真実

## 📊 完成したダッシュボード

![Dashboard Screenshot](https://user-images.githubusercontent.com/xxx/dashboard.png)
*※実際のダッシュボードのスクリーンショットをここに挿入*

## 🛠️ 技術スタック

- **Python 3.8+**
- **requests + BeautifulSoup4**: Webスクレイピング
- **pandas**: データ処理・分析
- **Streamlit**: インタラクティブWebダッシュボード
- **Plotly**: インタラクティブグラフ作成

## 📝 実装の流れ

### 1. JR東日本のページ構造を分析

まず、JR東日本の山手線運行情報ページを分析しました：

```python
url = "https://traininfo.jreast.co.jp/train_info/line.aspx?gid=1&lineid=yamanoteline"
```

このページには過去45日分の遅延証明書履歴が表形式で掲載されています。

### 2. スクレイピングの実装

```python
class YamanoteDelayScraper:
    def __init__(self):
        self.base_url = "https://traininfo.jreast.co.jp/train_info/line.aspx?gid=1&lineid=yamanoteline"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
```

#### ポイント1: 日付のパース

JR東日本のページでは「7月3日」という形式で日付が表示されているため、年を推定する処理を実装しました：

```python
def _parse_date(self, date_text: str) -> Optional[str]:
    """日付テキストをYYYY-MM-DD形式に変換"""
    current_year = datetime.now().year
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
```

#### ポイント2: 遅延時間の抽出

遅延時間は「10分」「20分」「61分以上」などの形式で記載されているため、正規表現で抽出：

```python
def _extract_delay_minutes(self, delay_info: str) -> int:
    """遅延情報から遅延時間（分）を抽出"""
    if '61分以上' in delay_info or '60分以上' in delay_info:
        return 61
        
    match = re.search(r'(\d+)分', delay_info)
    if match:
        return int(match.group(1))
    
    return 0
```

### 3. データ分析・可視化

取得したデータをpandasで分析し、様々な角度から可視化しました。

#### 曜日別・時間帯別ヒートマップ

```python
def create_weekday_heatmap(df):
    """曜日別遅延率ヒートマップを作成"""
    weekday_order = ['月', '火', '水', '木', '金', '土', '日']
    pivot_data = df.groupby(['weekday_jp', 'time_slot'])['has_delay'].mean().unstack(fill_value=0)
    pivot_data = pivot_data.reindex(weekday_order)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Reds'
    ))
    return fig
```

### 4. Streamlitダッシュボードの構築

最後に、分析結果をインタラクティブに探索できるダッシュボードを作成：

```python
st.set_page_config(
    page_title="山手線遅延分析ダッシュボード",
    page_icon="🚆",
    layout="wide"
)

# サイドバーで分析タイプを選択
analysis_type = st.sidebar.selectbox(
    "分析タイプを選択",
    ["概要", "ヒートマップ", "時間帯別分析", "日別傾向", "データテーブル"]
)
```

## 🔍 分析結果から見えてきたこと

### 1. 曜日別の遅延パターン

- **月曜日と金曜日**は他の曜日に比べて遅延発生率が高い
- **土日**は平日に比べて遅延が少ない傾向

### 2. 時間帯別の特徴

- **朝の通勤ラッシュ（7時～10時）**が最も遅延が多い
- **夕方のラッシュ（16時～21時）**も遅延が多いが、朝ほどではない
- **始発～7時**は比較的遅延が少ない

### 3. 遅延時間の分布

- ほとんどの遅延は**10分～20分**
- 30分以上の大規模遅延は比較的少ない

## 💡 得られた知見の活用方法

1. **通勤時間の最適化**: 始発～7時の時間帯を狙えば遅延リスクを減らせる
2. **曜日別の対策**: 月曜・金曜は余裕を持った移動計画を
3. **代替ルートの検討**: 遅延が多い時間帯は他の路線も検討

## 🚀 実際に動かしてみよう

### 環境構築

```bash
# リポジトリをクローン
git clone https://github.com/your-username/yamanote-delay-analysis.git
cd yamanote-delay-analysis

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Mac/Linux
# または
venv\Scripts\activate  # Windows

# 依存関係をインストール
pip install -r requirements.txt
```

### データ取得と分析

```bash
# 過去45日分の遅延データを取得
python src/yamanote_scraper.py

# Streamlitダッシュボードを起動
streamlit run app.py
```

## 📈 今後の拡張アイデア

1. **他路線との比較**: 中央線、総武線なども含めた総合分析
2. **天候データとの相関**: 雨の日は遅延が多い？
3. **リアルタイム通知Bot**: 遅延発生時にLINE/Slackに通知
4. **機械学習による予測**: 過去データから遅延を予測

## 🎯 まとめ

今回は山手線の遅延証明書データをスクレイピングし、Streamlitでインタラクティブなダッシュボードを作成しました。

技術的には以下の点が学べました：

- ✅ BeautifulSoup4を使った実践的なWebスクレイピング
- ✅ pandasによる時系列データの分析手法
- ✅ Streamlitでの高品質なダッシュボード作成
- ✅ Plotlyによるインタラクティブな可視化

そして何より、**データに基づいた意思決定**の重要性を実感できました。
「なんとなく遅延が多い」という感覚を、具体的な数値とグラフで裏付けることができたのは大きな収穫でした。

## 📚 参考リンク

- [ソースコード（GitHub）](https://github.com/your-username/yamanote-delay-analysis)
- [Streamlit公式ドキュメント](https://docs.streamlit.io/)
- [BeautifulSoup4ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## 🙏 最後に

この記事が皆さんの通勤ライフの改善や、データ分析の学習に少しでも役立てば幸いです！

質問やフィードバックがあれば、ぜひコメント欄でお聞かせください。

Happy Coding! 🚆✨