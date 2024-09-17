import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import japanize_matplotlib  # 日本語フォント対応
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import io
import pandas as pd

# タイトル
st.title('棒グラフに個々のデータをプロットするアプリ')

# セッションステートの初期化
if 'data' not in st.session_state:
    st.session_state.data = None
if 'group_column' not in st.session_state:
    st.session_state.group_column = None
if 'data_columns' not in st.session_state:
    st.session_state.data_columns = []

# サイドバーに設定を配置
with st.sidebar:
    st.header('データアップロード')
    
    # CSVファイルのアップロード
    uploaded_file = st.file_uploader("CSVファイルをアップロードしてください", type="csv")

    if uploaded_file is not None:
        # CSVファイルをデータフレームとして読み込み
        st.session_state.data = pd.read_csv(uploaded_file)
        
        # グループ名とデータ列を選択
        group_columns = st.session_state.data.columns.tolist()
        st.session_state.group_column = st.selectbox("グループ名の列を選択してください", 
                                                     group_columns + [None], 
                                                     index=group_columns.index(st.session_state.group_column) if st.session_state.group_column in group_columns else len(group_columns))
        
        st.session_state.data_columns = st.multiselect("データ列を選択してください", 
                                                      group_columns, 
                                                      default=st.session_state.data_columns if st.session_state.data_columns else [])

    st.header('グラフ設定')

    # グラフタイトル
    graph_title = st.text_input('グラフのタイトル', 'グループごとの平均値と個々のデータ')

    # 横軸と縦軸のラベル
    x_label = st.text_input('横軸のラベル', 'グループ')
    y_label = st.text_input('縦軸のラベル', '値')

    # ラベルフォントサイズ
    label_x_font_size = st.slider('横軸のラベルフォントサイズ', min_value=8, max_value=24, value=16)
    label_y_font_size = st.slider('縦軸のラベルフォントサイズ', min_value=8, max_value=24, value=16)

    # 数値フォントサイズ
    tick_x_font_size = st.slider('横軸のグループ名フォントサイズ', min_value=8, max_value=24, value=16)
    tick_y_font_size = st.slider('縦軸の数値フォントサイズ', min_value=8, max_value=24, value=16)

    # エラーバーの線の太さ
    errorbar_linewidth = st.slider('エラーバーの線の太さ', min_value=0.5, max_value=5.0, value=1.0)

    # 棒グラフの幅
    bar_width = st.slider('棒グラフの幅', min_value=0.1, max_value=1.0, value=0.5)

    # 縦軸の設定
    auto_ylim = st.checkbox('縦軸の最大値を自動設定する', value=True)
    
    if auto_ylim:
        y_min = None
        y_max = None
    else:
        y_min = st.number_input('縦軸の最小値', value=0.0, format="%.1f")
        y_max = st.number_input('縦軸の最大値', value=100.0, format="%.1f")
    
    y_ticks = st.number_input('目盛りの間隔', min_value=0.1, value=5.0, format="%.1f")

    # ジッターの範囲
    jitter_range = st.slider('プロットのジッター範囲', min_value=0.0, max_value=0.5, value=0.2)

    # プロットの大きさ
    scatter_size = st.slider('プロットの大きさ', min_value=10, max_value=200, value=50)

    # 縦横比
    aspect_ratio = st.slider('グラフの縦横比 (高さ / 幅)', min_value=0.5, max_value=2.0, value=1.0)

    # 縦横軸の線の太さと棒グラフの境界線の太さ
    axis_linewidth = st.slider('縦軸と横軸の線の太さ', min_value=0.5, max_value=5.0, value=1.0)
    bar_edgewidth = st.slider('棒グラフの境界線の太さ', min_value=0.5, max_value=5.0, value=1.0)

    # グラフの左右の余白（棒グラフと縦軸との距離）
    x_margin = st.slider('グラフの左右の余白（棒グラフと縦軸との距離）', min_value=0.0, max_value=1.0, value=0.2)

    # プロット表示設定
    show_scatter = st.checkbox('個々のデータを表示する', value=True)
    show_error_bars = st.checkbox('標準偏差を表示する', value=True)
    show_std_err = st.checkbox('標準誤差を表示する', value=False)

# メイン画面にグラフを配置
st.header('グラフ表示')

# データが存在する場合にのみアップロードされたデータを表示
if st.session_state.data is not None:
    st.write('アップロードされたデータ')
    st.write(st.session_state.data)  # 縦にすべて表示
    
    # グループ名とデータ列が選択されているか確認
    if st.session_state.group_column is not None and st.session_state.data_columns:
        # データが存在する場合にグラフを描画
        data = {}
        colors = {}
        
        for group_name in st.session_state.data[st.session_state.group_column].unique():
            group_data = st.session_state.data[st.session_state.data[st.session_state.group_column] == group_name][st.session_state.data_columns].values.flatten()
            if len(group_data) > 0:
                data[group_name] = group_data
                colors[group_name] = ('#ADD8E6', '#000000')  # デフォルトの色

        # 平均値と標準偏差の計算
        means = [np.mean(data[group]) for group in data]
        std_devs = [np.std(data[group]) for group in data]
        std_errs = [np.std(data[group]) / np.sqrt(len(data[group])) for group in data]
        group_names = list(data.keys())

        # グラフ作成
        fig, ax = plt.subplots(figsize=(8 * aspect_ratio, 6))

        # 棒グラフの位置
        x = np.arange(len(group_names))
        
        # 棒グラフをプロット
        bars = ax.bar(x, means, 
                      width=bar_width, 
                      color=[colors[group][0] for group in data], 
                      edgecolor='black', linewidth=bar_edgewidth, align='center')

        # 個々のデータをジッターでプロット（表示が選択された場合）
        if show_scatter:
            for i, group in enumerate(data):
                jitter = np.random.uniform(-jitter_range, jitter_range, len(data[group]))
                ax.scatter(np.full(len(data[group]), x[i]) + jitter, data[group],
                           color=colors[group][1], s=scatter_size, edgecolor='black')

        # 標準偏差または標準誤差を表示
        if show_error_bars or show_std_err:
            ax.errorbar(x, means, 
                        yerr=std_devs if show_error_bars else std_errs,
                        fmt='none', ecolor='black', elinewidth=errorbar_linewidth)

        # タイトルとラベル
        ax.set_title(graph_title, fontsize=20)
        ax.set_xlabel(x_label, fontsize=label_x_font_size)
        ax.set_ylabel(y_label, fontsize=label_y_font_size)

        # 横軸にグループ名を表示
        ax.set_xticks(x)
        ax.set_xticklabels(group_names, fontsize=tick_x_font_size, ha='center')

        # 縦軸の目盛り設定
        ax.yaxis.set_tick_params(labelsize=tick_y_font_size)
        ax.yaxis.set_major_locator(MultipleLocator(y_ticks))
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.1f'))

        # 縦軸の設定（手動設定が適用されるように修正）
        if not auto_ylim:
            ax.set_ylim([y_min, y_max])

        # 左右の余白設定
        ax.margins(x=x_margin)

        # 縦横軸の線の太さ
        ax.spines['top'].set_linewidth(axis_linewidth)
        ax.spines['right'].set_linewidth(axis_linewidth)
        ax.spines['bottom'].set_linewidth(axis_linewidth)
        ax.spines['left'].set_linewidth(axis_linewidth)

        # グラフを一時ファイルに保存
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plt.close(fig)

        # グラフを表示
        st.pyplot(fig)

        # グラフのダウンロードリンク
        st.download_button(label="グラフをダウンロード",
                           data=buffer,
                           file_name="graph.png",
                           mime="image/png")

    else:
        st.write("グループ名の列とデータ列を選択してください")
else:
    st.write("データがアップロードされていません")
