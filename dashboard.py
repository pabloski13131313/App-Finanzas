import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- TUS MÓDULOS ---
from strategies import RoiStrategy
from parsers import RevolutCSVParser
from portafolio import Portfolio

st.set_page_config(page_title="Mi Dashboard de Trading", layout="wide")

# --- FUNCIÓN DE CARGA ---
def get_transactions(file_source, is_demo=False):
    """Carga operaciones. file_source puede ser un archivo subido o una ruta string"""
    estrategia = RoiStrategy()
    parser = RevolutCSVParser()
    portfolio = Portfolio(strategy=estrategia)
    
    try:
        # Si es DEMO, file_source es un string ("demo_data.csv")
        # Si es UPLOAD, file_source es un buffer y hay que guardarlo temporalmente
        path_to_read = file_source
        
        if not is_demo:
            path_to_read = "temp_pnl.csv"
            with open(path_to_read, "wb") as f:
                f.write(file_source.getbuffer())

        portfolio.load_data(parser, path_to_read)
        portfolio.analyze()
        
        # Limpieza solo si creamos el temporal
        if not is_demo and os.path.exists("temp_pnl.csv"):
            os.remove("temp_pnl.csv")
            
        return portfolio._transactions
    except Exception as e:
        st.error(f"Error al leer datos: {e}")
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
    
    # --- BARRA LATERAL (SIDEBAR) PARA CARGA DE DATOS ---
    with st.sidebar:
        st.header("📂 Cargar Datos")
        uploaded_file = st.file_uploader("Sube tu CSV de Revolut", type=["csv"])
        
        st.markdown("--- O ---")
        
        # BOTÓN DE DEMO
        use_demo = st.toggle("Usar datos de DEMO", value=False)
        
        if use_demo:
            st.info("👀 Viendo datos de ejemplo (Tesla, Apple, Nvidia...)")

    # --- LÓGICA DE SELECCIÓN ---
    transactions = []

    if uploaded_file is not None:
        # Prioridad 1: El usuario sube su archivo
        transactions = get_transactions(uploaded_file, is_demo=False)
    elif use_demo:
        # Prioridad 2: El usuario activa el modo Demo
        # Asegúrate de que demo_data.csv está en GitHub
        if os.path.exists("demo.csv"):
            transactions = get_transactions("demo.csv", is_demo=True)
        else:
            st.error("⚠️ No encuentro el archivo 'demo.csv' en el repositorio.")
    else:
        # Estado inicial: Pantalla de bienvenida
        st.info("👈 Sube tu archivo CSV en el menú lateral o activa el **Modo Demo** para probar la App.")
        
        # Un poco de marketing visual para cuando entran
        st.markdown("""
        ### ¿Qué hace esta App?
        1. 📥 Procesa tu 'Profit & Loss' de Revolut.
        2. 📈 Calcula tu ROI real por operación.
        3. 🏆 Te muestra qué empresas te dan más dinero.
        """)
        st.stop()

    if not transactions:
        st.warning("No se encontraron operaciones.")
        return

    df = transactions_to_df(transactions)

    # --- DASHBOARD (El resto sigue igual que siempre) ---
    
    # KPI GLOBALES
    st.markdown("---")
    total_invertido = df["Invertido"].sum()
    total_pnl = df["PnL ($)"].sum()
    roi_global = (total_pnl / total_invertido * 100) if total_invertido != 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Capital Operado", f"${total_invertido:,.2f}")
    col2.metric("Beneficio Neto", f"${total_pnl:,.2f}", delta_color="normal")
    col3.metric("ROI Operativo", f"{roi_global:.2f}%")
    st.markdown("---")

    # PESTAÑAS
    tab1, tab2, tab3 = st.tabs(["📅 Visión Mensual", "🏢 Por Empresa", "📝 Datos Brutos"])

    with tab1:
        st.subheader("Evolución de Ganancias")
        monthly_df = df.groupby("Mes")["PnL ($)"].sum().reset_index()
        fig_month = px.bar(monthly_df, x="Mes", y="PnL ($)", color="PnL ($)",
                            color_continuous_scale=["red", "green"], text_auto='.2s')
        st.plotly_chart(fig_month, use_container_width=True)

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
        st.dataframe(df)

if __name__ == "__main__":
    main()

