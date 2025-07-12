import streamlit as st
import re
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Contador de Puntos", page_icon="🎯")
st.title("🎯 Contador de Puntos por Colegio")

# Definición de colegios y sus equipos
colegios = {
    "Warriors": ["🤍", "💙", "🖤", "💚"],
    "Ilvermorny": ["❤️", "💛", "💚", "💙", "🖤"]
}

# Equivalencias de emojis alternativos
equivalencias_personalizadas = {
    "♥️": "❤️",
    "💜": "🖤"
}

# Etiquetas personalizadas por emoji por colegio
etiquetas_por_colegio = {
    "Warriors": {
        "🤍": "blancos",
        "💙": "azules",
        "🖤": "negros",
        "💚": "verdes"
    },
    "Ilvermorny": {
        "❤️": "wampus",
        "💛": "pukukis",
        "💚": "serpientes",
        "💙": "thinder",
        "🖤": "directoras"
    }
}

# Colores personalizados por etiqueta
tema_colores = {
    "blancos": "#cccccc",
    "azules": "#3399ff",
    "negros": "#222222",
    "verdes": "#33cc33",
    "wampus": "#ff4d4d",
    "pukukis": "#ffcc00",
    "serpientes": "#00cc66",
    "thinder": "#3399ff",
    "directoras": "#9900cc"
}

# Selector de colegio
colegio_seleccionado = st.selectbox("Selecciona el colegio:", list(colegios.keys()))
equipos_validos = set(colegios[colegio_seleccionado])
etiquetas_equipo = etiquetas_por_colegio[colegio_seleccionado]

# Inputs del usuario
texto = st.text_area("Pega aquí el historial de mensajes:", height=400)
desglosado = st.checkbox("¿Mostrar información desglosada por día?", value=True)
calcular = st.button("Calcular puntos")

if texto and calcular:
    puntos_por_fecha = defaultdict(lambda: defaultdict(int))
    fecha_actual = "Sin fecha"

    def normaliza(emoji):
        return equivalencias_personalizadas.get(emoji, emoji)

    anio_actual = datetime.now().year
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea:
            continue

        # Extraer fecha de formato tipo [hh:mm, dd/mm/yyyy] o [dd/mm, hh:mm]
        match_fecha = re.match(r"\[(\d{1,2}/\d{1,2}),\s*(\d{1,2}:\d{2})\]", linea)
        if match_fecha:
            dia_mes, hora = match_fecha.groups()
            fecha_actual = f"{dia_mes}/{anio_actual}"
        else:
            match_fecha_alt = re.match(r"\[(\d{1,2}:\d{2}),\s*(\d{1,2}/\d{1,2}/\d{4})\]", linea)
            if match_fecha_alt:
                _, fecha_actual = match_fecha_alt.groups()

        match = re.search(r"(\d+)\s+puntos\s+a\s+([^\s]+)", linea)
        if match:
            cantidad, emoji = match.groups()
            emoji = normaliza(emoji)
            if emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad)
            continue

        match = re.search(r"([^\s]+)\s+([\d,.]+)\s+puntos", linea)
        if match:
            emoji, cantidad = match.groups()
            emoji = normaliza(emoji)
            cantidad = cantidad.replace(".", "").replace(",", "")
            if cantidad.isdigit() and emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad)
            continue

        match = re.match(r"^([^\d\s]+)\s*([\d]+[.,]?[\d]*)$", linea)
        if match:
            emoji, cantidad = match.groups()
            emoji = normaliza(emoji)
            cantidad = cantidad.replace(".", "").replace(",", "")
            if cantidad.isdigit() and emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad)

    filas = []
    for fecha, equipos in sorted(puntos_por_fecha.items()):
        for emoji in equipos:
            puntos = equipos[emoji]
            if puntos > 0:
                filas.append({"Fecha": fecha, "Equipo": emoji, "Puntos": puntos})

    df = pd.DataFrame(filas).sort_values(by=["Fecha", "Equipo"]).reset_index(drop=True)

    st.success("¡Conteo completado!")

    if desglosado:
        st.subheader("📅 Detalle por Fecha")
        df_formatted = df.copy()
        df_formatted["Puntos"] = df_formatted["Puntos"].apply(lambda x: f"{x:,}")
        st.dataframe(df_formatted)
        st.download_button("Descargar CSV por fecha", df.to_csv(index=False).encode(), "puntos_por_fecha.csv")

        st.subheader("📈 Evolución de Puntos por Día")
        df_grafico = df.pivot_table(index="Fecha", columns="Equipo", values="Puntos", aggfunc="sum", fill_value=0)
        df_grafico = df_grafico.rename(columns=etiquetas_equipo)
        df_grafico = df_grafico.sort_index()

        fig, ax = plt.subplots(figsize=(10, 5))
        for columna in df_grafico.columns:
            df_grafico[columna].plot(ax=ax, marker="o", label=columna, color=tema_colores.get(columna))

        ax.set_ylabel("Puntos")
        ax.set_xlabel("Fecha")
        ax.set_title("Puntos por Equipo a lo Largo del Tiempo")
        ax.grid(True)
        ax.legend(title="Equipo")
        st.pyplot(fig)

    resumen = df.groupby("Equipo")["Puntos"].sum().reset_index().sort_values(by="Puntos", ascending=False)
    resumen_str = "\n".join([f"{row['Equipo']}: {row['Puntos']:,} puntos" for _, row in resumen.iterrows()])

    st.subheader("🏆 Total por Equipo")
    resumen_format = resumen.copy()
    resumen_format["Equipo"] = resumen_format["Equipo"].apply(lambda e: f"{e} ({etiquetas_equipo.get(e, e)})")
    resumen_format["Puntos"] = resumen_format["Puntos"].apply(lambda x: f"{x:,}")
    st.dataframe(resumen_format)
    st.download_button("Descargar CSV resumen", resumen.to_csv(index=False).encode(), "resumen_puntos.csv")

    st.subheader("📋 Resultado total (para copiar)")
    st.code(resumen_str, language="markdown")
