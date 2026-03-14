# components/charts.py
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

RISK_COLORS = {
    "High":   "#E24B4A",
    "Medium": "#EF9F27",
    "Low":    "#1D9E75",
}


def radar_chart(stats_df: pd.DataFrame) -> go.Figure:
    """
    Spider/radar chart of player skill attributes.
    stats_df must have columns: ball_control, dribbling, stamina,
    reactions, balance, strength, acceleration, potential
    """
    categories = [
        "Ball Control", "Dribbling", "Stamina",
        "Reactions", "Balance", "Strength", "Acceleration", "Potential"
    ]
    col_map = {
        "Ball Control": "ball_control",
        "Dribbling":    "dribbling",
        "Stamina":      "stamina",
        "Reactions":    "reactions",
        "Balance":      "balance",
        "Strength":     "strength",
        "Acceleration": "acceleration",
        "Potential":    "potential",
    }

    row    = stats_df.iloc[0]
    values = [int(row.get(col_map[c], 0)) for c in categories]
    values_closed = values + [values[0]]
    cats_closed   = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor="rgba(55, 138, 221, 0.25)",
        line=dict(color="#378ADD", width=2),
        name=row.get("player_name", "Player"),
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont_size=10),
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=40, r=40),
        height=380,
    )
    return fig


def injury_gauge(risk_prob: float, risk_label: str) -> go.Figure:
    """
    Gauge chart showing injury risk probability 0–100%.
    """
    color = RISK_COLORS.get(risk_label, "#888")
    fig = go.Figure(go.Indicator(
        mode="gauge+delta",
        value=round(risk_prob * 100, 1),
        title={"text": f"Injury Risk — {risk_label}", "font": {"size": 15}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar":  {"color": color},
            "steps": [
                {"range": [0, 40],   "color": "#E1F5EE"},
                {"range": [40, 70],  "color": "#FAEEDA"},
                {"range": [70, 100], "color": "#FAECE7"},
            ],
            "threshold": {
                "line":  {"color": color, "width": 3},
                "thickness": 0.8,
                "value": risk_prob * 100,
            },
        },
    ))
    fig.update_layout(height=280, margin=dict(t=40, b=20, l=20, r=20))
    return fig


def performance_bar(performance_score: float) -> go.Figure:
    """Horizontal bar showing performance score out of 100."""
    color = (
        "#1D9E75" if performance_score >= 70 else
        "#EF9F27" if performance_score >= 45 else
        "#E24B4A"
    )
    fig = go.Figure(go.Bar(
        x=[performance_score],
        y=["Score"],
        orientation="h",
        marker_color=color,
        text=[f"{performance_score:.1f} / 100"],
        textposition="inside",
        textfont=dict(size=14, color="white"),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 100], showgrid=False),
        yaxis=dict(showticklabels=False),
        height=90,
        margin=dict(t=10, b=10, l=10, r=10),
        showlegend=False,
    )
    return fig


def workload_bars(injury_df: pd.DataFrame) -> go.Figure:
    """
    Bar chart of injury-related workload metrics for a single player.
    """
    if injury_df.empty:
        return go.Figure()

    row = injury_df.iloc[0]
    metrics = {
        "Fatigue Index":       row.get("fatigue_index", 0),
        "Training Load":       row.get("training_load", 0),
        "Minutes Played":      row.get("minutes_played", 0) / 10,  # scaled to 0-100
        "Recovery Time (hrs)": row.get("recovery_time", 0),
        "Matches (7 days)":    row.get("matches_last_7_days", 0) * 20,  # scaled
    }

    colors = [
        "#E24B4A" if v > 75 else
        "#EF9F27" if v > 50 else
        "#1D9E75"
        for v in metrics.values()
    ]

    fig = go.Figure(go.Bar(
        x=list(metrics.keys()),
        y=list(metrics.values()),
        marker_color=colors,
        text=[f"{v:.1f}" for v in metrics.values()],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 110], showgrid=True, gridcolor="#f0f0f0"),
        xaxis=dict(tickangle=-15),
        height=320,
        margin=dict(t=20, b=60, l=40, r=20),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def risk_donut(risk_df: pd.DataFrame) -> go.Figure:
    """Donut chart of risk distribution — coach overview."""
    fig = go.Figure(go.Pie(
        labels=risk_df["injury_risk_label"],
        values=risk_df["player_count"],
        hole=0.55,
        marker_colors=[
            RISK_COLORS.get(l, "#888")
            for l in risk_df["injury_risk_label"]
        ],
        textinfo="label+percent",
        textfont_size=13,
    ))
    fig.update_layout(
        height=300,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=False,
    )
    return fig


def performance_histogram(perf_df: pd.DataFrame) -> go.Figure:
    """Histogram of performance scores across all players — coach view."""
    fig = px.histogram(
        perf_df,
        x="performance_score",
        nbins=15,
        color_discrete_sequence=["#378ADD"],
        labels={"performance_score": "Performance Score"},
    )
    fig.update_layout(
        height=300,
        margin=dict(t=20, b=40, l=40, r=20),
        yaxis_title="Players",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def team_risk_bar(team_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar — avg injury risk % per team — coach view."""
    fig = go.Figure(go.Bar(
        x=team_df["avg_injury_risk_pct"],
        y=team_df["team_long_name"],
        orientation="h",
        marker_color=[
            "#E24B4A" if v > 60 else
            "#EF9F27" if v > 35 else
            "#1D9E75"
            for v in team_df["avg_injury_risk_pct"]
        ],
        text=[f"{v}%" for v in team_df["avg_injury_risk_pct"]],
        textposition="outside",
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110]),
        height=max(200, len(team_df) * 50),
        margin=dict(t=10, b=20, l=160, r=60),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig