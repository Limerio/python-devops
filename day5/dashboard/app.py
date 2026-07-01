"""Streamlit dashboard for the DevOps Monitoring API."""

import os
import time

import httpx
import pandas as pd
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "dev-key-change-me")
HISTORY_LENGTH = 60

st.set_page_config(page_title="DevOps Monitor", page_icon="📊", layout="wide")

if "metrics_history" not in st.session_state:
    st.session_state.metrics_history = []


@st.cache_data(ttl=2)
def fetch_metrics() -> dict:
    """Fetch live metrics from the API."""
    response = httpx.get(f"{API_BASE_URL}/metrics", timeout=5.0)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=5)
def fetch_servers() -> list[dict]:
    """Fetch registered servers."""
    response = httpx.get(f"{API_BASE_URL}/servers", timeout=5.0)
    response.raise_for_status()
    return response.json()


def status_color(status: str) -> str:
    """Return background color for server status."""
    colors = {
        "UP": "background-color: #d4edda",
        "DEGRADED": "background-color: #fff3cd",
        "DOWN": "background-color: #f8d7da",
        "UNKNOWN": "background-color: #e2e3e5",
    }
    return colors.get(status, "")


st.title("📊 DevOps Monitoring Dashboard")
st.caption(f"API: `{API_BASE_URL}`")

tab_metrics, tab_servers = st.tabs(["Métriques", "Serveurs"])

with tab_metrics:
    try:
        metrics = fetch_metrics()
        col1, col2, col3 = st.columns(3)
        col1.metric("CPU", f"{metrics['cpu_percent']:.1f}%")
        col2.metric("Mémoire", f"{metrics['memory_percent']:.1f}%")
        col3.metric("Disque", f"{metrics['disk_percent']:.1f}%")

        snapshot = {
            "cpu_percent": metrics["cpu_percent"],
            "memory_percent": metrics["memory_percent"],
            "disk_percent": metrics["disk_percent"],
        }
        st.session_state.metrics_history.append(snapshot)
        if len(st.session_state.metrics_history) > HISTORY_LENGTH:
            st.session_state.metrics_history = (
                st.session_state.metrics_history[-HISTORY_LENGTH:]
            )

        if st.session_state.metrics_history:
            chart_df = pd.DataFrame(st.session_state.metrics_history)
            st.line_chart(chart_df, height=250)
            st.caption(f"Fenêtre live — {len(st.session_state.metrics_history)} points")
    except Exception as exc:
        st.error(f"Impossible de joindre l'API : {exc}")

with tab_servers:
    try:
        servers = fetch_servers()
        if not servers:
            st.info("Aucun serveur enregistré.")
        else:
            df = pd.DataFrame(servers)
            styled = df.style.map(
                lambda _: "",
                subset=pd.IndexSlice[:, :],
            ).apply(
                lambda row: [status_color(row["status"])] * len(row),
                axis=1,
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

        with st.form("register_server", clear_on_submit=True):
            st.subheader("Enregistrer un serveur")
            name = st.text_input("Nom")
            host = st.text_input("Hôte", value="api")
            port = st.number_input("Port", min_value=1, max_value=65535, value=8000)
            submitted = st.form_submit_button("Enregistrer")
            if submitted:
                response = httpx.post(
                    f"{API_BASE_URL}/servers",
                    json={"name": name, "host": host, "port": int(port)},
                    headers={"X-API-Key": API_KEY},
                    timeout=5.0,
                )
                if response.status_code == 201:
                    st.success(f"Serveur '{name}' enregistré.")
                    fetch_servers.clear()
                    st.rerun()
                else:
                    st.error(f"Erreur {response.status_code}: {response.text}")
    except Exception as exc:
        st.error(f"Erreur serveurs : {exc}")

time.sleep(1)
st.rerun()
