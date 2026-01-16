import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- TUS MÓDULOS ---
# Asegúrate de que existen: strategies.py, parsers.py, portfolio.py
from strategies import RoiStrategy
from parsers import RevolutCSVParser
from portafolio import Portfolio

# Configuración de la página (Debe ser la primera línea de Streamlit)
st.set_page_config(page_title="Mi Dashboard de Trading", layout="wide")

# --- FUNCIÓN DE CARGA ---
def get_transactions(file_source, is_demo=False):
    """Carga operaciones desde archivo subido o demo."""
    estrategia = RoiStrategy()
    parser = RevolutCSVParser()
    portfolio = Portfolio(strategy=estrategia)
    
    try:
        path_to_read = file_source
        
        # Si no es demo, guardamos el archivo subido temporalmente
        if not is_demo:
            path_to_read = "temp_pnl.csv"
            with open(path_to_read, "wb") as f:
                f.write(file_source.getbuffer())

        portfolio.load_data(parser, path_to_read)
        portfolio.analyze()
        
        # Limpieza del archivo temporal
        if not is_demo and os.path.exists("temp_pnl.csv"):
            os.remove("temp_pnl.csv")
            
        return portfolio._transactions
    except Exception as e:
        st.error(f"Error al procesar los datos: {e}")
        return []

def transactions_to_df(transactions):
    """Convierte la lista de transacciones en un DataFrame completo."""
    data = []
    for t in transactions:
        # Recuperamos datos extra del parser
        qty = getattr(t, 'quantity', 0)
        d_acquired = getattr(t, 'date_acquired', pd.NaT)
        
        # Calculamos el total recibido (Coste + Ganancia)
        venta_total = t.invested + t.profit_amount
        
        data.append({
            "Fecha": t.date,                # Fecha de Venta
            "Fecha Compra": d_acquired,     # Fecha de Adquisición
            "Activo": t.description,
            "Cant. Vendida": qty,
            "Venta Total ($)": venta_total,
            "Invertido": t.invested,
            "PnL ($)": t.profit_amount,
            "ROI (%)": t.roi_percentage,
            "Mes": t.date.strftime("%Y-%m")
        })
    return pd.DataFrame(data)

# --- MAIN APP ---
def main():
    st.title("📊 Monitor de Rendimiento (Realized PnL)")
    
    # --- BARRA LATERAL ---
    with st.sidebar:
        st.header("📂 Cargar Datos")
        uploaded_file = st.file_uploader("Sube tu CSV de Revolut", type=["csv"])
        
        st.markdown("--- O ---")
        
        # Botón de Demo
        use_demo = st.toggle("Usar datos de DEMO", value=False)
        if use_demo:
            st.info("👀 Viendo datos de ejemplo")



    

    # --- LÓGICA DE SELECCIÓN DE DATOS ---
    transactions = []

    if uploaded_file is not None:
        transactions = get_transactions(uploaded_file, is_demo=False)
    elif use_demo:
        if os.path.exists("demo.csv"):
            transactions = get_transactions("demo.csv", is_demo=True)
        else:
            st.error("⚠️ No encuentro 'demo.csv' en el repositorio.")
    else:
        st.info("👈 Sube tu archivo CSV o activa el Modo Demo.")
        st.markdown("""
        ### ¿Qué hace esta App?
        1. 📥 **Procesa** tu reporte de ganancias y pérdidas.
        2. 📈 **Calcula** tu ROI real por operación.
        3. 🏆 **Visualiza** qué empresas te dan más rentabilidad.
        """)
        st.stop() # Detiene la app aquí si no hay datos
        st.stop()

    if not transactions:
        st.warning("No se encontraron operaciones.")
        return

    # Crear DataFrame Principal
    df = transactions_to_df(transactions)

    # --- KPI GLOBALES ---
    st.markdown("---")
    total_invertido = df["Invertido"].sum()
    total_pnl = df["PnL ($)"].sum()
    roi_global = (total_pnl / total_invertido * 100) if total_invertido != 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Capital Total Movido", f"${total_invertido:,.2f}")
    c2.metric("Beneficio Neto", f"${total_pnl:,.2f}", delta_color="normal")
    c3.metric("ROI Total", f"{roi_global:.2f}%")
    st.markdown("---")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📅 Visión Mensual", "🏢 Por Empresa", "📝 Datos Brutos"])

    # TAB 1: GRÁFICO MENSUAL
    with tab1:
        st.subheader("Evolución de Ganancias por Mes")
        monthly_df = df.groupby("Mes")["PnL ($)"].sum().reset_index()
        fig_month = px.bar(monthly_df, x="Mes", y="PnL ($)", 
                           color="PnL ($)", color_continuous_scale=["red", "green"])
        st.plotly_chart(fig_month, use_container_width=True)

    # TAB 2: DETALLE POR EMPRESA
    with tab2:
        st.subheader("Análisis Detallado por Activo")
        lista = sorted(df["Activo"].unique())
        sel = st.selectbox("Selecciona empresa:", lista)
        
        df_empresa = df[df["Activo"] == sel].sort_values("Fecha")
        
        # --- AQUÍ ESTÁ LO QUE FALTABA: MÉTRICAS INDIVIDUALES ---
        t_inv_emp = df_empresa["Invertido"].sum()
        t_pnl_emp = df_empresa["PnL ($)"].sum()
        t_roi_emp = df_empresa["ROI (%)"].mean()
        n_ops_emp = len(df_empresa)
        
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Invertido", f"${t_inv_emp:,.2f}")
        k2.metric("Ganancia Total", f"${t_pnl_emp:,.2f}", delta_color="normal")
        k3.metric("ROI Promedio", f"{t_roi_emp:.2f}%")
        k4.metric("Operaciones", f"{n_ops_emp}")
        
        st.markdown("---") # Separador visual

        # --- LÓGICA GRÁFICA ---
        df_empresa["PnL Acumulado"] = df_empresa["PnL ($)"].cumsum()
        
        # Fecha inicio (Compra)
        fecha_primera_compra = df_empresa["Fecha Compra"].min()
        if pd.isna(fecha_primera_compra):
            fecha_primera_compra = df_empresa["Fecha"].iloc[0]

        # Fila de inicio (Punto 0)
        start_row = pd.DataFrame([{
            "Fecha": fecha_primera_compra, 
            "PnL Acumulado": 0
        }])
        
        df_chart = pd.concat([start_row, df_empresa], ignore_index=True).sort_values("Fecha")
        
        # Gráfico Lineal (Crecimiento progresivo)
        st.write(f"📈 **Curva de Beneficio: {sel}**")
        
        # CAMBIO AQUÍ: line_shape='linear' hace la diagonal en vez del escalón
        fig_l = px.line(df_chart, x="Fecha", y="PnL Acumulado", markers=True, line_shape='linear')
        
        fig_l.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_l.update_traces(line_color='#2ecc71' if t_pnl_emp >= 0 else '#e74c3c', fill='tozeroy')
        st.plotly_chart(fig_l, use_container_width=True)
        
        # Tabla
        st.write("📖 **Historial de Operaciones:**")
        st.dataframe(
            # Asegúrate de que la función transactions_to_df genera "Cant. Vendida"
            df_empresa[["Fecha", "Fecha Compra", "Cant. Vendida", "Venta Total ($)", "Invertido", "PnL ($)", "ROI (%)"]]
            .style.format({
                "Fecha": "{:%Y-%m-%d}",
                "Fecha Compra": "{:%Y-%m-%d}",
                "Cant. Vendida": "{:.4f}",  
                "Venta Total ($)": "${:,.2f}",
                "Invertido": "${:,.2f}",
                "PnL ($)": "${:,.2f}",
                "ROI (%)": "{:.2f}%"
            })
            .applymap(lambda x: 'color: #e74c3c' if x < 0 else 'color: #2ecc71', subset=['PnL ($)', 'ROI (%)']),
            use_container_width=True
        )
    # TAB 3: DATA FRAME COMPLETO
    with tab3:
        st.dataframe(df)

if __name__ == "__main__":
    main()
