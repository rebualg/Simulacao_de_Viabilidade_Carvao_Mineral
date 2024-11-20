# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF  # Biblioteca para criar PDFs

# Critérios configuráveis para avaliação
CRITERIA = {
    "PCS (kcal/kg)": {"green_min": 5800, "yellow_min": 5700, "red_max": 5700},
    "PCI (kcal/kg)": {"green_min": 5700, "yellow_min": 5600, "red_max": 5600},
    "% Cinzas": {"green_max": 9, "yellow_max": 10, "red_min": 10},
    "% Umidade": {"green_max": 16, "yellow_max": 17, "red_min": 17},
    "% Enxofre": {"green_max": 0.55, "yellow_max": 0.69, "red_min": 0.7},
}

COST_TABLE = {
    0.61: 4.97,
    0.62: 5.01,
    0.63: 5.05,
    0.64: 5.14,
    0.65: 5.24,
    0.66: 5.33,
    0.67: 5.39,
    0.68: 5.45,
    0.69: 5.45,
}

# Função para avaliar os parâmetros do carvão
def evaluate_coal(data):
    def evaluate(row):
        reasons = []
        status = "Verde"
        additional_cost = None

        if row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCS fora do limite permitido")
        elif row["PCS (kcal/kg)"] < CRITERIA["PCS (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons.append("PCS abaixo do ideal")

        if row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["red_max"]:
            status = "Vermelho"
            reasons.append("PCI fora do limite permitido")
        elif row["PCI (kcal/kg)"] < CRITERIA["PCI (kcal/kg)"]["green_min"]:
            if status == "Verde":
                status = "Amarelo"
            reasons.append("PCI abaixo do ideal")

        if row["% Cinzas"] > CRITERIA["% Cinzas"]["red_min"]:
            status = "Vermelho"
            reasons.append("Cinzas fora do limite permitido")
        elif row["% Cinzas"] > CRITERIA["% Cinzas"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons.append("Cinzas acima do ideal")

        if row["% Umidade"] > CRITERIA["% Umidade"]["red_min"]:
            status = "Vermelho"
            reasons.append("Umidade fora do limite permitido")
        elif row["% Umidade"] > CRITERIA["% Umidade"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons.append("Umidade acima do ideal")

        if row["% Enxofre"] > CRITERIA["% Enxofre"]["red_min"]:
            status = "Vermelho"
            reasons.append("Enxofre fora do limite permitido")
        elif row["% Enxofre"] > CRITERIA["% Enxofre"]["green_max"]:
            if status == "Verde":
                status = "Amarelo"
            reasons.append("Enxofre acima do ideal")
            rounded_sulfur = round(row["% Enxofre"], 2)
            if rounded_sulfur in COST_TABLE:
                additional_cost = COST_TABLE[rounded_sulfur]

        return (
            status,
            "; ".join(reasons) if reasons else "Todos os parâmetros estão dentro dos limites ideais.",
            additional_cost,
        )

    df = pd.DataFrame(data, index=[0])
    df["Viabilidade"], df["Justificativa"], df["Custo Adicional (USD/t)"] = zip(
        *df.apply(evaluate, axis=1)
    )
    return df

# Função para exibir o gráfico
def show_graph(df):
    color_map = {"Verde": "green", "Amarelo": "yellow", "Vermelho": "red"}
    df["Cor"] = df["Viabilidade"].map(color_map)

    plt.figure(figsize=(10, 6))
    for viability, color in color_map.items():
        subset = df[df["Viabilidade"] == viability]
        plt.scatter(
            subset["PCS (kcal/kg)"],
            subset["% Cinzas"],
            label=viability,
            color=color,
            s=100,
            edgecolor="black",
        )

    plt.title("Avaliacao de Viabilidade do Carvao Mineral", fontsize=14)
    plt.xlabel("PCS (kcal/kg)", fontsize=12)
    plt.ylabel("% Cinzas", fontsize=12)
    plt.axhline(
        y=CRITERIA["% Cinzas"]["green_max"],
        color="black",
        linestyle="--",
        label="Limite de Cinzas",
    )
    plt.axvline(
        x=CRITERIA["PCS (kcal/kg)"]["green_min"],
        color="blue",
        linestyle="--",
        label="Limite de PCS",
    )
    plt.legend(title="Viabilidade")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.tight_layout()

    # Salva o gráfico como imagem em bytes
    buf = BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

# Função para criar o PDF
def create_pdf(data, df, graph_image):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Relatório de Viabilidade do Carvão Mineral", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, txt=f"PCS (kcal/kg): {data['PCS (kcal/kg)']}", ln=True)
    pdf.cell(0, 10, txt=f"PCI (kcal/kg): {data['PCI (kcal/kg)']}", ln=True)
    pdf.cell(0, 10, txt=f"% Cinzas: {data['% Cinzas']}", ln=True)
    pdf.cell(0, 10, txt=f"% Umidade: {data['% Umidade']}", ln=True)
    pdf.cell(0, 10, txt=f"% Enxofre: {data['% Enxofre']}", ln=True)
    pdf.ln(10)

    pdf.cell(0, 10, txt=f"Resultado: {df['Viabilidade'][0]}", ln=True)
    pdf.cell(0, 10, txt=f"Justificativa: {df['Justificativa'][0]}", ln=True)

    if df["Custo Adicional (USD/t)"].iloc[0]:
        pdf.cell(0, 10, txt=f"Custo Adicional: {df['Custo Adicional (USD/t)'][0]:.2f} USD/t", ln=True)

    pdf.ln(10)
    pdf.image(graph_image, x=50, y=None, w=100)

    return pdf.output(dest="S").encode("latin1")

# Função principal da aplicação
st.title("Simulacao de Viabilidade do Carvao Mineral")
pcs = st.number_input("PCS (kcal/kg)", min_value=0, step=100)
pci = st.number_input("PCI (kcal/kg)", min_value=0, step=100)
cinzas = st.number_input("% Cinzas", min_value=0.0, max_value=100.0, step=0.1)
umidade = st.number_input("% Umidade", min_value=0.0, max_value=100.0, step=0.1)
enxofre = st.number_input("% Enxofre", min_value=0.0, max_value=10.0, step=0.01)

if st.button("Rodar Simulacao"):
    data = {
        "PCS (kcal/kg)": pcs,
        "PCI (kcal/kg)": pci,
        "% Cinzas": cinzas,
        "% Umidade": umidade,
        "% Enxofre": enxofre,
    }
    df = evaluate_coal(data)
    st.write(f"**Resultado:** {df['Viabilidade'][0]}")
    st.write(f"**Justificativa:** {df['Justificativa'][0]}")
    if df["Custo Adicional (USD/t)"].iloc[0]:
        st.write(f"**Custo Adicional devido ao enxofre:** {df['Custo Adicional (USD/t)'][0]:.2f} USD/t")

   
