import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

API_URL = os.getenv("DASBOARD_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 15

st.set_page_config(
    page_title="UrbanMove Dashboard",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 1.5rem;
            max-width: 1400px;
        }
        .hero-card {
            padding: 1.3rem 1.4rem;
            border-radius: 20px;
            background: linear-gradient(135deg, rgba(35,85,180,0.12), rgba(0,180,140,0.10));
            border: 1px solid rgba(120,120,140,0.18);
            margin-bottom: 1rem;
        }
        .section-card {
            padding: 1rem 1.2rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(120,120,140,0.14);
            margin-bottom: 1rem;
        }
        .small-muted {
            color: #8b93a7;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_session() -> None:
    defaults = {
        "token": None,
        "role": None,
        "username": None,
        "logged_in": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session()


def get_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    token = st.session_state.get("token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def handle_api_error(response: requests.Response) -> None:
    try:
        payload = response.json()
        detail = payload.get("detail", response.text)
    except Exception:
        detail = response.text
    st.error(f"Request failed ({response.status_code}): {detail}")


def safe_get(endpoint: str) -> Optional[Any]:
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            headers=get_headers(),
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        handle_api_error(response)
        return None
    except requests.RequestException as exc:
        st.error(f"Could not reach backend: {exc}")
        return None


def safe_post(
    endpoint: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Optional[Any]:
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            headers=get_headers(),
            data=data,
            json=json,
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code in (200, 201):
            return response.json()
        handle_api_error(response)
        return None
    except requests.RequestException as exc:
        st.error(f"Could not reach backend: {exc}")
        return None


def login(username: str, password: str) -> bool:
    result = safe_post("/auth/login", data={"username": username, "password": password})
    if not result:
        return False

    st.session_state.token = result.get("access_token")
    st.session_state.role = result.get("role")
    st.session_state.username = result.get("username", username)
    st.session_state.logged_in = True
    return True


def register_user(username: str, password: str) -> bool:
    result = safe_post(
        "/auth/register",
        json={"username": username, "password": password}
    )
    if not result:
        return False

    st.session_state.token = result.get("access_token")
    st.session_state.role = result.get("role")
    st.session_state.username = result.get("username", username)
    st.session_state.logged_in = True
    return True


def logout() -> None:
    st.session_state.token = None
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.logged_in = False


def ensure_list(data: Any) -> List[Any]:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("items", "data", "vehicles", "traffic", "hotspots", "reroutes"):
            value = data.get(key)
            if isinstance(value, list):
                return value
        return [data]
    return []


def count_status(items: List[Dict[str, Any]], field_name: str, target: str) -> int:
    return sum(
        1 for item in items
        if str(item.get(field_name, "")).lower() == target.lower()
    )


def top_banner() -> None:
    st.markdown(
        """
        <div class="hero-card">
            <h1 style="margin-bottom:0.2rem;">UrbanMove Control Center</h1>
            <div class="small-muted">
                Real-time mobility visibility, route assistance, and operational analytics powered by your FastAPI backend.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_controls() -> str:
    with st.sidebar:
        st.markdown("## UrbanMove")
        st.caption("Smart Mobility Platform")
        st.write(f"**API**: `{API_URL}`")

        if st.session_state.logged_in:
            st.success(f"Logged in as **{st.session_state.username}**")
            st.write(f"Role: **{st.session_state.role}**")

            page = st.radio(
                "Navigation",
                ["Overview", "Mobility Monitor", "Route & Admin"],
            )

            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()

            return page

        return "Login"


def login_screen() -> None:
    top_banner()

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        mode = st.radio("Access", ["Login", "Create account"], horizontal=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)

        if mode == "Login":
            st.subheader("Sign in")
            st.caption("Use your UrbanMove credentials to access the dashboard.")

            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.warning("Enter both username and password.")
                else:
                    if login(username, password):
                        st.success("Login successful.")
                        st.rerun()

        else:
            st.subheader("Create account")
            st.caption("Create a standard user account.")

            with st.form("register_form"):
                username = st.text_input("Choose a username", key="register_username")
                password = st.text_input("Choose a password", type="password", key="register_password")
                confirm_password = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create user", use_container_width=True)

            if submitted:
                if not username or not password or not confirm_password:
                    st.warning("Fill in all fields.")
                elif password != confirm_password:
                    st.warning("Passwords do not match.")
                else:
                    if register_user(username, password):
                        st.success("User created successfully.")
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.info("Make sure the backend is running and /auth/login and /auth/register are reachable.")


def page_overview() -> None:
    top_banner()
    st.subheader("Overview")
    st.caption("A quick operational summary of the UrbanMove platform.")

    refresh = st.button("Refresh data")
    if refresh:
        st.rerun()

    health = safe_get("/health")
    vehicles_data = safe_get("/vehicles")
    traffic_data = safe_get("/traffic")

    overview_data = None
    if st.session_state.role == "admin":
        overview_data = safe_get("/analytics/overview")

    vehicles = ensure_list(vehicles_data)
    traffic = ensure_list(traffic_data)

    total_vehicles = len(vehicles)
    moving_vehicles = count_status(vehicles, "status", "moving")
    high_traffic_segments = count_status(traffic, "traffic_level", "high")

    a, b, c, d = st.columns(4)
    a.metric("Backend Health", "Online" if health else "Unavailable")
    b.metric("Vehicles", total_vehicles)
    c.metric("Moving Vehicles", moving_vehicles)
    d.metric("High Traffic Segments", high_traffic_segments)

    e, f = st.columns(2)

    with e:
        st.markdown("### Fleet snapshot")
        if vehicles:
            st.dataframe(vehicles[:20], use_container_width=True)
        else:
            st.info("No vehicle data returned by the backend.")

    with f:
        st.markdown("### Traffic snapshot")
        if traffic:
            st.dataframe(traffic[:20], use_container_width=True)
        else:
            st.info("No traffic data returned by the backend.")

    if overview_data and isinstance(overview_data, dict):
        st.markdown("### Admin summary")
        cols = st.columns(min(4, max(1, len(overview_data))))
        for idx, (key, value) in enumerate(overview_data.items()):
            cols[idx % len(cols)].metric(key.replace("_", " ").title(), value)


def page_mobility_monitor() -> None:
    top_banner()
    st.subheader("Mobility Monitor")
    st.caption("Live visibility for vehicles, traffic conditions, and bus lines.")

    refresh = st.button("Refresh monitor")
    if refresh:
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["Vehicles", "Traffic", "Bus Lines"])

    with tab1:
        vehicles_data = safe_get("/vehicles")
        vehicles = ensure_list(vehicles_data)

        if vehicles:
            search = st.text_input("Filter by vehicle ID, type or status")
            filtered = vehicles

            if search:
                s = search.lower().strip()
                filtered = [
                    v for v in vehicles
                    if s in str(v.get("vehicle_id", "")).lower()
                    or s in str(v.get("vehicle_type", "")).lower()
                    or s in str(v.get("status", "")).lower()
                ]

            st.dataframe(filtered, use_container_width=True)
        else:
            st.info("No vehicle records available.")

    with tab2:
        traffic_data = safe_get("/traffic")
        traffic = ensure_list(traffic_data)

        if traffic:
            level = st.selectbox("Traffic level filter", ["all", "low", "medium", "high"])
            filtered = traffic

            if level != "all":
                filtered = [
                    t for t in traffic
                    if str(t.get("traffic_level", "")).lower() == level
                ]

            st.dataframe(filtered, use_container_width=True)
        else:
            st.info("No traffic records available.")

    with tab3:
        bus_lines_data = safe_get("/bus-lines")
        bus_lines = ensure_list(bus_lines_data)

        if bus_lines:
            st.dataframe(bus_lines, use_container_width=True)
        else:
            st.info("No bus line records available.")


def page_route_and_admin() -> None:
    top_banner()
    st.subheader("Route & Admin")
    st.caption("Route recommendation plus admin operational analytics.")

    left, right = st.columns([1.1, 1])

    with left:
        st.markdown("### Best route recommendation")

        with st.form("route_form"):
            start = st.text_input("Start point / node", placeholder="Example: 4")
            end = st.text_input("End point / node", placeholder="Example: 92")
            submitted = st.form_submit_button("Recommend route", use_container_width=True)

        if submitted:
            if not start or not end:
                st.warning("Enter both start and end points.")
            else:
                result = safe_post(
                    "/routes/recommend",
                    json={"start": start, "end": end}
                )
                if result is not None:
                    st.success("Route generated successfully.")
                    st.json(result)

    with right:
        st.markdown("### Admin analytics")

        if st.session_state.role != "admin":
            st.info("Admin analytics are only visible for admin users.")
        else:
            hotspots = safe_get("/analytics/congestion-hotspots")
            avg_speed = safe_get("/analytics/avg-speed")
            overview = safe_get("/analytics/overview")
            reroutes_data = safe_get("/reroutes")

            hotspot_list = ensure_list(hotspots)
            reroutes = ensure_list(reroutes_data)

            col1, col2 = st.columns(2)
            col1.metric("Congestion Hotspots", len(hotspot_list))

            avg_speed_value = avg_speed
            if isinstance(avg_speed, dict):
                avg_speed_value = (
                    avg_speed.get("avg_speed")
                    or avg_speed.get("average_speed")
                    or str(avg_speed)
                )
            col2.metric("Average Speed", avg_speed_value if avg_speed_value is not None else "N/A")

            st.markdown("#### Overview stats")
            if isinstance(overview, dict):
                st.json(overview)
            else:
                st.info("No overview stats available.")

            st.markdown("#### Congestion hotspots")
            if hotspot_list:
                st.dataframe(hotspot_list, use_container_width=True)
            else:
                st.info("No hotspot data available.")

            st.markdown("#### Reroutes")
            if reroutes:
                st.dataframe(reroutes, use_container_width=True)
            else:
                st.info("No reroute endpoint data available yet.")


def main() -> None:
    page = sidebar_controls()

    if not st.session_state.logged_in:
        login_screen()
        return

    if page == "Overview":
        page_overview()
    elif page == "Mobility Monitor":
        page_mobility_monitor()
    elif page == "Route & Admin":
        page_route_and_admin()


if __name__ == "__main__":
    main()