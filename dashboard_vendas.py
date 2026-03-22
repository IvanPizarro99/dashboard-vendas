import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard de Vendas", layout="wide")

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_numero(valor, casas=3):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dividir_seguro(a, b):
    return a / b if b != 0 else 0

@st.cache_data(ttl=3600)
def carregar_dados(arquivo=None):
    if arquivo:
        df = pd.read_csv(arquivo, sep=';', decimal=',', encoding='utf-8')
    else:
        df = pd.read_csv('relatorioABCVenda.csv', sep=';', decimal=',', encoding='utf-8')

    df.columns = df.columns.str.strip()

    df['Quebra'] = pd.to_datetime(df['Quebra'], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Quebra'])

    df = df.sort_values('Quebra')

    return df

arquivo = st.sidebar.file_uploader("📂 Enviar CSV", type=["csv"])

try:
    df = carregar_dados(arquivo)

    st.markdown("## 📊 Dashboard de Faturamento")

    min_data = df['Quebra'].min().date()
    max_data = df['Quebra'].max().date()

    col_top1, col_top2 = st.columns(2)

    with col_top1:
        data_inicio = st.date_input("Data inicial", min_data)

    with col_top2:
        data_fim = st.date_input("Data final", max_data)

    st.markdown(f"### 📅 Período: {data_inicio.strftime('%d/%m/%Y')} até {data_fim.strftime('%d/%m/%Y')}")

    st.sidebar.header("🔎 Filtros")

    busca_produto = st.sidebar.text_input("🔍 Buscar produto")

    if busca_produto:
        df = df[df['Descrição'].str.contains(busca_produto, case=False)]

    df_periodo = df[
        (df['Quebra'].dt.date >= data_inicio) &
        (df['Quebra'].dt.date <= data_fim)
    ].copy()

    faturamento = df_periodo['Faturamento'].sum()
    quantidade = df_periodo['Quantidade'].sum()
    ticket = dividir_seguro(faturamento, quantidade)

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Faturamento", formatar_moeda(faturamento))
    col2.metric("📦 Quantidade", formatar_numero(quantidade))
    col3.metric("🎯 Ticket Médio", formatar_moeda(ticket))

    st.markdown("---")

    st.subheader("📈 Evolução do faturamento")

    evolucao = df_periodo.groupby('Quebra')['Faturamento'].sum().reset_index()

    fig = px.line(evolucao, x='Quebra', y='Faturamento', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📅 Dias com maior faturamento")

    top_dias = df_periodo.groupby(df_periodo['Quebra'].dt.date)['Faturamento'].sum().reset_index()
    top_dias.columns = ['Data', 'Faturamento']

    top_dias = top_dias.sort_values(by='Faturamento', ascending=False).head(10)
    top_dias = top_dias.sort_values(by='Data')

    top_dias['Data'] = pd.to_datetime(top_dias['Data']).dt.strftime('%d/%m/%Y')

    fig_dias = px.bar(
        top_dias,
        x='Data',
        y='Faturamento',
        text='Faturamento',
        color='Faturamento',
        color_continuous_scale='Blues'
    )

    fig_dias.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
    fig_dias.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig_dias, use_container_width=True)

    st.subheader("📊 Faturamento por dia da semana")

    dias_ordem = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]

    mapa_dias = {
        "Sunday": "Domingo",
        "Monday": "Segunda",
        "Tuesday": "Terça",
        "Wednesday": "Quarta",
        "Thursday": "Quinta",
        "Friday": "Sexta",
        "Saturday": "Sábado"
    }

    df_periodo['Dia'] = df_periodo['Quebra'].dt.day_name()

    semana = df_periodo.groupby('Dia')['Faturamento'].sum().reindex(dias_ordem).reset_index()
    semana['Dia'] = semana['Dia'].map(mapa_dias)

    fig_semana = px.bar(
        semana,
        x='Dia',
        y='Faturamento',
        text='Faturamento',
        color='Faturamento',
        color_continuous_scale='Blues'
    )

    fig_semana.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')

    st.plotly_chart(fig_semana, use_container_width=True)

    st.subheader("🏆 Produtos que mais faturaram")

    top_n = st.sidebar.slider("Top N produtos", 5, 50, 10)

    top_prod = df_periodo.groupby('Descrição')['Faturamento'] \
        .sum().sort_values(ascending=False).head(top_n).reset_index()

    fig_prod = px.bar(
        top_prod,
        x='Faturamento',
        y='Descrição',
        orientation='h',
        color='Faturamento'
    )

    fig_prod.update_layout(yaxis={'categoryorder': 'total ascending'})

    st.plotly_chart(fig_prod, use_container_width=True)

    st.markdown("---")
    st.subheader("🔍 Detalhamento por dia")

    datas = df_periodo['Quebra'].dt.date.unique()
    data_sel = st.selectbox("Selecione uma data", datas)

    df_dia = df_periodo[df_periodo['Quebra'].dt.date == data_sel]

    if not df_dia.empty:
        st.write(
            f"**Faturamento:** {formatar_moeda(df_dia['Faturamento'].sum())} | "
            f"**Quantidade:** {formatar_numero(df_dia['Quantidade'].sum())}"
        )

        st.dataframe(
            df_dia[['Código', 'Descrição', 'Quantidade', 'Faturamento']]
            .sort_values('Faturamento', ascending=False),
            use_container_width=True,
            hide_index=True
        )

except FileNotFoundError:
    st.error("Arquivo 'relatorioABCVenda.csv' não encontrado.")
except Exception as e:
    st.error(f"Erro: {e}")