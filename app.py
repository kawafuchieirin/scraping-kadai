#!/usr/bin/env python3
"""
山手線遅延分析 Streamlit ダッシュボード
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os
import glob

# Streamlitの設定
st.set_page_config(
    page_title="山手線遅延分析ダッシュボード",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stAlert {
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """データファイルを読み込む"""
    data_files = glob.glob("data/*.csv")
    if not data_files:
        return None
    
    # 最新のファイルを選択
    latest_file = max(data_files, key=os.path.getctime)
    
    try:
        df = pd.read_csv(latest_file)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        st.error(f"データファイルの読み込みに失敗しました: {e}")
        return None

def create_weekday_heatmap(df):
    """曜日別遅延率ヒートマップを作成"""
    # 曜日順序を定義
    weekday_order = ['月', '火', '水', '木', '金', '土', '日']
    
    # ピボットテーブル作成
    pivot_data = df.groupby(['weekday_jp', 'time_slot'])['has_delay'].mean().unstack(fill_value=0)
    
    # 曜日順序を調整
    pivot_data = pivot_data.reindex(weekday_order)
    
    # Plotlyヒートマップ作成
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='Reds',
        hoverongaps=False,
        colorbar=dict(title="遅延発生率")
    ))
    
    fig.update_layout(
        title="曜日別・時間帯別 遅延発生率ヒートマップ",
        xaxis_title="時間帯",
        yaxis_title="曜日",
        height=500
    )
    
    return fig

def create_time_analysis_charts(df):
    """時間帯別分析チャートを作成"""
    # サブプロット作成
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("時間帯別 遅延発生回数", "時間帯別 平均遅延時間", 
                       "曜日別 遅延発生回数", "遅延時間分布"),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # 1. 時間帯別遅延回数
    time_delay_count = df[df['has_delay']].groupby('time_slot').size()
    fig.add_trace(
        go.Bar(x=time_delay_count.index, y=time_delay_count.values, 
               name="遅延回数", marker_color='lightcoral'),
        row=1, col=1
    )
    
    # 2. 時間帯別平均遅延時間
    time_avg_delay = df[df['has_delay']].groupby('time_slot')['delay_minutes'].mean()
    fig.add_trace(
        go.Bar(x=time_avg_delay.index, y=time_avg_delay.values, 
               name="平均遅延時間", marker_color='skyblue'),
        row=1, col=2
    )
    
    # 3. 曜日別遅延回数
    weekday_order = ['月', '火', '水', '木', '金', '土', '日']
    weekday_delay = df[df['has_delay']].groupby('weekday_jp').size().reindex(weekday_order)
    fig.add_trace(
        go.Bar(x=weekday_delay.index, y=weekday_delay.values, 
               name="曜日別遅延", marker_color='lightgreen'),
        row=2, col=1
    )
    
    # 4. 遅延時間分布
    delay_minutes = df[df['has_delay']]['delay_minutes']
    fig.add_trace(
        go.Histogram(x=delay_minutes, nbinsx=20, name="遅延時間分布", 
                    marker_color='gold'),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=False)
    fig.update_xaxes(title_text="時間帯", row=1, col=1)
    fig.update_xaxes(title_text="時間帯", row=1, col=2)
    fig.update_xaxes(title_text="曜日", row=2, col=1)
    fig.update_xaxes(title_text="遅延時間（分）", row=2, col=2)
    
    fig.update_yaxes(title_text="遅延回数", row=1, col=1)
    fig.update_yaxes(title_text="平均遅延時間（分）", row=1, col=2)
    fig.update_yaxes(title_text="遅延回数", row=2, col=1)
    fig.update_yaxes(title_text="件数", row=2, col=2)
    
    return fig

def create_daily_trend_chart(df):
    """日別遅延傾向チャートを作成"""
    # 日別統計を計算
    daily_stats = df.groupby('date').agg({
        'has_delay': ['sum', 'count'],
        'delay_minutes': 'sum'
    })
    daily_stats.columns = ['遅延件数', '総件数', '総遅延時間']
    daily_stats['遅延率'] = daily_stats['遅延件数'] / daily_stats['総件数'] * 100
    
    # サブプロット作成
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=("日別 遅延発生件数の推移", "日別 遅延発生率の推移", "日別 総遅延時間"),
        vertical_spacing=0.08
    )
    
    # 1. 日別遅延件数
    fig.add_trace(
        go.Scatter(x=daily_stats.index, y=daily_stats['遅延件数'], 
                  mode='lines+markers', name='遅延件数', line=dict(color='blue')),
        row=1, col=1
    )
    
    # 2. 日別遅延率
    fig.add_trace(
        go.Scatter(x=daily_stats.index, y=daily_stats['遅延率'], 
                  mode='lines+markers', name='遅延率', line=dict(color='orange')),
        row=2, col=1
    )
    
    # 3. 日別総遅延時間
    fig.add_trace(
        go.Bar(x=daily_stats.index, y=daily_stats['総遅延時間'], 
               name='総遅延時間', marker_color='red', opacity=0.7),
        row=3, col=1
    )
    
    fig.update_layout(height=900, showlegend=False)
    fig.update_yaxes(title_text="遅延件数", row=1, col=1)
    fig.update_yaxes(title_text="遅延率（%）", row=2, col=1)
    fig.update_yaxes(title_text="総遅延時間（分）", row=3, col=1)
    fig.update_xaxes(title_text="日付", row=3, col=1)
    
    return fig

def display_summary_stats(df):
    """サマリー統計を表示"""
    total_records = len(df)
    delay_records = df['has_delay'].sum()
    delay_rate = delay_records / total_records * 100
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("総データ数", f"{total_records:,}件")
    
    with col2:
        st.metric("遅延発生件数", f"{delay_records:,}件")
    
    with col3:
        st.metric("遅延発生率", f"{delay_rate:.1f}%")
    
    with col4:
        if delay_records > 0:
            avg_delay = df[df['has_delay']]['delay_minutes'].mean()
            st.metric("平均遅延時間", f"{avg_delay:.1f}分")
        else:
            st.metric("平均遅延時間", "0分")

def display_insights(df):
    """データの洞察を表示"""
    st.subheader("🔍 データの洞察")
    
    # 曜日別分析
    weekday_stats = df.groupby('weekday_jp')['has_delay'].agg(['count', 'sum', 'mean'])
    weekday_stats['rate'] = (weekday_stats['mean'] * 100).round(1)
    
    worst_weekday = weekday_stats['rate'].idxmax()
    best_weekday = weekday_stats['rate'].idxmin()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**最も遅延が多い曜日**: {worst_weekday}曜日 ({weekday_stats.loc[worst_weekday, 'rate']:.1f}%)")
    
    with col2:
        st.success(f"**最も遅延が少ない曜日**: {best_weekday}曜日 ({weekday_stats.loc[best_weekday, 'rate']:.1f}%)")
    
    # 時間帯別分析
    if 'time_slot' in df.columns:
        time_stats = df.groupby('time_slot')['has_delay'].agg(['count', 'sum', 'mean'])
        time_stats['rate'] = (time_stats['mean'] * 100).round(1)
        
        worst_time = time_stats['rate'].idxmax()
        best_time = time_stats['rate'].idxmin()
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.warning(f"**最も遅延が多い時間帯**: {worst_time} ({time_stats.loc[worst_time, 'rate']:.1f}%)")
        
        with col4:
            st.success(f"**最も遅延が少ない時間帯**: {best_time} ({time_stats.loc[best_time, 'rate']:.1f}%)")

def main():
    """メインアプリケーション"""
    # ヘッダー
    st.markdown('<h1 class="main-header">🚆 山手線遅延分析ダッシュボード</h1>', unsafe_allow_html=True)
    
    # データ読み込み
    df = load_data()
    
    if df is None:
        st.error("データファイルが見つかりません。まずスクレイピングを実行してください。")
        st.code("python src/yamanote_scraper.py", language="bash")
        return
    
    # サイドバー
    st.sidebar.title("📊 分析オプション")
    
    # データ期間表示
    min_date = df['date'].min().strftime('%Y/%m/%d')
    max_date = df['date'].max().strftime('%Y/%m/%d')
    st.sidebar.info(f"**データ期間**: {min_date} ～ {max_date}")
    
    # 分析タイプ選択
    analysis_type = st.sidebar.selectbox(
        "分析タイプを選択",
        ["概要", "ヒートマップ", "時間帯別分析", "日別傾向", "データテーブル"]
    )
    
    # 日付範囲フィルタ
    date_range = st.sidebar.date_input(
        "日付範囲を選択",
        value=(df['date'].min().date(), df['date'].max().date()),
        min_value=df['date'].min().date(),
        max_value=df['date'].max().date()
    )
    
    # データフィルタリング
    if len(date_range) == 2:
        mask = (df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])
        filtered_df = df[mask]
    else:
        filtered_df = df
    
    # 分析結果表示
    if analysis_type == "概要":
        display_summary_stats(filtered_df)
        display_insights(filtered_df)
        
        # 最新の遅延情報
        st.subheader("📈 最新の遅延状況")
        latest_data = filtered_df.groupby('date')['has_delay'].sum().tail(7)
        
        fig = px.bar(
            x=latest_data.index,
            y=latest_data.values,
            title="直近7日間の遅延発生件数",
            labels={'x': '日付', 'y': '遅延件数'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    elif analysis_type == "ヒートマップ":
        st.subheader("📊 曜日別・時間帯別 遅延発生率")
        fig = create_weekday_heatmap(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
    elif analysis_type == "時間帯別分析":
        st.subheader("⏰ 時間帯別詳細分析")
        fig = create_time_analysis_charts(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
    elif analysis_type == "日別傾向":
        st.subheader("📅 日別遅延傾向")
        fig = create_daily_trend_chart(filtered_df)
        st.plotly_chart(fig, use_container_width=True)
        
    elif analysis_type == "データテーブル":
        st.subheader("📋 生データ")
        
        # 列選択
        columns = st.multiselect(
            "表示する列を選択",
            options=filtered_df.columns.tolist(),
            default=['date', 'time_slot', 'delay_info', 'delay_minutes', 'weekday_jp']
        )
        
        if columns:
            st.dataframe(filtered_df[columns], use_container_width=True)
        
        # CSVダウンロード
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="CSVダウンロード",
            data=csv,
            file_name=f"yamanote_delay_data_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    # フッター
    st.markdown("---")
    st.markdown("🚆 **山手線遅延分析ダッシュボード** | データ出典: JR東日本")

if __name__ == "__main__":
    main()