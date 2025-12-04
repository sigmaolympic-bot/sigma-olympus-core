import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
from scipy.stats import poisson

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SIGMA | OLYMPUS v18.4", layout="wide", page_icon="🛡️")
st.markdown("""<style>.stApp {background-color: #0e1117;} h1, h2, h3 {color: #f3f4f6;} .stDataFrame {border: 1px solid #374151;}</style>""", unsafe_allow_html=True)

# --- 2. CONFIGURACIÓN DE ACTIVOS ---
SPORTS_CONFIG = {
    # 🌍 RUTA MUNDIALISTA
    "soccer_conmebol_world_cup_qualifiers": {"name": "🌎 ELIMINATORIAS SUDAMÉRICA", "type": "National", "min_plan": "Spartan"},
    "soccer_uefa_nations_league": {"name": "🇪🇺 UEFA NATIONS", "type": "National", "min_plan": "Spartan"},
    "soccer_fifa_world_cup": {"name": "🏆 COPA MUNDIAL", "type": "National", "min_plan": "EventPass"},
    # 🏟️ LIGAS DE CLUBES
    "soccer_spain_la_liga": {"name": "🇪🇸 La Liga", "type": "Club", "min_plan": "Spartan"},
    "soccer_epl": {"name": "🇬🇧 Premier League", "type": "Club", "min_plan": "Titan"}, 
    "basketball_nba": {"name": "🏀 NBA", "type": "Club", "min_plan": "Titan"},       
    "americanfootball_nfl": {"name": "🏈 NFL", "type": "Club", "min_plan": "Titan"},
    "icehockey_nhl": {"name": "🏒 NHL", "type": "Club", "min_plan": "Spartan"},
    "baseball_mlb": {"name": "⚾ MLB", "type": "Club", "min_plan": "Spartan"},
}

# --- 3. SISTEMA DE LICENCIAS (GOD MODE) ---
def check_license():
    VALID_KEYS = {
        "ADMIN-KEY-999": "Titan",     # GOD MODE (Dueño)
        "TITAN-DEMO-01": "Titan",     # Cliente VIP
        "SPARTAN-DEMO": "Spartan",    # Cliente Básico
        "MUNDIAL-PREVIA": "EventPass" # Turista
    }
    
    def verify_key():
        key_input = st.session_state["input_license"].strip().upper()
        if key_input in VALID_KEYS:
            st.session_state["license_valid"] = True
            st.session_state["user_plan"] = VALID_KEYS[key_input]
            st.session_state["license_key"] = key_input
        else:
            st.session_state["license_valid"] = False
            st.error("❌ Licencia no válida.")

    if "license_valid" not in st.session_state:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.title("🛡️ SIGMA OLYMPUS")
            st.text_input("Licencia de Software:", key="input_license", on_change=verify_key, type="password")
        return False
    elif not st.session_state["license_valid"]:
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            st.title("🛡️ SIGMA OLYMPUS")
            st.text_input("Licencia de Software:", key="input_license", on_change=verify_key, type="password")
        return False
    else:
        return True

# --- 4. CACHÉ ---
@st.cache_data(ttl=300) 
def obtener_datos_api(sport, api_key):
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}'
        return requests.get(url).json()
    except: return []

# --- 5. LÓGICA MATEMÁTICA ---
SIGMA_VOLATILITY_MATRIX = {
    "basketball_nba": {
        "default": 13.5, 
        "options": {
            "🛡️ Conservadora (11.0)": 11.0, 
            "⚖️ Estándar (13.5)": 13.5, 
            "🦁 Agresiva (21.0)": 21.0
        }
    },
    "americanfootball_nfl": {
        "default": 14.5, 
        "options": {
            "🛡️ Conservadora (12.5)": 12.5, 
            "⚖️ Estándar (14.5)": 14.5, 
            "🦁 Agresiva (17.5)": 17.5
        }
    },
    "icehockey_nhl": {
        "default": 1.6, 
        "options": {
            "🛡️ Conservadora (1.2)": 1.2, 
            "⚖️ Estándar (1.6)": 1.6, 
            "🦁 Agresiva (2.1)": 2.1
        }
    },
    "soccer": {
        "default": 1.2, 
        "options": {
            "🛡️ Conservadora (0.9)": 0.9, 
            "⚖️ Estándar (1.2)": 1.2, 
            "🦁 Agresiva (1.5)": 1.5
        }
    },
    "baseball_mlb": {
        "default": 0.16, 
        "options": {
            "🛡️ Conservadora (0.12)": 0.12, 
            "⚖️ Estándar (0.16)": 0.16, 
            "🦁 Agresiva (0.22)": 0.22
        }
    },
    "tennis": {
        "default": 0.12, 
        "options": {
            "🛡️ Conservadora (0.08)": 0.08, 
            "⚖️ Estándar (0.12)": 0.12, 
            "🦁 Agresiva (0.18)": 0.18
        }
    }
}
CLUB_POWER_DB = { "Real Madrid": 1.35, "Manchester City": 1.40, "Liverpool": 1.35, "Boston Celtics": 1.30, "Kansas City Chiefs": 1.30 }
NATIONAL_POWER_DB = { "Brazil": 1.45, "France": 1.45, "Argentina": 1.40, "England": 1.35, "Germany": 1.30 }

def obtener_factor_titan(equipo, tipo_liga):
    if tipo_liga == "National": return NATIONAL_POWER_DB.get(equipo, 1.0)
    else: return CLUB_POWER_DB.get(equipo, 1.0)

def motor_titan_hibrido(home, away, cuota, sport_id, volatilidad, tipo_liga):
    prob_impl = 1 / cuota
    fuerza_home = obtener_factor_titan(home, tipo_liga)
    fuerza_away = obtener_factor_titan(away, tipo_liga)
    diferencial = fuerza_home - fuerza_away
    
    if 'soccer' in sport_id or 'nhl' in sport_id:
        lambda_home = 1.6; lambda_away = 1.1
        es_neutral = False
        if tipo_liga == "National" and "cup" in sport_id: es_neutral = True
        if not es_neutral and diferencial > -0.2: lambda_home *= 1.15 
        lambda_home *= fuerza_home; lambda_away *= fuerza_away
        g_home = np.random.poisson(lambda_home * volatilidad, 5000)
        g_away = np.random.poisson(lambda_away * volatilidad, 5000)
        wins = np.sum(g_home > g_away); validos = np.sum(g_home != g_away)
        prob_final = wins / validos if validos > 0 else 0
    else:
        std_dev = volatilidad
        spread_estimado = (prob_impl - 0.5) * std_dev * 2
        if diferencial < 0: spread_estimado += (diferencial * 8)
        sims = np.random.normal(spread_estimado, std_dev, 5000)
        prob_final = np.sum(sims > 0) / 5000
    
    if 'baseball' in sport_id: prob_final = np.mean(np.random.beta(prob_impl*100, (1-prob_impl)*100, 5000) > 0.5)
    return min(prob_final, 0.85)

def estrategia_kelly(prob, cuota, bankroll):
    if prob <= 0.50: return (0, "NO BET", "SKIP")
    b = cuota - 1; kelly = (b * prob - (1 - prob)) / b
    kelly_final = max(0, min(kelly * 0.25, 0.05))
    stake = bankroll * kelly_final
    tipo = "⚪"
    if kelly_final > 0.035: tipo = "🔥 FUERTE"
    elif kelly_final > 0.01: tipo = "✅ VALOR"
    else: tipo = "☕ LEAN"
    if stake < 5: return (0, "BAJO", "SKIP")
    return stake, f"{tipo} ({kelly_final*100:.1f}%)", tipo

# --- 6. INTERFAZ ---
def app_sigma():
    plan_actual = st.session_state["user_plan"]
    licencia_actual = st.session_state["license_key"]
    
    st.sidebar.title(f"🛡️ SIGMA | {plan_actual.upper()}")
    if st.sidebar.button("🔒 Desconectar"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    api_key = st.sidebar.text_input("🔑 API Key", type="password")
    bankroll = st.sidebar.number_input("💰 Bankroll ($)", value=1000, step=100)
    st.sidebar.markdown("---")
    
    # --- MENÚ DE RADARES ---
    opciones_visuales = []
    mapa_inverso = {}
    st.sidebar.subheader("🌍 TORNEOS INTERNACIONALES")
    for codigo, data in SPORTS_CONFIG.items():
        if data["type"] == "National":
            if plan_actual == "Spartan" and data["min_plan"] == "EventPass": nombre_mostrar = f"🔒 {data['name']} (PPV)"
            else: nombre_mostrar = f"{data['name']}"
            opciones_visuales.append(nombre_mostrar); mapa_inverso[nombre_mostrar] = codigo

    st.sidebar.subheader("🏟️ LIGAS DE CLUBES")
    for codigo, data in SPORTS_CONFIG.items():
        if data["type"] == "Club":
            if plan_actual == "EventPass": continue 
            if plan_actual == "Spartan" and data["min_plan"] == "Titan": nombre_mostrar = f"🔒 {data['name']} (TITAN)"
            else: nombre_mostrar = f"{data['name']}"
            opciones_visuales.append(nombre_mostrar); mapa_inverso[nombre_mostrar] = codigo

    default_sport = [opciones_visuales[0]] if opciones_visuales else []
    deportes_seleccionados_nombres = st.sidebar.multiselect("Seleccionar:", opciones_visuales, default=default_sport)
    deportes_reales = [mapa_inverso[d] for d in deportes_seleccionados_nombres]

    # --- CALIBRACIÓN ---
    st.sidebar.markdown("---")
    st.sidebar.header("🎚️ CALIBRACIÓN")
    perfil = SIGMA_VOLATILITY_MATRIX["basketball_nba"]
    if deportes_reales:
        s = deportes_reales[0]
        for k, v in SIGMA_VOLATILITY_MATRIX.items():
            if k in s or (k == "soccer" and "soccer" in s): perfil = v; break

    if plan_actual == "Spartan" or plan_actual == "EventPass":
        VOLATILITY = perfil["default"]
    else:
        opcion = st.sidebar.radio(f"Modo:", list(perfil["options"].keys()), index=0)
        VOLATILITY = perfil["options"][opcion]
    
    run = st.sidebar.button("🚀 INICIAR BARRIDO")

    # --- 🧪 WAR ROOM (SOLO VISIBLE PARA ADMIN/DUEÑO) ---
    # Corrección estratégica: Solo el Admin ve esto. El cliente Titan NO.
    if licencia_actual == "ADMIN-KEY-999":
        st.sidebar.markdown("---")
        st.sidebar.error("⚠️ ZONA ADMIN (SOLO TÚ)")
        with st.sidebar.expander("🧪 WAR ROOM (SIMULADOR)"):
            st.caption("Herramienta de Marketing")
            sim_liga = st.selectbox("Tipo:", ["National", "Club"])
            sim_home = st.text_input("Local", "Argentina")
            sim_away = st.text_input("Visita", "France")
            sim_cuota = st.number_input("Cuota", value=2.50, step=0.1)
            
            if st.button("SIMULAR"):
                prob_sim = motor_titan_hibrido(sim_home, sim_away, sim_cuota, "soccer", VOLATILITY, sim_liga)
                stake_sim, _, signal_sim = estrategia_kelly(prob_sim, sim_cuota, bankroll)
                st.success(f"Prob: {prob_sim:.1%}")
                st.metric("Edge", signal_sim)

    # --- DASHBOARD ---
    st.title(f"🛡️ SIGMA OLYMPUS: {plan_actual.upper()}")
    
    if run and api_key and deportes_reales:
        all_bets = []
        ahora_utc = datetime.now(timezone.utc)
        
        with st.status("📡 Analizando Datos...", expanded=True):
            for sport in deportes_reales:
                data_sport = SPORTS_CONFIG[sport]
                if plan_actual == "Spartan" and (data_sport["min_plan"] == "Titan" or data_sport["min_plan"] == "EventPass"):
                    st.error(f"❌ {data_sport['name']}: Acceso Denegado."); continue

                res = obtener_datos_api(sport, api_key)
                if not res: st.error(f"Sin datos para {sport}"); continue
                
                for game in res:
                    try:
                        home, away = game['home_team'], game['away_team']
                        inicio = datetime.strptime(game['commence_time'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        hora = inicio.strftime("%H:%M")
                        diff = (inicio - ahora_utc).total_seconds() / 3600
                        penal = 0.05 if diff > 24 else (0.02 if diff > 1 else 0.0)
                        t_icon = "🔴" if diff > 24 else ("🟡" if diff > 1 else "🟢")
                        
                        if not game['bookmakers']: continue
                        odds = game['bookmakers'][0]['markets'][0]['outcomes']
                        cuota = next((x['price'] for x in odds if x['name'] == home), 0)
                        
                        if 'icehockey' in sport and cuota > 5.0: continue
                        if cuota < 1.05: continue
                        
                        prob = motor_titan_hibrido(home, away, cuota, sport, VOLATILITY, data_sport["type"])
                        prob_adj = prob - penal
                        stake, desc, tipo = estrategia_kelly(prob_adj, cuota, bankroll)
                        
                        if stake > 0:
                            all_bets.append({"T": t_icon, "Hora": hora, "Torneo": data_sport['name'], "Partido": f"{home} vs {away}", "Cuota": cuota, "Prob": f"{prob_adj:.1%}", "Stake": f"${stake:.2f}", "Señal": tipo})
                    except: continue
        
        if all_bets:
            st.dataframe(pd.DataFrame(all_bets).style.applymap(lambda x: 'color: #4ade80' if 'FUERTE' in str(x) else '', subset=['Señal']), use_container_width=True)
        else: st.warning("❄️ Sin resultados.")

if __name__ == "__main__":
    if check_license():
        app_sigma()