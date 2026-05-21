# ============================================================
# PROJETO: FRAUD ANALYTICS PIPELINE
# ============================================================

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

def carregar_query(nome_arquivo):
    caminho = f"queries/{nome_arquivo}"

    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()
    
# ============================================================
# 1. CONFIGURAÇÃO DO PROJETO
# ============================================================

ARQUIVO_TREINO = "dados/fraudTrain.csv"
ARQUIVO_TESTE = "dados/fraudTest.csv"

os.makedirs("graficos", exist_ok=True)


# ============================================================
# 2. LEITURA DOS DADOS
# ============================================================

df_train = pd.read_csv(ARQUIVO_TREINO)
df_test = pd.read_csv(ARQUIVO_TESTE)


# ============================================================
# 3. EXPLORAÇÃO INICIAL
# ============================================================

# print(df_train.head())
# print(df_train.info())
# print(df_test.head())
# print(df_test.info())


# ============================================================
# 4. LIMPEZA INICIAL
# ============================================================

df_train = df_train.drop(columns=["Unnamed: 0"])
df_test = df_test.drop(columns=["Unnamed: 0"])

df_train["trans_date_trans_time"] = pd.to_datetime(df_train["trans_date_trans_time"])
df_test["trans_date_trans_time"] = pd.to_datetime(df_test["trans_date_trans_time"])

df_train["dob"] = pd.to_datetime(df_train["dob"])
df_test["dob"] = pd.to_datetime(df_test["dob"])

conexao = sqlite3.connect("fraud_analytics.db")

df_train.to_sql(
    "transactions",
    conexao,
    if_exists="replace",
    index=False
)

# ============================================================
# 5. LEITURA DAS QUERIES SQL
# ============================================================

query_fraud_rate = carregar_query(
    "fraud_rate.sql"
)

query_fraude_categoria = carregar_query(
    "fraude_categoria.sql"
)

query_fraude_hora = carregar_query(
    "fraude_hora.sql"
)

query_fraude_periodo = carregar_query(
    "fraude_periodo.sql"
)

fraud_rate_sql = pd.read_sql_query(
    query_fraud_rate,
    conexao
)

fraude_categoria_sql = pd.read_sql_query(
    query_fraude_categoria,
    conexao
)

fraude_hora_sql = pd.read_sql_query(
    query_fraude_hora,
    conexao
)

fraude_periodo_sql = pd.read_sql_query(
    query_fraude_periodo,
    conexao
)

# ============================================================
# 6. FEATURE ENGINEERING
# ============================================================

df_train["hora_transacao"] = df_train["trans_date_trans_time"].dt.hour

# ============================================================
# CLASSIFICAÇÃO DE PERÍODO DO DIA
# ============================================================

def classificar_periodo(hora):

    if 0 <= hora < 6:
        return "Madrugada"

    elif 6 <= hora < 12:
        return "Manhã"

    elif 12 <= hora < 18:
        return "Tarde"

    else:
        return "Noite"

df_train["periodo_dia"] = df_train["hora_transacao"].apply(
    classificar_periodo
)

# ============================================================
# 7. ANÁLISES DE FRAUDE
# ============================================================

distribuicao_fraude = df_train["is_fraud"].value_counts()

percentual_fraude = df_train["is_fraud"].value_counts(normalize=True) * 100

fraude_categoria = (
    df_train
    .groupby("category")["is_fraud"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

valor_medio = (
    df_train
    .groupby("is_fraud")["amt"]
    .mean()
    .reset_index()
)

valor_medio["tipo_transacao"] = valor_medio["is_fraud"].map(
    {
        0: "Transação Normal",
        1: "Transação Fraudulenta"
    }
)

fraude_por_hora = (
    df_train
    .groupby("hora_transacao")["is_fraud"]
    .mean()
    .reset_index()
)

fraude_estado = (
    df_train
    .groupby("state")
    .agg(
        total_transacoes=("is_fraud", "count"),
        taxa_fraude=("is_fraud", "mean")
    )
    .reset_index()
)

fraude_estado = (
    fraude_estado[fraude_estado["total_transacoes"] > 1000]
    .sort_values(by="taxa_fraude", ascending=False)
)

top_estados = fraude_estado.head(10)

fraude_merchant = (
    df_train
    .groupby("merchant")
    .agg(
        total_transacoes=("is_fraud", "count"),
        taxa_fraude=("is_fraud", "mean")
    )
    .reset_index()
)

fraude_merchant = fraude_merchant[
    fraude_merchant["total_transacoes"] > 100
]

fraude_merchant = fraude_merchant.sort_values(
    by="taxa_fraude",
    ascending=False
)

top_merchant = fraude_merchant.head(10)

fraude_categoria_periodo = (
    df_train
    .groupby(
        ["periodo_dia", "category"]
    )["is_fraud"]
    .mean()
    .reset_index()
)

madrugada = fraude_categoria_periodo[
    fraude_categoria_periodo["periodo_dia"] == "Madrugada"
]

# ============================================================
# 8. VISUALIZAÇÕES
# ============================================================

# ------------------------------------------------------------
# GRÁFICO: TAXA DE FRAUDE POR CATEGORIA
# ------------------------------------------------------------

plt.figure(figsize=(12, 6))

barras = plt.bar(
    fraude_categoria["category"],
    fraude_categoria["is_fraud"]
)

plt.title("Taxa de Fraude por Categoria", fontsize=16)
plt.xlabel("Categoria", fontsize=12)
plt.ylabel("Taxa de Fraude (%)", fontsize=12)
plt.xticks(rotation=45)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.1%}")
)

for barra in barras:
    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 0.0003,
        f"{altura:.2%}",
        ha="center",
        fontsize=9
    )

plt.tight_layout()

plt.savefig(
    "graficos/fraude_por_categoria.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# GRÁFICO: VALOR MÉDIO POR TIPO DE TRANSAÇÃO
# ------------------------------------------------------------

plt.figure(figsize=(8, 6))

barras = plt.bar(
    valor_medio["tipo_transacao"],
    valor_medio["amt"]
)

plt.title("Valor Médio por Tipo de Transação", fontsize=16)
plt.xlabel("Tipo de Transação", fontsize=12)
plt.ylabel("Valor Médio (USD)", fontsize=12)

for barra in barras:
    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 10,
        f"${altura:.2f}",
        ha="center",
        fontsize=10
    )

plt.tight_layout()

plt.savefig(
    "graficos/valor_medio_fraude.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# GRÁFICO: TAXA DE FRAUDE POR HORA
# ------------------------------------------------------------

plt.figure(figsize=(12, 6))

plt.plot(
    fraude_por_hora["hora_transacao"],
    fraude_por_hora["is_fraud"],
    marker="o"
)

plt.title("Taxa de Fraude por Hora", fontsize=16)
plt.xlabel("Hora do Dia", fontsize=12)
plt.ylabel("Taxa de Fraude (%)", fontsize=12)

plt.xticks(range(0, 24))

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.2%}")
)

plt.grid(
    linestyle="--",
    alpha=0.5
)

plt.tight_layout()

plt.savefig(
    "graficos/fraude_por_hora.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# GRÁFICO: TAXA DE FRAUDE POR ESTADO
# ------------------------------------------------------------

plt.figure(figsize=(14, 6))

barras = plt.bar(
    fraude_estado["state"],
    fraude_estado["taxa_fraude"]
)

plt.title("Taxa de Fraude por Estado", fontsize=16)
plt.xlabel("Estado", fontsize=12)
plt.ylabel("Taxa de Fraude (%)", fontsize=12)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda y, _: f"{y:.2%}")
)

for barra in barras:
    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 0.0001,
        f"{altura:.2%}",
        ha="center",
        fontsize=7,
        rotation=90
    )

plt.grid(
    linestyle="--",
    alpha=0.5
)

plt.tight_layout()

plt.savefig(
    "graficos/fraude_por_estado.png",
    dpi=300
)

plt.close()

# ------------------------------------------------------------
# GRÁFICO: TAXA DE FRAUDE POR MERCHANT
# ------------------------------------------------------------

plt.figure(figsize=(14, 6))

barras = plt.bar(
    top_merchant["merchant"],
    top_merchant["taxa_fraude"]
)

plt.title(
    "Top 10 Merchants com Maior Taxa de Fraude",
    fontsize=16
)

plt.xlabel(
    "Merchant",
    fontsize=12
)

plt.ylabel(
    "Taxa de Fraude (%)",
    fontsize=12
)

plt.xticks(rotation=75)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda y, _: f"{y:.2%}"
    )
)

for barra in barras:

    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 0.0005,
        f"{altura:.2%}",
        ha="center",
        fontsize=8
    )

plt.grid(
    linestyle="--",
    alpha=0.5
)

plt.tight_layout()

plt.savefig(
    "graficos/top_merchant_fraude.png",
    dpi=300
)

plt.close()


# ------------------------------------------------------------
# GRÁFICO: TAXA DE FRAUDE POR CATEGORIA - MADRUGADA
# ------------------------------------------------------------

plt.figure(figsize=(12, 6))

barras = plt.bar(
    madrugada["category"],
    madrugada["is_fraud"]
)

plt.title(
    "Taxa de Fraude por Categoria - Madrugada",
    fontsize=16
)

plt.xlabel(
    "Categoria",
    fontsize=12
)

plt.ylabel(
    "Taxa de Fraude (%)",
    fontsize=12
)

plt.xticks(rotation=45)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(
        lambda y, _: f"{y:.2%}"
    )
)

for barra in barras:

    altura = barra.get_height()

    plt.text(
        barra.get_x() + barra.get_width() / 2,
        altura + 0.0005,
        f"{altura:.2%}",
        ha="center",
        fontsize=8
    )

plt.grid(
    linestyle="--",
    alpha=0.5
)

plt.tight_layout()

plt.savefig(
    "graficos/fraude_categoria_madrugada.png",
    dpi=300
)

plt.close()


# ============================================================
# 9. INSIGHTS AUTOMÁTICOS
# ============================================================

taxa_media_geral = df_train["is_fraud"].mean()

hora_mais_risco = fraude_por_hora.sort_values(
    by="is_fraud",
    ascending=False
).iloc[0]

categoria_mais_risco = fraude_categoria.iloc[0]

insight_1 = (
    f"A maior taxa de fraude por hora ocorreu às "
    f"{hora_mais_risco['hora_transacao']}h, "
    f"com taxa de {hora_mais_risco['is_fraud']:.2%}."
)

insight_2 = (
    f"A categoria com maior taxa de fraude foi "
    f"{categoria_mais_risco['category']}, "
    f"com taxa de {categoria_mais_risco['is_fraud']:.2%}."
)

print(insight_1)
print(insight_2)

# ============================================================
# 10. VALIDAÇÃO FINAL
# ============================================================

df_train.to_csv(
    "dados/fraud_transactions_clean.csv",
    index=False,
    encoding="utf-8"
)

colunas_dashboard = [
    "trans_date_trans_time",
    "category",
    "amt",
    "gender",
    "state",
    "merchant",
    "is_fraud",
    "hora_transacao",
    "periodo_dia"
]

dashboard_df = df_train[colunas_dashboard]

print("Pipeline executado com sucesso.")