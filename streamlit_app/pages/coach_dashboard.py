# pages/coach_dashboard.py
import streamlit as st
import pandas as pd
from components.charts import (
    radar_chart,
    injury_gauge,
    performance_bar,
    workload_bars,
    risk_donut,
    performance_histogram,
    team_risk_bar,
)
from components.insights_generator import generate_team_insights
from utils.snowflake_queries import (
    get_all_players_summary,
    get_risk_distribution,
    get_performance_distribution,
    get_team_stats_overview,
    get_player_prediction,
    get_player_stats,
    get_player_injury_details,
    get_all_teams,
    get_team_players,
    get_team_summary,
)

RISK_COLORS = {"High": "#E24B4A", "Medium": "#EF9F27", "Low": "#1D9E75"}


def _risk_badge(label: str) -> str:
    c = RISK_COLORS.get(label, "#888")
    return (
        f"<span style='background:{c};color:white;padding:3px 12px;"
        f"border-radius:20px;font-size:13px;font-weight:500'>{label} Risk</span>"
    )


def _player_detail_panel(player_id: int, player_name: str):
    """Renders the full detail view when a coach searches/selects a player."""
    st.markdown(f"### {player_name} — Full Profile")

    pred_df   = get_player_prediction(player_id)
    stats_df  = get_player_stats(player_id)
    injury_df = get_player_injury_details(player_id)

    if pred_df.empty:
        st.warning("No prediction data found for this player.")
        return

    row   = pred_df.iloc[0]
    label = row.get("injury_risk_label", "Low")
    prob  = float(row.get("injury_risk_prob", 0))
    score = float(row.get("performance_score", 0))

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Team",        row.get("team_long_name", "—"))
    k2.metric("Perf Score",  f"{score:.1f}/100")
    k3.metric("Injury Risk", label)
    k4.metric("Risk Prob",   f"{prob*100:.1f}%")

    # Charts row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Performance score**")
        st.plotly_chart(performance_bar(score), use_container_width=True)
        if not stats_df.empty:
            st.markdown("**Skill radar**")
            st.plotly_chart(radar_chart(stats_df), use_container_width=True)

    with c2:
        st.markdown(
            f"**Injury risk** &nbsp; {_risk_badge(label)}",
            unsafe_allow_html=True,
        )
        st.plotly_chart(injury_gauge(prob, label), use_container_width=True)

    with c3:
        if not injury_df.empty:
            irow = injury_df.iloc[0]
            st.markdown("**Load metrics**")
            st.markdown(f"""
            | Metric | Value |
            |---|---|
            | Fatigue index | `{irow.get('fatigue_index', 0):.1f}` |
            | Training load | `{irow.get('training_load', 0):.1f}` |
            | Minutes played | `{int(irow.get('minutes_played', 0))}` |
            | Matches (7d) | `{int(irow.get('matches_last_7_days', 0))}` |
            | Recovery time | `{irow.get('recovery_time', 0):.1f} hrs` |
            | Prev injury | `{'Yes' if irow.get('previous_injury', 0) else 'No'}` |
            """)

    # Workload chart
    if not injury_df.empty:
        st.markdown("**Workload breakdown**")
        st.plotly_chart(workload_bars(injury_df), use_container_width=True)

    # Recommendation
    rec = row.get("recommendation", "No recommendation available.")
    bg     = {"High": "#FAECE7", "Medium": "#FAEEDA", "Low": "#E1F5EE"}.get(label, "#F1EFE8")
    border = RISK_COLORS.get(label, "#888")
    st.markdown("**Coaching recommendation**")
    st.markdown(f"""
        <div style='background:{bg};border-left:4px solid {border};
                    padding:1rem 1.2rem;border-radius:0 8px 8px 0;line-height:1.7'>
            {rec}
        </div>
    """, unsafe_allow_html=True)

    st.markdown(
        f"<p style='color:gray;font-size:12px;text-align:right;margin-top:8px'>"
        f"Predicted at: {row.get('predicted_at', '—')}</p>",
        unsafe_allow_html=True,
    )


def render(coach_name: str):
    # ── HEADER ───────────────────────────────────────────────────
    st.markdown(f"""
        <div style='padding:1rem 0 0.5rem'>
            <h2 style='margin:0'>Coach Dashboard</h2>
            <p style='color:gray;margin:0'>Welcome, {coach_name}</p>
        </div>
    """, unsafe_allow_html=True)

    # ── TEAM SELECTOR ────────────────────────────────────────────
    st.markdown("### Select Your Team")
    
    with st.spinner("Loading teams..."):
        teams_df = get_all_teams()
    
    team_options = teams_df.to_dict('records')
    team_labels = [f"{t['team_long_name']} ({t['total_players']} players)" for t in team_options]
    
    selected_team_idx = st.selectbox(
        "Choose a team to manage:",
        range(len(team_options)),
        format_func=lambda i: team_labels[i],
        key="coach_team_selector"
    )
    
    selected_team = team_options[selected_team_idx]
    team_id = selected_team['team_id']
    team_name = selected_team['team_long_name']
    
    # Display selected team info
    st.info(f"📊 Currently managing: **{team_name}** (ID: {team_id})")
    
    st.divider()

    # ── TABS ─────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs([
        "Team Performance",
        "Team Players",
        "Player Search",
    ])

    # ════════════════════════════════════════════════════════════
    # TAB 1 — TEAM PERFORMANCE
    # ════════════════════════════════════════════════════════════
    with tab1:
        with st.spinner(f"Loading {team_name} performance data..."):
            team_summary = get_team_summary(team_id)
        
        if not team_summary.empty:
            summary = team_summary.iloc[0]
            
            st.markdown(f"## {team_name} — Performance Overview")
            
            # Team KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Players", summary['total_players'])
            k2.metric("Avg Performance", f"{summary['avg_performance']:.1f}/100")
            k3.metric("High Risk Count", int(summary['high_risk_players']))
            k4.metric("Low Risk Count", int(summary['low_risk_players']))
            
            st.divider()
            
            # AI Insights Section
            col_insights1, col_insights2 = st.columns([3, 1])
            with col_insights1:
                st.write("**Get AI-Generated Team Insights** — Strategic analysis of your team's performance, injury status, and focus areas.")
            with col_insights2:
                if st.button("Get Team Insights", use_container_width=True, type="primary"):
                    with st.spinner("Generating team insights..."):
                        # Prepare aggregated team summary for insights (scalable approach)
                        team_context = {
                            'team_long_name': team_name,
                            'total_players': summary['total_players'],
                            'avg_performance': summary['avg_performance'],
                            'min_performance': summary['min_performance'],
                            'max_performance': summary['max_performance'],
                            'high_risk_players': int(summary['high_risk_players']),
                            'medium_risk_players': int(summary['medium_risk_players']),
                            'low_risk_players': int(summary['low_risk_players']),
                            'high_performers': int(summary.get('high_performers', 0)),
                            'mid_performers': int(summary.get('mid_performers', 0)),
                            'low_performers': int(summary.get('low_performers', 0)),
                        }
                        
                        insights = generate_team_insights(team_context)
                        st.session_state['team_insights'] = insights
            
            # Display team insights if available
            if 'team_insights' in st.session_state:
                st.markdown(f"""
                    <div style='background:#E3F2FD;border-left:4px solid #1976D2;
                                padding:1rem 1.2rem;border-radius:0 8px 8px 0;
                                margin-top:0.5rem;line-height:1.7;color:#0D47A1'>
                        <strong>🤖 Team Insights:</strong><br>{st.session_state['team_insights']}
                    </div>
                """, unsafe_allow_html=True)
            
            st.divider()
            
            # Team Stats
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Risk Distribution")
                risk_data = {
                    "High": summary['high_risk_players'],
                    "Medium": summary['medium_risk_players'],
                    "Low": summary['low_risk_players']
                }
                st.bar_chart(risk_data)
            
            with col2:
                st.markdown("### Performance Distribution")
                perf_range = {
                    "Min": summary['min_performance'],
                    "Avg": summary['avg_performance'],
                    "Max": summary['max_performance']
                }
                st.bar_chart(perf_range)
            
            st.divider()
            
            st.markdown("### Team Squad Details")
            
            # Team squad table
            with st.spinner("Loading squad details..."):
                squad_df = get_team_players(team_id)
            
            if not squad_df.empty:
                display_squad = squad_df[[
                    "player_name", "age", "potential",
                    "performance_score",
                    "injury_risk_label"
                ]].copy()
                display_squad.columns = [
                    "Player Name", "Age", "Potential",
                    "Performance", "Injury Risk"
                ]
                
                def color_risk(val):
                    if isinstance(val, str):
                        if val == "High":
                            return "color: #E24B4A"
                        elif val == "Medium":
                            return "color: #EF9F27"
                        else:
                            return "color: #1D9E75"
                    return ""
                
                st.dataframe(
                    display_squad.style.applymap(color_risk, subset=["Injury Risk"]),
                    use_container_width=True,
                    height=500,
                )
        else:
            st.warning(f"No data available for {team_name}")
    
    # ════════════════════════════════════════════════════════════
    # TAB 2 — TEAM PLAYERS
    # ════════════════════════════════════════════════════════════
    with tab2:
        st.markdown(f"## {team_name} — Squad Analysis")
        
        with st.spinner(f"Loading {team_name} players..."):
            team_players = get_team_players(team_id)
        
        if not team_players.empty:
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                risk_filter = st.multiselect(
                    "Filter by Risk Level:",
                    ["High", "Medium", "Low"],
                    default=["High", "Medium", "Low"]
                )
            
            with col2:
                min_perf = st.slider("Min Performance Score:", 0, 100, 0)
            
            with col3:
                max_perf = st.slider("Max Performance Score:", 0, 100, 100)
            
            # Apply filters
            filtered_players = team_players[
                (team_players['injury_risk_label'].isin(risk_filter)) &
                (team_players['performance_score'] >= min_perf) &
                (team_players['performance_score'] <= max_perf)
            ]
            
            st.markdown(f"**Found {len(filtered_players)} players matching criteria**")
            
            # Display players
            for idx, player in filtered_players.iterrows():
                with st.expander(f"{player['player_name']} — Age {player['age']}, Potential {player['potential']}"):
                    p_col1, p_col2, p_col3 = st.columns(3)
                    p_col1.metric("Performance", f"{player['performance_score']:.1f}/100")
                    p_col2.metric("Risk Level", player['injury_risk_label'])
                    p_col3.metric("Risk %", f"{player['injury_risk_pct']:.1f}%")
                    
                    # Show full profile
                    if st.button(f"View full profile", key=f"view_player_{player['player_id']}"):
                        _player_detail_panel(player['player_id'], player['player_name'])
        else:
            st.warning(f"No players found for {team_name}")

    # ════════════════════════════════════════════════════════════
    # TAB 3 — PLAYER SEARCH
    # ════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("Search for any player to view their full profile, predictions, and charts.")

        with st.spinner("Fetching player list..."):
            all_players_df = get_all_players_summary()

        if all_players_df.empty:
            st.warning("No player data found.")
        else:
            # Search box
            search_term = st.text_input(
                "Search player name",
                placeholder="e.g. De Bruyne, Pedri...",
            )

            filtered = all_players_df
            if search_term:
                filtered = all_players_df[
                    all_players_df["player_name"]
                    .str.lower()
                    .str.contains(search_term.lower(), na=False)
                ]

            if filtered.empty:
                st.info("No players found matching your search.")
            else:
                # Player picker
                player_options = dict(
                    zip(filtered["player_name"], filtered["player_id"])
                )
                selected_name = st.selectbox(
                    "Select a player",
                    options=list(player_options.keys()),
                )

                if st.button("Load Player Profile", type="primary"):
                    st.session_state["selected_player_id"]   = player_options[selected_name]
                    st.session_state["selected_player_name"] = selected_name

                # Render profile if one is selected
                if (
                    "selected_player_id" in st.session_state
                    and "selected_player_name" in st.session_state
                ):
                    st.divider()
                    _player_detail_panel(
                        st.session_state["selected_player_id"],
                        st.session_state["selected_player_name"],
                    )