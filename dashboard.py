import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- TUS MÓDULOS ---
from strategies import RoiStrategy
from parsers import RevolutCSVParser
from portafolio import Portfolio

st.set_page_config(page_title="Mi Dashboard de Trading", layout="wide")

# --- FUNCIONES DE CARGA ---
def get_transactions(file_path):
    """Carga exclusivamente operaciones de venta (PnL)"""
    estrategia = RoiStrategy()
    parser = RevolutCSVParser()
    portfolio = Portfolio(strategy=estrategia)
    try:
        portfolio.load_data(parser, file_path)
        portfolio.analyze()
        return portfolio._transactions
    except Exception as e:
        return []

def transactions_to_df(transactions):
    data = []
    for t in transactions:
        data.append({
            "Fecha": t.date,
            "Activo": t.description,
            "Invertido": t.invested,
            "PnL ($)": t.profit_amount,
            "ROI (%)": t.roi_percentage,
            "Mes": t.date.strftime("%Y-%m")
        })
    return pd.DataFrame(data)

# --- MAIN APP ---
def main():
    st.title("📊 Monitor de Rendimiento (Realized PnL)")
    st.markdown("Analiza la rentabilidad de tus operaciones cerradas.")
    
    # 1. ZONA DE CARGA (Un solo archivo, limpio)
    uploaded_file = st.file_uploader("Sube tu archivo 'Profit & Loss' (CSV)", type=["csv"])

    if uploaded_file is None:
        st.info("☝️ Sube el archivo CSV de Revolut para ver tus estadísticas.")
        st.stop()

    # 2. PROCESAMIENTO
    temp_filename = "temp_pnl.csv"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.getbuffer())

    transactions = get_transactions(temp_filename)
    
    # Limpieza inmediata
    if os.path.exists(temp_filename):
        os.remove(temp_filename)
    
    if not transactions:
        st.error("No se encontraron operaciones de venta en el archivo. Asegúrate de subir el 'Profit & Loss'.")
        return

    df = transactions_to_df(transactions)

    # 3. DASHBOARD DE RENDIMIENTO
    
    # --- KPI GLOBALES ---
    st.markdown("---")
    
    total_invertido = df["Invertido"].sum() # Cost Basis de lo vendido
    total_pnl = df["PnL ($)"].sum()
    
    # ROI Operativo: (Ganancia / Coste de lo vendido)
    roi_global = (total_pnl / total_invertido * 100) if total_invertido != 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Operado (Cost Basis)", f"${total_invertido:,.2f}", help="Suma del dinero que costaron las acciones que has vendido.")
    col2.metric("Beneficio Neto Realizado", f"${total_pnl:,.2f}", delta_color="normal")
    col3.metric("ROI Operativo", f"{roi_global:.2f}%", help="Rentabilidad media ponderada de tus operaciones.")

    st.markdown("---")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📅 Visión Mensual", "🏢 Por Empresa", "📝 Datos Brutos"])

    with tab1:
        st.subheader("Evolución de Ganancias Realizadas")
        monthly_df = df.groupby("Mes")["PnL ($)"].sum().reset_index()
        
        if not monthly_df.empty:
            fig_month = px.bar(monthly_df, x="Mes", y="PnL ($)", color="PnL ($)",
                            color_continuous_scale=["red", "green"], text_auto='.2s')
            fig_month.update_traces(marker_line_width=1.5, opacity=0.8)
            st.plotly_chart(fig_month, use_container_width=True)
        else:
            st.warning("No hay datos suficientes para la vista mensual.")

    with tab2:
        st.subheader("Detalle por Activo")
        lista_empresas = sorted(df["Activo"].unique())
        empresa_selec = st.selectbox("Selecciona una empresa:", lista_empresas)
        
        # Filtros
        df_empresa = df[df["Activo"] == empresa_selec].sort_values("Fecha")
        
        # Preparar Gráfico Escalera (Step Chart)
        primera_fecha = df_empresa["Fecha"].iloc[0]
        start_row = pd.DataFrame([{
            "Fecha": primera_fecha, "Activo": empresa_selec, "Invertido": 0, 
            "PnL ($)": 0, "ROI (%)": 0, "PnL Acumulado": 0, "Mes": primera_fecha.strftime("%Y-%m")
        }])
        
        df_empresa["PnL Acumulado"] = df_empresa["PnL ($)"].cumsum()
        df_chart = pd.concat([start_row, df_empresa]).drop_duplicates(subset=["Fecha"], keep='last')

        # Métricas Detalladas
        t_inv_emp = df_empresa["Invertido"].sum()
        t_pnl_emp = df_empresa["PnL ($)"].sum()
        t_roi_emp = df_empresa["ROI (%)"].mean()
        n_ops_emp = len(df_empresa)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Invertido", f"${t_inv_emp:,.2f}")
        c2.metric("Ganancia Total", f"${t_pnl_emp:,.2f}", delta=f"{t_pnl_emp:,.2f}", delta_color="normal")
        c3.metric("ROI Promedio", f"{t_roi_emp:.2f}%")
        c4.metric("Operaciones", f"{n_ops_emp}")
        
        # Gráfico
        st.write(f"📈 **Curva de Beneficio con {empresa_selec}:**")
        fig_linea = px.line(df_chart, x="Fecha", y="PnL Acumulado", markers=True, 
                            line_shape='hv')
        
        fig_linea.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_linea.update_traces(line_color='#2ecc71' if t_pnl_emp >= 0 else '#e74c3c', 
                                line_width=3, fill='tozeroy')
        st.plotly_chart(fig_linea, use_container_width=True)
        
        # Tabla
        st.dataframe(df_empresa[["Fecha", "Invertido", "PnL ($)", "ROI (%)"]].style.format({
            "Invertido": "${:.2f}", "PnL ($)": "${:.2f}", "ROI (%)": "{:.2f}%"}))

    with tab3:
        st.subheader("Listado Completo de Operaciones")
        st.dataframe(df)

if __name__ == "__main__":
    main()