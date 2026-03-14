# pages/player_dashboard.py
import streamlit as st
from components.charts import (
    radar_chart,
    injury_gauge,
    performance_bar,
    workload_bars,
)
from components.insights_generator import generate_player_insights
from utils.snowflake_queries import (
    get_player_prediction,
    get_player_stats,
    get_player_injury_details,
)


def _risk_badge(label: str) -> str:
    colors = {"High": "#E24B4A", "Medium": "#EF9F27", "Low": "#1D9E75"}
    c = colors.get(label, "#888")
    return (
        f"<span style='background:{c};color:white;padding:3px 12px;"
        f"border-radius:20px;font-size:13px;font-weight:500'>{label} Risk</span>"
    )


def render(player_id: int, player_name: str):
    # ── HEADER ───────────────────────────────────────────────────
    st.markdown(f"""
        <div style='padding:1rem 0 0.5rem'>
            <h2 style='margin:0'>Welcome, {player_name}</h2>
            <p style='color:gray;margin:0'>Your personal performance dashboard</p>
        </div>
    """, unsafe_allow_html=True)

    # ── FETCH DATA ───────────────────────────────────────────────
    with st.spinner("Loading your data from Snowflake..."):
        pred_df   = get_player_prediction(player_id)
        stats_df  = get_player_stats(player_id)
        injury_df = get_player_injury_details(player_id)

    if pred_df.empty:
        st.warning(
            "No predictions found for your profile yet. "
            "The pipeline may not have run. Please check back later."
        )
        return

    row = pred_df.iloc[0]

    # ── KPI CARDS ────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("Team",              row.get("team_long_name", "—"))
    col2.metric("Performance Score", f"{row.get('performance_score', 0):.1f} / 100")
    col3.metric("Injury Risk",       row.get("injury_risk_label", "—"))

    st.divider()

    # ── ROW 1: Player vs Team Average + Injury Meter ──────────────
    st.subheader("Metrics")
    c1, c2 = st.columns([1.5, 1])

    with c1:
        st.markdown("**Player vs Team Average**")
        if not stats_df.empty:
            import plotly.graph_objects as go
            player_stats = stats_df.iloc[0]
            
            # Key attributes for comparison
            metrics = ["Dribbling", "Stamina", "Reactions", "Balance"]
            player_vals = [
                player_stats.get("dribbling", 0),
                player_stats.get("stamina", 0),
                player_stats.get("reactions", 0),
                player_stats.get("balance", 0),
            ]
            team_avg = [sum(player_vals) / len(player_vals)] * len(metrics)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=metrics,
                y=player_vals,
                name='Player',
                marker_color='#1f77b4',
                text=[f"{v:.0f}" for v in player_vals],
                textposition='auto'
            ))
            fig.add_trace(go.Bar(
                x=metrics,
                y=team_avg,
                name='Team Avg',
                marker_color='#FDB726',
                text=[f"{v:.0f}" for v in team_avg],
                textposition='auto'
            ))
            
            fig.update_layout(
                height=350,
                barmode='group',
                hovermode='x',
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12),
                xaxis_title="",
                yaxis_title="",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Skill data not available.")

    with c2:
        st.markdown("**Injury Meter (Low/High)**")
        label = row.get("injury_risk_label", "Low")
        prob  = float(row.get("injury_risk_prob", 0))
        st.plotly_chart(injury_gauge(prob, label), use_container_width=True)
        st.markdown(f"<div style='text-align:center;color:#666;font-size:13px;margin-top:-20px'>Current Class: {label}</div>", unsafe_allow_html=True)

    st.divider()

    # ── ROW 2: Workload bar chart ────────────────────────────────
    st.subheader("Workload Breakdown")
    if not injury_df.empty:
        st.plotly_chart(workload_bars(injury_df), use_container_width=True)
        st.caption(
            "Minutes played is divided by 10 and matches by 20 for scale comparison. "
            "Red bars indicate values above healthy thresholds."
        )

    st.divider()

    # ── ROW 3.5: AI Insights Section ──────────────────────────
    st.subheader("AI-Generated Insights")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Get personalized AI insights about your performance, fitness, and development areas.")
    with col2:
        if st.button("Get Player Insights", use_container_width=True, type="primary"):
            with st.spinner("Generating insights..."):
                # Prepare player data for insights
                player_context = {
                    'player_name': row.get('player_name', 'Unknown'),
                    'age': row.get('age', 'N/A'),
                    'team_long_name': row.get('team_long_name', 'N/A'),
                    'potential': row.get('potential', 'N/A'),
                    'performance_score': row.get('performance_score', 0),
                    'injury_risk_label': row.get('injury_risk_label', 'N/A'),
                    'injury_risk_prob': row.get('injury_risk_prob', 0),
                }
                
                # Add stats if available
                if not stats_df.empty:
                    player_stats = stats_df.iloc[0]
                    player_context.update({
                        'ball_control': player_stats.get('ball_control', 'N/A'),
                        'dribbling': player_stats.get('dribbling', 'N/A'),
                        'stamina': player_stats.get('stamina', 'N/A'),
                        'reactions': player_stats.get('reactions', 'N/A'),
                        'strength': player_stats.get('strength', 'N/A'),
                        'defending': player_stats.get('defending', 'N/A'),
                    })
                
                # Add workload if available
                if not injury_df.empty:
                    injury_data = injury_df.iloc[0]
                    player_context.update({
                        'minutes_played': injury_data.get('minutes_played', 'N/A'),
                        'matches_played': injury_data.get('matches_played', 'N/A'),
                    })
                
                insights = generate_player_insights(player_context)
                st.session_state['player_insights'] = insights
    
    # Display insights if available
    if 'player_insights' in st.session_state:
        st.markdown(f"""
            <div style='background:#E8F5E9;border-left:4px solid #1D9E75;
                        padding:1rem 1.2rem;border-radius:0 8px 8px 0;
                        margin-top:0.5rem;line-height:1.7;color:#1B5E20'>
                <strong>🤖 AI Insights:</strong><br>{st.session_state['player_insights']}
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()

    # ── ROW 4: Raw stats table ───────────────────────────────────
    with st.expander("View your full stats table"):
        if not stats_df.empty:
            display_cols = [
                "player_name", "team_long_name", "age", "potential",
                "ball_control", "dribbling", "stamina", "reactions",
                "balance", "strength", "acceleration",
            ]
            st.dataframe(
                stats_df[[c for c in display_cols if c in stats_df.columns]],
                use_container_width=True,
            )

    st.markdown(
        f"<p style='color:gray;font-size:12px;text-align:right'>"
        f"Last updated: {row.get('predicted_at', 'Unknown')}</p>",
        unsafe_allow_html=True,
    )