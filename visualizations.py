import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import config


# ============================================================
# FIXED COLORS FOR THE FIRST FIVE NON-3D GRAPHS
# ============================================================
# 1 = Black
# 2 = Red
# 3 = Blue
# 4 = Green
# 5 = Pink

GRAPH_COLORS = [
    "#000000",  # 1. Black
    "#D50000",  # 2. Red
    "#1565C0",  # 3. Blue
    "#00A152",  # 4. Green
    "#E91E63",  # 5. Pink
]


# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
# Use dictionary-style access instead of attribute-style access.
# This is more robust on Streamlit Cloud and prevents
# AttributeError when the state does not exist yet.

if "rx_timeline_color_registry" not in st.session_state:
    st.session_state["rx_timeline_color_registry"] = {}

if "rx_timeline_color_index" not in st.session_state:
    st.session_state["rx_timeline_color_index"] = 0


# ============================================================
# TIMELINE COLOR HELPER
# ============================================================

def _get_timeline_color(key: str) -> str:
    """
    Give each non-3D timeline graph one fixed color.

    The first five unique timeline graphs receive:
    1. Black
    2. Red
    3. Blue
    4. Green
    5. Pink

    The color remains stable during Streamlit reruns.
    """

    key = str(key)

    registry = st.session_state["rx_timeline_color_registry"]
    color_index = st.session_state["rx_timeline_color_index"]

    # If this graph does not yet have a color,
    # assign the next color in the palette.
    if key not in registry:

        color = GRAPH_COLORS[color_index % len(GRAPH_COLORS)]

        registry[key] = color

        st.session_state["rx_timeline_color_index"] = color_index + 1

    return registry[key]


# ============================================================
# TIMELINE CHART
# ============================================================

def timeline_chart(
    df,
    title: str,
    key: str,
    granularity: str,
    selection_message: str
):
    """
    Create one interactive timeline bar chart.

    The first five non-3D timeline charts receive fixed colors:
    black, red, blue, green, pink.
    """

    graph_color = _get_timeline_color(key)

    fig = px.bar(
        df,
        x="Period",
        y="Reports",
        title=title,
        labels={
            "Period": granularity,
            "Reports": "Number of Reports"
        },
        custom_data=["Period"],
    )

    # ========================================================
    # COLOR ONLY THE NON-3D TIMELINE GRAPHS
    # ========================================================

    fig.update_traces(
        marker=dict(
            color=graph_color,
            line=dict(
                color="rgba(0,0,0,0.35)",
                width=1,
            ),
        )
    )

    fig.update_layout(
        height=500,
        hovermode="x unified",
        margin=dict(
            l=20,
            r=20,
            t=70,
            b=60
        ),
    )

    st.info(selection_message)

    return st.plotly_chart(
        fig,
        width="stretch",
        on_select="rerun",
        selection_mode="points",
        key=key,
    )


# ============================================================
# METRIC SQUARES
# ============================================================

def render_metric_squares(data_list: list):
    """
    Render compact square metric cards with large bold numbers.
    """

    cards = "".join(
        f'<div class="metric-square">'
        f'<div class="metric-square-title">{item["title"]}</div>'
        f'<div class="metric-square-val">{item["value"]}</div>'
        f'<div class="metric-square-sub">{item["sub"]}</div>'
        f'</div>'
        for item in data_list
    )

    st.markdown(
        f'<div class="metric-square-container">{cards}</div>',
        unsafe_allow_html=True
    )


# ============================================================
# 3D BALLOON MATRIX
# ============================================================
# IMPORTANT:
# This section is intentionally kept as it was.
# The 3D colors and balloon design are NOT controlled by
# GRAPH_COLORS and are NOT affected by the timeline colors.

def render_3d_matrix(
    df_3d_agg,
    top10_fx: list,
    search_drug: str
):
    fig_3d = go.Figure()

    colors = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728"
    ]

    UNIFORM_BALLOON_SIZE = 8

    for idx, cat in enumerate(config.POLY_ORDER):

        c_df = df_3d_agg[
            df_3d_agg["Polypharmacy Category"] == cat
        ]

        if c_df.empty:
            continue

        fig_3d.add_trace(
            go.Scatter3d(
                x=c_df["Polypharmacy Category"],
                y=c_df["Adverse Effect"],
                z=c_df["Death Percentage (%)"],
                mode="markers",
                name=cat,

                marker=dict(
                    size=UNIFORM_BALLOON_SIZE,
                    color=colors[idx % len(colors)],
                    opacity=0.92,
                    line=dict(
                        width=1.5,
                        color="rgba(0,0,0,0.7)"
                    ),
                ),

                customdata=c_df[
                    ["Reports", "Death"]
                ],

                hovertemplate=(
                    "<b>Tier:</b> %{x}<br>"
                    "<b>Effect:</b> %{y}<br>"
                    "<b>Death Rate:</b> %{z:.1f}%<br>"
                    "<b>Reports:</b> %{customdata[0]:,}<br>"
                    "<b>Fatalities:</b> %{customdata[1]:,}"
                    "<extra></extra>"
                ),
            )
        )

    fig_3d.update_layout(
        title=(
            f"3D Multidimensional Polypharmacy "
            f"& Fatality Matrix: {search_drug}"
        ),

        scene=dict(
            xaxis_title="Pharmacy Group",
            yaxis_title="Top 10 Adverse Effects",
            zaxis_title="Death %",

            xaxis=dict(
                type="category"
            ),

            yaxis=dict(
                type="category",
                categoryorder="array",
                categoryarray=top10_fx,
                tickmode="array",
                tickvals=top10_fx,
                ticktext=top10_fx,
                dtick=1,
                tickfont=dict(size=10),
            ),
        ),

        height=750,

        margin=dict(
            l=0,
            r=0,
            b=0,
            t=50
        ),

        legend=dict(
            title="<b>Pharmacy Tiers</b>",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ),
    )

    st.plotly_chart(
        fig_3d,
        width="stretch",
        key="balloon_3d_final"
    )