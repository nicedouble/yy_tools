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
    #     df = df.iloc[:, [0, 6, 8, 7]]
    df = df[['商品ID', '一口价(单位元)', '活动价(单位元)']]
    df.columns = ['id', 'fixed', 'active']
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    df.iloc[:, 1:] = np.ceil(df.iloc[:, 1:])
    # group and agg
    agg_df = df.groupby('id').agg(['min', 'std'])
    agg_df.columns = ['fixed_min', 'fixed_std', 'active_min', 'active_std']
    # group
    df1 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: all(x.isnull()), axis=1)]
    df2 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: all(x == 0), axis=1)]
    df3 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: any(x > 0), axis=1)]

    # output
    def select(d):
        d = d[['fixed_min', 'active_min']].sort_values('fixed_min').reset_index()
        d.columns = ['商品ID', '一口价(单位元)', '活动价(单位元)']
        return d

    return select(df1), select(df2), select(df3)


# sidebar layout
menu = st.sidebar.radio('功能', ['鹿班打标', '价格检测'])

st.sidebar.success("""
    ## 操作指南  
    **第一步** 上传Excel表    
    **第二步** 点击计算按钮  
""")

if menu == '鹿班打标':
    file = st.file_uploader('上传Excel')
    st.write('津贴设置')
    st.number_input('每满', min_value=0)
    b = st.button('计算')
    # main layout
    if b:
        if file is not None:
            st.markdown('## 计算结果')
            c1, c2, c3 = st.columns(3)
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
            st.info("""
            备注：  
            1. 选取目标列[商品ID, 一口价(单位元), 活动价(单位元)]  
            2. 价格向上取整  
            3. 按商品ID列分组聚合  
            4. 根据价格方差对结果分类  
            5. 每个表根据一口价升序排序  
            """)
            st.balloons()
        else:
            st.warning('请先上传表格，再点击计算按钮！')
if menu == '价格检测':
    c = st.columns(2)
    with c[0]:
        file1 = st.file_uploader('原始价格Excel')
    with c[1]:
        file2 = st.file_uploader('现在价格Excel')
    b = st.button('计算')
    table = st.columns(3)
    if b:
        if file1 is not None and file2 is not None:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            df1.drop_duplicates(inplace=True)
            df2.drop_duplicates(inplace=True)
            # 连接
            df = df1.merge(df2, how='outer')
            df['价差'] = df['现在价格'] - df['原始价格']
            ids = df['外部ID'].value_counts()  # id列联表

            # 多商品ID
            m_ids = ids[ids > 1]
            if not m_ids.empty:
                # 筛选多个外部ID
                m_df = df[df['外部ID'].isin(m_ids.index)]
                # 筛选价差大于100
                m_df = m_df[m_df['价差'] > 100]
                # 分组价差均值
                agg = m_df.groupby('外部ID')['价差'].agg(['mean']).sort_values('mean', ascending=False).reset_index()
                # 合并
                m_df = agg.merge(m_df).rename(columns={'mean': '价差均值'})
                # 列排序
                m_df = m_df[['外部ID', '原始价格', '现在价格', '价差', '价差均值']].reset_index(drop=True)
                with table[0]:
                    st.markdown('### **表1：多商品ID**')
                    st.write(m_df)
            else:
                m_df = pd.DataFrame()
                st.info('无多商品ID情形')

            # 单商品ID
            s_ids = ids[ids == 1]
            if not s_ids.empty:
                s_df = df[df['外部ID'].isin(s_ids.index)]
                # 筛选价差大于100
                s_df = s_df[s_df['价差'] > 100]
                # 排序
                s_df = s_df.sort_values(by='价差', ascending=False).reset_index(drop=True)
                with table[1]:
                    st.markdown('### **表2：单商品ID**')
                    st.write(s_df)
            else:
                s_df = pd.DataFrame()
                st.info('无单商品ID情形')

            # 未上架 (外部ID原始价格无，现在价格有)
            no_df = df[df['原始价格'].isna() & ~df['现在价格'].isna()]
            if not no_df.empty:
                no_df = no_df.sort_values(by='现在价格').reset_index(drop=True)
                with table[2]:
                    st.markdown('### **表3：未上架**')
                    st.write(no_df)
            else:
                st.info('无未上架情形')

            st.markdown(download_as_excel([m_df, s_df, no_df], ['多商品ID', '单商品ID', '未上架'],
                                          filename=f'{pd.Timestamp.now().date()}价格检测'), unsafe_allow_html=True)
            st.balloons()
        else:
            st.warning('请先上传表格，再点击计算按钮！')
