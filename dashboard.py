# App Streamlit que lê os dados coletados pelo flight_collector em background
# e exibe na UI, com o layout e customizações solicitadas.

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import os
import re
import subprocess
import pytz

# --- Configurações ---
SCHEDULE_FILE = 'flight_schedule.json'
REFRESH_INTERVAL = 20

STATUS_TRANSLATION = {
    'landed': 'Pouso estimado às',
    'estimated': 'Estimado às',
    'scheduled': 'Programado para',
    'delayed': 'Atrasado para',
    'cancelled': 'Cancelado',
    'departed': 'Partida estimada às',
    'unknown': 'Status desconhecido'
}

# Estado global para armazenar os horários dos cards de destaque
st.session_state.setdefault('last_highlight_arr_time', None)
st.session_state.setdefault('last_highlight_dep_time', None)
st.session_state.setdefault('flash_arr_counter', 0)
st.session_state.setdefault('flash_dep_counter', 0)
st.session_state.setdefault('historico_voos', [])
st.session_state.setdefault('modo_simplificado', False)

def load_schedule():
    try:
        subprocess.run(['python3', 'flight_collector.py'], check=True)
        with open(SCHEDULE_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar schedule: {e}")
        return {}

def translate_status(status, time_str):
    if not status:
        return 'Status desconhecido'
    label = STATUS_TRANSLATION.get(status.strip().lower(), 'Status desconhecido')
    if time_str:
        return f"{label} {time_str}"
    return label

def to_dataframe(schedule_list):
    rows = []
    for item in schedule_list:
        flight = item.get('flight', {})
        identification = flight.get('identification', {})
        callsign = identification.get('callsign') or identification.get('number', {}).get('default', '')

        status_raw = flight.get('status', {})
        status = (status_raw.get('generic', {}).get('status', {}).get('text') or 
                  status_raw.get('text') or 'unknown')

        event_utc_ts = (
            flight.get('status', {}).get('generic', {}).get('eventTime', {}).get('utc') or
            flight.get('time', {}).get('scheduled', {}).get('arrival') or
            flight.get('time', {}).get('scheduled', {}).get('departure')
        )

        time_str = ''
        dt_brt = None
        if event_utc_ts:
            try:
                dt_brt = datetime.fromtimestamp(event_utc_ts, pytz.timezone('America/Sao_Paulo'))
                time_str = dt_brt.strftime('%H:%M')
            except Exception:
                pass

        status_label = translate_status(status, time_str)

        origin = flight.get('airport', {}).get('origin', {}).get('name', '')
        destination = flight.get('airport', {}).get('destination', {}).get('name', '')
        location = origin or destination or ''

        aeronave_model = flight.get('aircraft', {}).get('model', {}).get('text')
        aeronave_code = flight.get('aircraft', {}).get('model', {}).get('code')
        aeronave = aeronave_model or aeronave_code or ''

        airline = flight.get('airline', {}).get('name', '')

        row = {
            'Horario': f"{time_str}h" if time_str else '',
            'Voo': callsign or '',
            'Origem/Destino': location,
            'Companhia': airline,
            'Aeronave': aeronave,
            'Status': status_label,
            'RawStatus': status,
            'HoraBruta': time_str,
            'BRTDatetime': dt_brt if dt_brt else pd.NaT
        }
        rows.append(row)
    return pd.DataFrame(rows)

def atualizar_historico(voo, tipo):
    if voo is None:
        return
    item = voo.copy()
    item['Tipo'] = tipo
    historico = st.session_state['historico_voos']
    historico.insert(0, item)
    st.session_state['historico_voos'] = historico[:5]

def render_destaque(info, tipo):
    if info is None:
        st.info("Sem destaque no momento.")
        return

    key_last_index = 'highlight_arr_index' if tipo == 'arrival' else 'highlight_dep_index'
    key_flash = 'flash_arr_counter' if tipo == 'arrival' else 'flash_dep_counter'

    if key_last_index in st.session_state and info.name != st.session_state[key_last_index]:
        st.session_state[key_flash] = 6

    flash = st.session_state[key_flash] > 0
    if flash:
        st.session_state[key_flash] -= 1

    aeronave = f"<br><i>{info['Aeronave']}</i>" if info.get('Aeronave') else f"<br><i>{info['Voo']}</i>"

    if tipo == 'arrival':
        texto_principal = f"<b>{info['Companhia']}</b> - {info['Voo']}{aeronave}<br>Vindo de: {info['Origem/Destino']}<br>Status: {info['Status']}"
        bg_color = '#b84c4c' if flash else '#3a0f0f'
        emoji = '🛬'
    else:
        texto_principal = f"<b>{info['Companhia']}</b> - {info['Voo']}{aeronave}<br>Para: {info['Origem/Destino']}<br>Status: {info['Status']}"
        bg_color = '#3db86d' if flash else '#0f3a1a'
        emoji = '🛫'

    html = f"""
    <div style='background-color:{bg_color}; padding:20px; border-radius:20px; color:white; font-weight:bold; font-size:18px; text-align:center;'>
        <div style='font-size:30px'>{emoji}</div>
        {texto_principal}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def get_next_event(df, tipo):
    agora = pd.Timestamp.now(tz='America/Sao_Paulo')
    hora_analise = agora + timedelta(minutes=2)

    key_evento = 'highlight_arr_event' if tipo == 'arrival' else 'highlight_dep_event'
    key_index = 'highlight_arr_index' if tipo == 'arrival' else 'highlight_dep_index'

    if key_evento in st.session_state:
        voo_atual = st.session_state[key_evento]
        if isinstance(voo_atual, pd.Series):
            hora_voo = voo_atual.get('BRTDatetime')
            if hora_voo and agora < hora_voo + timedelta(minutes=1):
                return voo_atual
            else:
                atualizar_historico(voo_atual, 'Chegada' if tipo == 'arrival' else 'Partida')

    df_valid = df[df['BRTDatetime'] >= hora_analise].sort_values('BRTDatetime')

    if not df_valid.empty:
        proximo_voo = df_valid.iloc[0]
        st.session_state[key_evento] = proximo_voo
        st.session_state[key_index] = proximo_voo.name
        return proximo_voo

    return None

# --- Interface Principal ---
st.set_page_config(page_title="Berenices da Sacada - Aeroporto", layout="wide")

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=REFRESH_INTERVAL * 1000, key='auto_refresh_data')
except ImportError:
    st.warning("Para atualização automática, instale: pip install streamlit-autorefresh")

col_toggle, col_title = st.columns([1, 6])
with col_toggle:
    st.session_state['modo_simplificado'] = st.checkbox("Simplificar", value=st.session_state['modo_simplificado'])

with col_title:
    st.markdown("""
    <h1 style='text-align: left; margin-bottom: 1rem;'>✈ Berenices da Sacada - Aeroporto</h1>
    """, unsafe_allow_html=True)

now_brt = datetime.now(pytz.timezone('America/Sao_Paulo'))
st.markdown(f"**Hora local:** {now_brt.strftime('%Y-%m-%d %H:%M:%S')} BRT")

schedule = load_schedule()

fetched = schedule.get('fetched_at_utc')
if fetched:
    fetched_clean = re.sub(r'\..*', '', fetched.replace("T", " ").replace("Z", ""))
    ts = datetime.strptime(fetched_clean, "%Y-%m-%d %H:%M:%S")
    ts_brt = ts.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Sao_Paulo'))
    st.success(f"Dados atualizados em: {ts_brt.strftime('%Y-%m-%d %H:%M:%S')} BRT | Página recarregada às {now_brt.strftime('%H:%M:%S')}")
else:
    st.warning("Nenhum dado carregado. Verifique se o flight_collector está rodando.")

df_arr = to_dataframe(schedule.get('arrivals', []))
df_dep = to_dataframe(schedule.get('departures', []))

highlight_arr = get_next_event(df_arr, 'arrival')
highlight_dep = get_next_event(df_dep, 'departure')

st.markdown("""
<style>
    .center-container > div {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state['modo_simplificado']:
    with st.sidebar:
        st.markdown("### Próximas Chegadas")
        if not df_arr.empty:
            st.dataframe(df_arr.drop(columns=['RawStatus', 'HoraBruta', 'BRTDatetime']), use_container_width=True, height=250)
        else:
            st.info("Nenhuma chegada listada.")

        st.markdown("### Próximas Partidas")
        if not df_dep.empty:
            st.dataframe(df_dep.drop(columns=['RawStatus', 'HoraBruta', 'BRTDatetime']), use_container_width=True, height=250)
        else:
            st.info("Nenhuma partida listada.")

        st.markdown("### Histórico de Destaques")
        historico = pd.DataFrame(st.session_state['historico_voos'])
        if not historico.empty:
            st.dataframe(historico[['Tipo', 'Horario', 'Voo', 'Origem/Destino', 'Companhia']], use_container_width=True, height=180)
        else:
            st.info("Nenhum destaque anterior.")

with st.container():
    st.markdown("<div class='center-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Chegada em Destaque")
        render_destaque(highlight_arr, 'arrival')
    with col2:
        st.subheader("Partida em Destaque")
        render_destaque(highlight_dep, 'departure')

    st.subheader("Vídeo ao Vivo")
    st.components.v1.html("""
    <iframe width="100%" height="500" 
    src="https://www.youtube.com/embed/llszXlN8oCo?autoplay=1&mute=1" 
    title="YouTube video player" frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
    allowfullscreen></iframe>
    """, height=500)
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"A página e dados são atualizados a cada {REFRESH_INTERVAL}s automaticamente.")
