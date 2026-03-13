import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime
import plotly.graph_objects as go
from collections import defaultdict

st.set_page_config(page_title="F.C. de Quinta", layout="wide")

st.markdown("""
<style>

div.stButton > button {
    width: 100%;
    height: 70px;
    font-size: 22px;
    font-weight: bold;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# ESTILO VISUAL
# -----------------------------

st.markdown("""
<style>

body {
background-color: #0e1117;
}

h1, h2, h3 {
text-align:center;
}

div.stButton > button {
width:100%;
height:70px;
font-size:22px;
font-weight:bold;
border-radius:12px;
}

</style>
""", unsafe_allow_html=True)

st.title("⚽ F.C. de Quinta")

conn = sqlite3.connect("fc_quinta.db", check_same_thread=False)
cursor = conn.cursor()

# -----------------------------
# TABELAS
# -----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS jogadores (
id INTEGER PRIMARY KEY AUTOINCREMENT,
nome TEXT,
numero INTEGER,
tipo TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS partidas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
data TEXT,
gols_amarelo INTEGER,
gols_cinza INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS eventos (
id INTEGER PRIMARY KEY AUTOINCREMENT,
partida_id INTEGER,
tempo TEXT,
time TEXT,
tipo TEXT,
jogador TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS estatisticas (
jogador TEXT PRIMARY KEY,
gols INTEGER,
assistencias INTEGER,
vitorias INTEGER
)
""")

conn.commit()

menu = st.sidebar.selectbox(
"Menu",
[
"Registrar jogo",
"Jogadores",
"Histórico de partidas",
"Estatísticas"
]
)

# -----------------------------
# JOGADORES
# -----------------------------

if menu == "Jogadores":

    st.header("Cadastro de jogadores")

    nome = st.text_input("Nome")
    numero = st.number_input("Número",0,99)
    tipo = st.selectbox("Tipo",["Fixo","Convidado"])

    if st.button("Adicionar jogador"):

        cursor.execute(
        "INSERT INTO jogadores (nome,numero,tipo) VALUES (?,?,?)",
        (nome,numero,tipo)
        )

        conn.commit()

        st.success("Jogador cadastrado")

    jogadores = pd.read_sql("SELECT * FROM jogadores",conn)
    st.dataframe(jogadores)

# -----------------------------
# HISTÓRICO
# -----------------------------

if menu == "Histórico de partidas":

    st.header("Histórico de jogos")

    partidas = pd.read_sql("SELECT * FROM partidas ORDER BY id DESC",conn)

    if len(partidas)==0:
        st.info("Nenhuma partida registrada")
    else:
        st.dataframe(partidas)

    if st.button("🗑 Limpar histórico de partidas"):

        cursor.execute("DELETE FROM eventos")
        cursor.execute("DELETE FROM partidas")

        conn.commit()

        st.success("Histórico apagado")

# -----------------------------
# ESTATÍSTICAS
# -----------------------------

if menu == "Estatísticas":

    st.header("📊 Estatísticas dos jogadores")

    stats = pd.read_sql("SELECT * FROM estatisticas ORDER BY gols DESC",conn)

    if len(stats)==0:
        st.info("Nenhuma estatística registrada")
    else:
        st.dataframe(stats)

    if st.button("🗑 Limpar estatísticas"):

        cursor.execute("DELETE FROM estatisticas")
        conn.commit()

        st.success("Estatísticas apagadas")

# -----------------------------
# REGISTRAR JOGO
# -----------------------------

if menu == "Registrar jogo":

    jogadores = pd.read_sql("SELECT * FROM jogadores", conn)
    lista = jogadores["numero"].dropna().astype(int).tolist()

    if "inicio" not in st.session_state:
        st.session_state.inicio=None

    if "eventos" not in st.session_state:
        st.session_state.eventos=[]

    if "etapa" not in st.session_state:
        st.session_state.etapa="evento"

    if "tempo_gol" not in st.session_state:
        st.session_state.tempo_gol=None

    if st.session_state.inicio is None:

        col1,col2 = st.columns(2)

        with col1:
            time_amarelo = st.multiselect("🟡 Time Amarelo",lista)

        with col2:
            time_cinza = st.multiselect("⚪ Time Cinza",lista)

        if st.button("▶ Iniciar jogo"):

            st.session_state.time_amarelo=time_amarelo
            st.session_state.time_cinza=time_cinza
            st.session_state.inicio=time.time()

            st.rerun()

    if st.session_state.inicio:

        tempo=int(time.time()-st.session_state.inicio)

        minutos=tempo//60
        segundos=tempo%60

        tempo_evento=f"{minutos:02d}:{segundos:02d}"

        gols_amarelo=sum(
        1 for e in st.session_state.eventos
        if e["tipo"]=="gol" and e["time"]=="Amarelo"
        )

        gols_cinza=sum(
        1 for e in st.session_state.eventos
        if e["tipo"]=="gol" and e["time"]=="Cinza"
        )

        # PLACAR GRANDE

        st.markdown(
        f"""
        <div style='text-align:center;
        font-size:60px;
        font-weight:bold'>
        🟡 {gols_amarelo}  x  {gols_cinza} ⚪
        </div>
        """,
        unsafe_allow_html=True
        )

        # TEMPO

        st.markdown(
        f"""
        <div style='text-align:center;
        font-size:40px'>
        ⏱ {tempo_evento}
        </div>
        """,
        unsafe_allow_html=True
        )

        col1,col2,col3 = st.columns(3)

        if col1.button("⚽ Gol"):
            st.session_state.tipo="gol"
            st.session_state.etapa="time"

        if col2.button("🛡 Roubo"):
            st.session_state.tipo="roubo"
            st.session_state.etapa="time"

        if col3.button("🧤 Defesa"):
            st.session_state.tipo="defesa"
            st.session_state.etapa="time"

        # RESTANTE DO CÓDIGO CONTINUA IGUAL

        st.subheader("📋 Súmula")

        sumula=pd.DataFrame(st.session_state.eventos)
        st.dataframe(sumula)

        csv = sumula.to_csv(index=False).encode()

        st.download_button(
        "📥 Baixar Súmula",
        csv,
        "sumula_partida.csv",
        "text/csv"
        )

        if st.button("🏁 Encerrar partida"):

            data=datetime.now().strftime("%d/%m/%Y")

            cursor.execute(
            "INSERT INTO partidas (data,gols_amarelo,gols_cinza) VALUES (?,?,?)",
            (data,gols_amarelo,gols_cinza)
            )

            conn.commit()

            st.success("Partida salva no histórico")

            st.session_state.inicio=None
            st.session_state.eventos=[]