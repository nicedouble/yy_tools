#!/usr/bin/env python
# _*_coding:utf-8_*_

"""
@Time     : 2021/5/31 16:17
@Author   : ji hao ran
@File     : tidy_price.py
@Project  : yy_tools
@Software : PyCharm
"""
import base64
import time
import streamlit as st
import pandas as pd
import numpy as np
import io

# app 全局设置
st.set_page_config(
    page_title="My love",
    page_icon=":heart:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def download_as_excel(df, sheet, filename: str = 'download'):
    """下载dataframe为csv"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        for i in range(len(df)):
            df[i].to_excel(writer, sheet_name=sheet[i], index=False)
    buffer.seek(0)
    b64 = base64.b64encode(buffer.read()).decode()
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">下载Excel</a>'


@st.cache
def tidy_price(file):
    # read excel
    df = pd.read_excel(file)
    # select columns
    df = df.iloc[:, [0, 6, 8, 7]]
    df.columns = ['id', 'fixed', 'active', 'shop']
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    df.iloc[:, 1:] = np.ceil(df.iloc[:, 1:])
    # group and agg
    agg_df = df.groupby('id').agg(['min', 'std'])
    agg_df.columns = ['fixed_min', 'fixed_std', 'active_min', 'active_std', 'shop_min', 'shop_std']
    # group
    df1 = agg_df.loc[agg_df[['fixed_std', 'active_std', 'shop_std']].apply(lambda x: all(x.isnull()), axis=1)]
    df2 = agg_df.loc[agg_df[['fixed_std', 'active_std', 'shop_std']].apply(lambda x: all(x == 0), axis=1)]
    df3 = agg_df.loc[agg_df[['fixed_std', 'active_std', 'shop_std']].apply(lambda x: any(x > 0), axis=1)]

    # output
    def select(d):
        d = d[['fixed_min', 'active_min', 'shop_min']].sort_values('fixed_min').reset_index()
        d.columns = ['商品ID', '一口价(单位元)', '活动价(单位元)', '专柜价(单位元)']
        return d

    return select(df1), select(df2), select(df3)


# css
st.markdown("""
<style>
[data-testid="Styled(div)"] {
    text-align: center;
}
button.css-1g71wml.edgvbvh1 {
    width: 100%;
}
</style>
""", unsafe_allow_html=True)
# sidebar layout
st.sidebar.success("""
    ## 操作指南  
    **第一步** 上传Excel表    
    **第二步** 点击计算按钮  
""")
file = st.sidebar.file_uploader('上传Excel')
st.sidebar.write('')
b = st.sidebar.button('计算')
# main layout
if b:
    if file is not None:
        my_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.01)
            my_bar.progress(i + 1)
        st.markdown('## 计算结果')
        c1, c2, c3 = st.beta_columns(3)
        d1, d2, d3 = tidy_price(file)
        with c1:
            st.markdown('### **表1：只有一个商品ID**')
            st.write(d1)
            st.write(f'总共有{d1.shape[0]}行')

        with c2:
            st.markdown('### **表2：有多个商品ID，价格相同**')
            st.write(d2)
            st.write(f'总共有{d2.shape[0]}行')

        with c3:
            st.markdown('### **表3：有多个商品ID，价格不同**')
            st.write(d3)
            st.write(f'总共有{d3.shape[0]}行')

        st.markdown(download_as_excel([d1, d2, d3], ['只有一个商品ID', '多个商品ID价格相同', '多个商品ID价格不同'],
                                      filename=f'{pd.Timestamp.now().date()}价格表'), unsafe_allow_html=True)
        st.write('')
        st.info("""
        备注：  
        1. 选取目标列[商品ID, 一口价(单位元), 专柜价(单位元), 活动价(单位元)]  
        2. 价格向上取整  
        3. 按商品ID列分组聚合  
        4. 根据价格方差对结果分类  
        5. 每个表根据一口价升序排序  
        """)
        st.balloons()
    else:
        st.warning('请先上传表格，再点击计算按钮！')
