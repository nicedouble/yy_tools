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
    page_title="I Love YangYang",
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
    data = 'data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64'
    return f'<a href="{data},{b64}" download="{filename}.xlsx">Download as xlsx</a>'


def tidy_price(file):
    # read excel
    df = pd.read_excel(file)
    # 选择列
    df = df[['商品ID', '一口价(单位元)', '活动价(单位元)']]
    # 重命名
    df.columns = ['id', 'fixed', 'active']
    # 类型转换
    df.iloc[:, 0] = df.iloc[:, 0].astype(str)
    # df.iloc[:, 1:] = np.ceil(df.iloc[:, 1:])
    # 按id分组计算最小值，方差
    agg_df = df.groupby('id').agg(['min', 'std'])
    agg_df.columns = ['fixed_min', 'fixed_std', 'active_min', 'active_std']
    # 分为3个表
    df1 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: all(x.isnull()), axis=1)]
    df2 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: all(x == 0), axis=1)]
    df3 = agg_df.loc[agg_df[['fixed_std', 'active_std']].apply(lambda x: any(x > 0), axis=1)]

    # output
    def select(d):
        # 活动价取整
        d['active_int'] = d['active_min'].apply(lambda x: np.ceil(x))
        # 津贴列
        if st.session_state['u']:
            d['jin_tie'] = d['active_min'].apply(lambda x: jin_tie(x, st.session_state['m'], st.session_state['n']))
        else:
            d['jin_tie'] = 0
        # 优惠券列
        man_jian = []
        for i in range(1, 5):
            if st.session_state[f'u{i}']:
                man_jian.append([st.session_state[f'm{i}'], st.session_state[f'n{i}']])
        if len(man_jian) > 0:
            d['yhq'] = d['active_min'].apply(lambda x: you_hui_quan(x, *man_jian))
        else:
            d['yhq'] = 0
        # 到手价
        d['dao_shou'] = d[['active_min', 'jin_tie', 'yhq']].apply(lambda x: np.ceil(x[0] - x[1] - x[2]), axis=1)
        # 选择列
        d = d[['fixed_min', 'active_min', 'active_int', 'jin_tie', 'yhq', 'dao_shou']].sort_values(
            'fixed_min').reset_index()
        d.columns = ['商品ID', '一口价', '活动价', '活动价取整', '津贴', '优惠券', '到手价']
        return d

    return select(df1), select(df2), select(df3)


def jin_tie(huo_dong_jia, mei_man, jian):
    #  计算津贴 每满**减**
    return int(huo_dong_jia / mei_man) * jian


def you_hui_quan(huo_dong_jia, *man_jian):
    # 计算优惠券 满**减** 多个叠加
    r = []
    for i in man_jian:
        man, jian = i[0], i[1]
        if huo_dong_jia >= man:
            r.append(jian)
    return sum(r)


# sidebar layout
menu = st.sidebar.radio('功能', ['鹿班打标', '价格检测'])

if menu == '鹿班打标':
    file = st.file_uploader('上传Excel')
    col = st.columns(5)
    with col[0].expander('津贴 😀', True):
        st.checkbox('启用', True, key='u')
        st.number_input('每满', key='m', min_value=0, value=1400,
                        disabled=False if st.session_state['u'] else True)
        st.number_input('减', key='n', min_value=0, value=100, disabled=False if st.session_state['u'] else True)
    with col[1].expander('优惠券1', True):
        st.checkbox('启用', True, key='u1')
        st.number_input('满', min_value=0, value=1499, key='m1',
                        disabled=False if st.session_state['u1'] else True)
        st.number_input('减', min_value=0, value=50, key='n1',
                        disabled=False if st.session_state['u1'] else True)
    with col[2].expander('优惠券2', True):
        st.checkbox('启用', key='u2')
        st.number_input('满', min_value=0, value=1499, key='m2',
                        disabled=False if st.session_state['u2'] else True)
        st.number_input('减', min_value=0, value=50, key='n2',
                        disabled=False if st.session_state['u2'] else True)
    with col[3].expander('优惠券3', True):
        st.checkbox('启用', key='u3')
        st.number_input('满', min_value=0, value=1499, key='m3',
                        disabled=False if st.session_state['u3'] else True)
        st.number_input('减', min_value=0, value=50, key='n3',
                        disabled=False if st.session_state['u3'] else True)
    with col[4].expander('优惠券4', True):
        st.checkbox('启用', key='u4')
        st.number_input('满', min_value=0, value=1499, key='m4',
                        disabled=False if st.session_state['u4'] else True)
        st.number_input('减', min_value=0, value=50, key='n4',
                        disabled=False if st.session_state['u4'] else True)

    b = st.button('计算')
    # main layout
    if b:
        if file is not None:
            with st.spinner('计算中...'):
                d1, d2, d3 = tidy_price(file)
            tabs = st.tabs(['只有一个商品ID', '有多个商品ID,价格相同', '有多个商品ID,价格不同'])
            with tabs[0]:
                st.dataframe(d1, use_container_width=True)
            with tabs[1]:
                st.dataframe(d2, use_container_width=True)
            with tabs[2]:
                st.dataframe(d3, use_container_width=True)

            st.markdown(download_as_excel([d1, d2, d3], ['只有一个商品ID', '多个商品ID价格相同', '多个商品ID价格不同'],
                                          filename=f'{pd.Timestamp.now().date()}价格表'), unsafe_allow_html=True)
            st.info("""
            备注：  
            1. 选取目标列[商品ID, 一口价(单位元), 活动价(单位元)]  
            2. 到手价=向上取整（活动价-津贴-优惠券）  
            3. 按商品ID列分组计算价格最小值和方差
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
