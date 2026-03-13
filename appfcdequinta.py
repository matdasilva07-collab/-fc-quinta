import streamlit as st
import sqlite3
import pandas as pd
import time

st.set_page_config(layout="wide")

# -------------------------
# BANCO DE DADOS
# -------------------------

conn = sqlite3.connect("fc_quinta.db", check_same_thread=False)
cursor = conn.cursor()

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

conn.commit()

# -------------------------
# MENU
# -------------------------

menu = st.sidebar.selectbox(
    "Menu",
    ["Registrar jogo","Jogadores","Estatísticas"]
)

# -------------------------
# JOGADORES
# -------------------------

if menu == "Jogadores":

    st.title("👥 Cadastro de jogadores")

    nome = st.text_input("Nome")
    numero = st.number_input("Número da camisa",0,99)
    tipo = st.selectbox("Tipo",["Fixo","Convidado"])

    if st.button("Adicionar jogador"):

        cursor.execute(
        "INSERT INTO jogadores (nome,numero,tipo) VALUES (?,?,?)",
        (nome,numero,tipo)
        )

        conn.commit()
        st.success("Jogador cadastrado")

    jogadores = pd.read_sql("SELECT * FROM jogadores",conn)

    st.subheader("Lista de jogadores")
    st.dataframe(jogadores)

# -------------------------
# REGISTRAR JOGO
# -------------------------

if menu == "Registrar jogo":

    st.title("⚽ Registrar partida")

    if "inicio" not in st.session_state:
        st.session_state.inicio = None

    if "eventos" not in st.session_state:
        st.session_state.eventos = []

    jogadores = pd.read_sql("SELECT * FROM jogadores",conn)

    lista = jogadores["numero"].tolist()

    col1,col2 = st.columns(2)

    with col1:
        time_amarelo = st.multiselect("Time Amarelo",lista)

    with col2:
        time_cinza = st.multiselect("Time Cinza",lista)

    if st.button("Iniciar jogo"):

        st.session_state.inicio = time.time()
        st.session_state.eventos = []

    if st.session_state.inicio:

        tempo=int(time.time()-st.session_state.inicio)

        minutos=tempo//60
        segundos=tempo%60

        tempo_evento=f"{minutos:02d}:{segundos:02d}"

        gols_amarelo=sum(1 for e in st.session_state.eventos if e["tipo"]=="gol" and e["time"]=="Amarelo")
        gols_cinza=sum(1 for e in st.session_state.eventos if e["tipo"]=="gol" and e["time"]=="Cinza")

        st.header(f"🟡 {gols_amarelo} x {gols_cinza} ⚪")
        st.write(f"⏱ {tempo_evento}")

        evento = st.selectbox(
            "Evento",
            ["Gol","Assistência","Roubo","Defesa"]
        )

        time = st.selectbox("Time",["Amarelo","Cinza"])

        if evento != "Defesa":

            jogador = st.selectbox("Jogador",lista)

        if st.button("Registrar evento"):

            if evento == "Defesa":

                st.session_state.eventos.append({
                    "tempo":tempo_evento,
                    "tipo":"defesa",
                    "time":time,
                    "jogador":f"Goleiro {time}"
                })

            else:

                st.session_state.eventos.append({
                    "tempo":tempo_evento,
                    "tipo":evento.lower(),
                    "time":time,
                    "jogador":jogador
                })

        st.subheader("Eventos")

        st.write(st.session_state.eventos)

        if st.button("Encerrar jogo"):

            cursor.execute(
            "INSERT INTO partidas (data,gols_amarelo,gols_cinza) VALUES (date('now'),?,?)",
            (gols_amarelo,gols_cinza)
            )

            partida_id = cursor.lastrowid

            for e in st.session_state.eventos:

                cursor.execute(
                "INSERT INTO eventos (partida_id,tempo,time,tipo,jogador) VALUES (?,?,?,?,?)",
                (partida_id,e["tempo"],e["time"],e["tipo"],str(e["jogador"]))
                )

            conn.commit()

            st.success("Partida salva!")

            st.session_state.inicio = None

# -------------------------
# ESTATÍSTICAS
# -------------------------

if menu == "Estatísticas":

    st.title("📊 Estatísticas da temporada")

    eventos = pd.read_sql("SELECT * FROM eventos",conn)

    if len(eventos) == 0:
        st.write("Sem dados ainda")
    else:

        gols = eventos[eventos["tipo"]=="gol"]
        assist = eventos[eventos["tipo"]=="assistência"]
        roubos = eventos[eventos["tipo"]=="roubo"]
        defesas = eventos[eventos["tipo"]=="defesa"]

        ranking = {}

        for j in eventos["jogador"]:

            ranking.setdefault(j,{
                "gols":0,
                "assist":0,
                "roubo":0,
                "defesa":0
            })

        for j in gols["jogador"]:
            ranking[j]["gols"] += 1

        for j in assist["jogador"]:
            ranking[j]["assist"] += 1

        for j in roubos["jogador"]:
            ranking[j]["roubo"] += 1

        for j in defesas["jogador"]:
            ranking[j]["defesa"] += 1

        tabela=[]

        for j,d in ranking.items():

            pontos=d["gols"]*3+d["assist"]*2+d["roubo"]+d["defesa"]

            tabela.append({
                "Jogador":j,
                "Gols":d["gols"],
                "Assist":d["assist"],
                "Roubo":d["roubo"],
                "Defesas":d["defesa"],
                "Pontos":pontos
            })

        df=pd.DataFrame(tabela).sort_values("Pontos",ascending=False)

        st.dataframe(df)