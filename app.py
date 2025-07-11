import streamlit as st
import re
from collections import defaultdict
import pandas as pd

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

# Selector de colegio
colegio_seleccionado = st.selectbox("Selecciona el colegio:", list(colegios.keys()))
equipos_validos = set(colegios[colegio_seleccionado])

# Inputs del usuario
texto = st.text_area("Pega aquí el historial de mensajes:", height=400)
desglosado = st.checkbox("¿Mostrar información desglosada por día?", value=True)

if texto:
    puntos_por_fecha = defaultdict(lambda: defaultdict(int))
    fecha_actual = "Sin fecha"

    # Normalizar emojis si hay equivalencias
    def normaliza(emoji):
        return equivalencias_personalizadas.get(emoji, emoji)

    for linea in texto.splitlines():
        match_fecha = re.match(r"\[\d{1,2}:\d{2},\s*(\d{1,2}/\d{1,2}/\d{4})\]", linea)
        if match_fecha:
            fecha_actual = match_fecha.group(1)
            continue

        for cantidad, emoji in re.findall(r"(\d+)\s+puntos\s+a\s+([^\s]+)", linea):
            emoji = normaliza(emoji)
            if emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad)

        for emoji, cantidad in re.findall(r"([^\s]+)\s+([\d,]+)\s+puntos", linea):
            emoji = normaliza(emoji)
            if emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad.replace(",", ""))

        for emoji, cantidad in re.findall(r"([^\s]+)[\s]*([\d]+\.[\d]+)", linea):
            emoji = normaliza(emoji)
            if emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad.replace(".", ""))

        for emoji, cantidad in re.findall(r"([^\s]+)\s+0*(\d+)$", linea):
            emoji = normaliza(emoji)
            if emoji in equipos_validos:
                puntos_por_fecha[fecha_actual][emoji] += int(cantidad)

    # Construcción de resultados por fecha
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
        st.dataframe(df)
        st.download_button("Descargar CSV por fecha", df.to_csv(index=False).encode(), "puntos_por_fecha.csv")

    resumen = df.groupby("Equipo")["Puntos"].sum().reset_index().sort_values(by="Puntos", ascending=False)
    resumen_str = "\n".join([f"{row['Equipo']}: {row['Puntos']} puntos" for _, row in resumen.iterrows()])

    st.subheader("🏆 Total por Equipo")
    st.dataframe(resumen)
    st.download_button("Descargar CSV resumen", resumen.to_csv(index=False).encode(), "resumen_puntos.csv")

    st.text_area("📋 Resultado total (para copiar):", value=resumen_str, height=150)
    st.button("Copiar total", on_click=lambda: st.session_state.update({"copiado": True}))
