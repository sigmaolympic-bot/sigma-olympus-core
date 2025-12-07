import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timezone
from scipy.stats import poisson
from collections import Counter

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="SIGMA | OLYMPUS TERMINAL", layout="wide", page_icon="🛡️")

# Estilo CSS para que los precios se vean profesionales
st.markdown("""
    <style>
    .stApp {background-color: #0e1117;} 
    h1, h2, h3 {color: #f3f4f6;} 
    .stDataFrame {border: 1px solid #374151;}
    .price-card {
        background-color: #1f2937;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #374151;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DICCIONARIO DE IDIOMAS ---
TRANSLATIONS = {
    "ES": {
        "sidebar_title": "🛡️ SIGMA | {}", "disconnect": "🔒 Desconectar", "api_label": "🔑 API Key", "bankroll_label": "💰 Bankroll ($)",
        "nav_label": "Navegación:", "nav_options": ["📡 ESCÁNER", "💰 MI CARTERA", "🧪 WAR ROOM"], "radars_label": "📡 Radares Activos:",
        "calibration_label": "🎚️ CALIBRACIÓN", "mode_label": "Modo Táctico:", "run_btn": "🚀 INICIAR BARRIDO", "analyzing": "Simulando Escenarios...",
        "no_data": "Sin datos para {}", "access_denied": "❌ Acceso Denegado: Requiere Plan {}", "results_table": "🎯 OBJETIVOS & MARCADORES",
        "no_results": "❄️ Sin resultados o Escáner no iniciado.", "save_btn": "✅ GUARDAR EN CARTERA", "portfolio_title": "💰 GESTIÓN DE PATRIMONIO",
        "clean_btn": "🗑️ Limpiar Cartera", "war_room_title": "🧪 LABORATORIO (ADMIN)", "login_title": "🛡️ SIGMA OLYMPUS",
        "login_input": "Licencia de Software:", "login_error": "❌ Licencia no válida."
    },
    "EN": {
        "sidebar_title": "🛡️ SIGMA | {}", "disconnect": "🔒 Disconnect", "api_label": "🔑 API Key", "bankroll_label": "💰 Bankroll ($)",
        "nav_label": "Navigation:", "nav_options": ["📡 SCANNER", "💰 MY PORTFOLIO", "🧪 WAR ROOM"], "radars_label": "📡 Active Radars:",
        "calibration_label": "🎚️ CALIBRATION", "mode_label": "Tactical Mode:", "run_btn": "🚀 START SCAN", "analyzing": "Simulating Scenarios...",
        "no_data": "No data for {}", "access_denied": "❌ Access Denied: Requires {} Plan", "results_table": "🎯 TARGETS & SCORES",
        "no_results": "❄️ No results or Scanner not started.", "save_btn": "✅ ADD TO PORTFOLIO", "portfolio_title": "💰 WEALTH MANAGEMENT",
        "clean_btn": "🗑️ Clear Portfolio", "war_room_title": "🧪 LABORATORY (ADMIN)", "login_title": "🛡️ SIGMA OLYMPUS",
        "login_input": "Software License Key:", "login_error": "❌ Invalid License."
    }
}

# --- 3. SISTEMA DE LICENCIAS & LANDING PAGE (SHOWROOM) ---
def check_license(lang_code):
    t = TRANSLATIONS[lang_code]
    VALID_KEYS = {
        "ADMIN-KEY-999": "Titan", "TITAN-DEMO-01": "Titan", "OLYMPIAN-DEMO": "Olympian",
        "SPARTAN-DEMO": "Spartan", "MUNDIAL-PREVIA": "EventPass"
    }
    
    def verify_key():
        key_input = st.session_state["input_license"].strip().upper()
        if key_input in VALID_KEYS:
            st.session_state["license_valid"] = True
            st.session_state["user_plan"] = VALID_KEYS[key_input]
            st.session_state["license_key"] = key_input
        else: st.session_state["license_valid"] = False; st.error(t["login_error"])

    # SI NO ESTÁ LOGUEADO -> MUESTRA LA LANDING PAGE
    if "license_valid" not in st.session_state or not st.session_state["license_valid"]:
        
        # --- HEADER ---
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🛡️ SIGMA OLYMPUS")
            st.caption("INSTITUTIONAL SPORTS INTELLIGENCE TERMINAL")
            st.markdown("---")
            
            # --- LOGIN AREA (PRIORIDAD ALTA) ---
            st.subheader("🔓 MEMBER ACCESS")
            st.text_input(t["login_input"], key="input_license", on_change=verify_key, type="password", placeholder="Enter License Key...")
            st.markdown("---")

        # --- SECCIÓN DE VENTAS (PRICING) ---
        st.header("💎 CHOOSE YOUR WEAPON")
        st.write("Join the elite using mathematical edge.")
        
        p1, p2, p3 = st.columns(3)
        
        with p1:
            st.info("⚔️ SPARTAN")
            st.metric("ENTRY", "$29 / mo")
            st.markdown("""
            * ✅ Soccer & MLB
            * ✅ Basic Signals
            * 🔒 No NBA/NFL
            """)
            # Aquí pondrás tu link de WHOP real luego
            st.link_button("START TRIAL", "https://whop.com/") 

        with p2:
            st.success("🏛️ OLYMPIAN (Best Seller)")
            st.metric("STANDARD", "$59 / mo")
            st.markdown("""
            * ✅ **NBA, NFL, EPL**
            * ✅ Portfolio Tracking
            * ✅ Priority Support
            """)
            st.link_button("GET ACCESS", "https://whop.com/")

        with p3:
            st.warning("🦁 TITAN")
            st.metric("INSTITUTIONAL", "$99 / mo")
            st.markdown("""
            * ✅ **GOD MODE**
            * ✅ Volatility Control
            * ✅ War Room Access
            """)
            st.link_button("JOIN ELITE", "https://whop.com/")

        st.divider()
        st.caption("© 2025 SIGMA OLYMPUS LLC | Powered by Poisson & Gauss Hybrid Engines.")
        
        return False
    return True

# --- 4. MOTORES Y LÓGICA (IGUAL A V23.1) ---
if 'portfolio' not in st.session_state: st.session_state['portfolio'] = []
if 'last_results' not in st.session_state: st.session_state['last_results'] = [] 

def guardar_apuesta(bet_data):
    if bet_data not in st.session_state['portfolio']: 
        st.session_state['portfolio'].append(bet_data)
        st.toast("✅ Saved / Guardado")
    else: st.toast("⚠️ Already in Portfolio")

@st.cache_data(ttl=300) 
def obtener_datos_api(sport, api_key):
    try: return requests.get(f'https://api.the-odds-api.com/v4/sports/{sport}/odds/?regions=us&markets=h2h&oddsFormat=decimal&apiKey={api_key}').json()
    except: return []

SPORTS_CONFIG = {
    "soccer_fifa_world_cup": {"name": "🏆 COPA MUNDIAL", "type": "National", "min_plan": "EventPass"},
    "mma_mixed_martial_arts_ufc": {"name": "🥊 UFC / MMA", "type": "National", "min_plan": "EventPass"}, 
    "boxing_boxing": {"name": "🥊 BOXEO ESTELAR", "type": "National", "min_plan": "EventPass"},
    "soccer_conmebol_world_cup_qualifiers": {"name": "🌎 ELIMINATORIAS", "type": "National", "min_plan": "Spartan"},
    "soccer_usa_mls": {"name": "🇺🇸 MLS (Fútbol USA)", "type": "Club", "min_plan": "Spartan"}, 
    "soccer_spain_la_liga": {"name": "🇪🇸 La Liga", "type": "Club", "min_plan": "Spartan"},
    "soccer_mexico_ligamx": {"name": "🇲🇽 Liga MX", "type": "Club", "min_plan": "Spartan"},
    "soccer_italy_serie_a": {"name": "🇮🇹 Serie A", "type": "Club", "min_plan": "Spartan"}, 
    "soccer_epl": {"name": "🇬🇧 Premier League", "type": "Club", "min_plan": "Olympian"}, 
    "basketball_nba": {"name": "🏀 NBA", "type": "Club", "min_plan": "Olympian"},       
    "americanfootball_nfl": {"name": "🏈 NFL", "type": "Club", "min_plan": "Olympian"},
    "americanfootball_ncaaf": {"name": "🎓 NCAA Football", "type": "Club", "min_plan": "Titan"},
    "icehockey_nhl": {"name": "🏒 NHL", "type": "Club", "min_plan": "Spartan"},
    "baseball_mlb": {"name": "⚾ MLB", "type": "Club", "min_plan": "Spartan"},
}

SIGMA_VOLATILITY_MATRIX = {
    "basketball_nba": {"default": 13.5, "options": {"🛡️ Conservadora": 11.0, "⚖️ Estándar": 13.5, "🦁 Agresiva": 21.0}},
    "americanfootball_nfl": {"default": 14.5, "options": {"🛡️ Conservadora": 12.5, "⚖️ Estándar": 14.5, "🦁 Agresiva": 17.5}},
    "icehockey_nhl": {"default": 1.6, "options": {"🛡️ Conservadora": 1.2, "⚖️ Estándar": 1.6, "🦁 Agresiva": 2.1}},
    "soccer": {"default": 1.2, "options": {"🛡️ Conservadora": 0.9, "⚖️ Estándar": 1.2, "🦁 Agresiva": 1.5}},
    "baseball_mlb": {"default": 0.16, "options": {"🛡️ Conservadora": 0.12, "⚖️ Estándar": 0.16, "🦁 Agresiva": 0.22}},
    "tennis": {"default": 0.12, "options": {"🛡️ Conservadora": 0.12, "⚖️ Estándar": 0.12, "🦁 Agresiva": 0.18}},
    "mma": {"default": 0.45, "options": {"🛡️ Conservadora": 0.35, "⚖️ Estándar": 0.45, "🦁 Agresiva": 0.60}} 
}

CLUB_POWER_DB = { "Real Madrid": 1.35, "Manchester City": 1.40, "Liverpool": 1.35, "Boston Celtics": 1.30, "Kansas City Chiefs": 1.30 }
NATIONAL_POWER_DB = { "Brazil": 1.45, "France": 1.45, "Argentina": 1.40 }
def obtener_factor_titan(equipo, tipo_liga): return NATIONAL_POWER_DB.get(equipo, 1.0) if tipo_liga == "National" else CLUB_POWER_DB.get(equipo, 1.0)

def motor_titan_hibrido(home, away, cuota, sport_id, volatilidad, tipo_liga, n_sims=5000):
    prob_impl = 1 / cuota
    extra_data = "N/A"
    
    if 'mma' in sport_id or 'boxing' in sport_id or 'baseball' in sport_id or 'tennis' in sport_id:
        factor_ajuste = 0
        if prob_impl > 0.70 and 'mma' in sport_id: factor_ajuste = 0.05 
        sims = np.random.beta(prob_impl*100, (1-prob_impl)*100, n_sims)
        prob_final = np.mean(sims + factor_ajuste > 0.5)
        return min(prob_final, 0.90), "Volatile"

    fuerza_home = obtener_factor_titan(home, tipo_liga); fuerza_away = obtener_factor_titan(away, tipo_liga)
    if 'soccer' in sport_id or 'nhl' in sport_id:
        lambda_home = 1.6; lambda_away = 1.1
        if 'soccer' in sport_id and (fuerza_home - fuerza_away) > -0.2: lambda_home *= 1.15 
        lambda_home *= fuerza_home; lambda_away *= fuerza_away
        g_home = np.random.poisson(lambda_home * volatilidad, n_sims)
        g_away = np.random.poisson(lambda_away * volatilidad, n_sims)
        wins = np.sum(g_home > g_away); validos = np.sum(g_home != g_away)
        try:
            pares = list(zip(g_home, g_away))
            marcador_comun = Counter(pares).most_common(1)[0][0]
            extra_data = f"{marcador_comun[0]} - {marcador_comun[1]}"
        except: extra_data = "?-?"
        return (wins / validos if validos > 0 else 0), extra_data
    else:
        std_dev = volatilidad
        spread_estimado = (prob_impl - 0.5) * std_dev * 2
        diferencial = fuerza_home - fuerza_away
        if diferencial < 0: spread_estimado += (diferencial * 8)
        sims = np.random.normal(spread_estimado, std_dev, n_sims)
        margen_medio = np.mean(sims)
        signo = "+" if margen_medio > 0 else ""
        extra_data = f"Margen {signo}{margen_medio:.1f}"
        return (np.sum(sims > 0) / n_sims), extra_data

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

# --- 6. APP PRINCIPAL ---
def app_sigma(lang_code):
    t = TRANSLATIONS[lang_code]
    plan_actual = st.session_state["user_plan"]
    st.sidebar.title(t["sidebar_title"].format(plan_actual.upper()))
    menu_nav = st.sidebar.radio(t["nav_label"], t["nav_options"], index=0)
    if st.sidebar.button(t["disconnect"]):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

    if menu_nav == t["nav_options"][0]: 
        api_key = st.sidebar.text_input(t["api_label"], type="password")
        bankroll = st.sidebar.number_input(t["bankroll_label"], value=1000, step=100)
        st.sidebar.markdown("---")
        opciones_visuales = []; mapa_inverso = {}
        for codigo, data in SPORTS_CONFIG.items():
            acceso_ok = False
            if plan_actual == "Titan": acceso_ok = True
            elif plan_actual == "Olympian" and data["min_plan"] != "Titan": acceso_ok = True
            elif plan_actual == "Spartan" and data["min_plan"] == "Spartan": acceso_ok = True
            elif plan_actual == "EventPass" and data["type"] == "National": acceso_ok = True
            nm = f"{data['name']}" if acceso_ok else f"🔒 {data['name']}"
            opciones_visuales.append(nm); mapa_inverso[nm] = codigo
        
        default_sport = [opciones_visuales[0]] if opciones_visuales else []
        deportes_sel = st.sidebar.multiselect(t["radars_label"], opciones_visuales, default=default_sport)
        deportes_reales = [mapa_inverso[d] for d in deportes_sel]

        st.sidebar.header(t["calibration_label"])
        perfil = SIGMA_VOLATILITY_MATRIX["basketball_nba"]
        if deportes_reales:
            for k, v in SIGMA_VOLATILITY_MATRIX.items():
                if k in deportes_reales[0] or (k == "soccer" and "soccer" in deportes_reales[0]) or (k == "mma" and ("mma" in deportes_reales[0] or "boxing" in deportes_reales[0])): perfil = v; break
        
        if plan_actual == "Titan":
            opcion = st.sidebar.radio(t["mode_label"], list(perfil["options"].keys()), index=1)
            VOLATILITY = perfil["options"][opcion]
        else: st.sidebar.caption("🔒 Auto-Calibración"); VOLATILITY = perfil["default"]

        run = st.sidebar.button(t["run_btn"])
        st.title(f"📡 {plan_actual.upper()} TERMINAL")
        
        if run and api_key and deportes_reales:
            st.session_state['last_results'] = [] 
            ahora_utc = datetime.now(timezone.utc)
            if plan_actual == "Titan": N_SIMS = 15000 
            elif plan_actual == "Olympian": N_SIMS = 5000 
            else: N_SIMS = 2500 

            with st.status(f"{t['analyzing']} ({N_SIMS} Sims)", expanded=True):
                for sport in deportes_reales:
                    data_sport = SPORTS_CONFIG[sport]
                    min_plan = data_sport["min_plan"]
                    allowed = False
                    if plan_actual == "Titan": allowed = True
                    elif plan_actual == "Olympian" and min_plan in ["Spartan", "Olympian", "EventPass"]: allowed = True
                    elif plan_actual == "Spartan" and min_plan in ["Spartan"]: allowed = True
                    elif plan_actual == "EventPass" and min_plan == "EventPass": allowed = True
                    if not allowed: st.error(t["access_denied"].format(min_plan)); continue
                    res = obtener_datos_api(sport, api_key)
                    if not res: st.error(t["no_data"].format(sport)); continue
                    
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
                            
                            prob, extra = motor_titan_hibrido(home, away, cuota, sport, VOLATILITY, data_sport["type"], N_SIMS)
                            prob_adj = prob - penal
                            stake, desc, tipo = estrategia_kelly(prob_adj, cuota, bankroll)
                            
                            if stake > 0:
                                st.session_state['last_results'].append({"T": t_icon, "Hora": hora, "Torneo": data_sport['name'], "Partido": f"{home} vs {away}", "Cuota": cuota, "Prob": f"{prob_adj:.1%}", "Score/Data": extra, "Stake": f"${stake:.2f}", "Señal": tipo, "Raw_Stake": stake})
                        except: continue
        
        if st.session_state['last_results']:
            st.subheader(t["results_table"])
            df = pd.DataFrame(st.session_state['last_results']).drop(columns=["Raw_Stake"])
            st.dataframe(df.style.applymap(lambda x: 'color: #4ade80' if 'FUERTE' in str(x) else '', subset=['Señal']), use_container_width=True)
            opciones_guardar = [f"{x['Partido']} ({x['Señal']})" for x in st.session_state['last_results']]
            seleccion = st.selectbox("Select:", opciones_guardar)
            if st.button(t["save_btn"]):
                item = next((x for x in st.session_state['last_results'] if f"{x['Partido']} ({x['Señal']})" == seleccion), None)
                if item: guardar_apuesta(item)
        else:
            if not run: st.info(t["no_results"])

    elif menu_nav == t["nav_options"][1]: 
        st.title(t["portfolio_title"])
        if st.session_state['portfolio']:
            df_port = pd.DataFrame(st.session_state['portfolio'])
            st.dataframe(df_port.drop(columns=["Raw_Stake"]), use_container_width=True)
            if st.button(t["clean_btn"]): st.session_state['portfolio'] = []; st.rerun()
        else: st.info("Empty / Vacía")

    elif menu_nav == t["nav_options"][2]:
        if st.session_state["license_key"] == "ADMIN-KEY-999":
            st.title(t["war_room_title"])
            sim_h = st.text_input("Home", "Argentina"); sim_a = st.text_input("Away", "France"); sim_c = st.number_input("Odds", 2.50)
            if st.button("Simulate"): st.success("OK")
        else: st.error("⛔ ADMIN ONLY")

if __name__ == "__main__":
    lang = st.sidebar.selectbox("Language / Idioma", ["EN", "ES"])
    if check_license(lang): app_sigma(lang)
