
import streamlit as st
import base64
from pathlib import Path


def apply_ui_styling():

    # =========================================================
    # PAGE CONFIGURATION
    # =========================================================

    st.set_page_config(
        page_title="RxInsight - Drug Safety Dashboard",
        layout="wide"
    )

    # =========================================================
    # LOAD PHARMACEUTICAL BACKGROUND IMAGE
    # =========================================================

    background_path = Path(__file__).parent / "rxinsight_background.png"

    if background_path.exists():

        with open(background_path, "rb") as image_file:
            encoded_background = base64.b64encode(
                image_file.read()
            ).decode()

        background_image = (
            f"data:image/png;base64,{encoded_background}"
        )

    else:
        background_image = ""

    # =========================================================
    # CUSTOM CSS
    # =========================================================

    st.markdown(
        f"""
        <style>

        /* =====================================================
           💊 MAIN RXINSIGHT BACKGROUND
           ===================================================== */

        .stApp {{
            min-height: 100vh;

            background-image:
                linear-gradient(
                    135deg,
                    rgba(224, 238, 247, 0.82),
                    rgba(235, 232, 246, 0.78),
                    rgba(224, 242, 241, 0.80),
                    rgba(241, 232, 239, 0.78)
                ),
                url("{background_image}");

            background-size:
                300% 300%,
                cover;

            background-position:
                0% 50%,
                center;

            background-attachment:
                fixed,
                fixed;

            animation:
                rxGradientMove 24s ease-in-out infinite;
        }}


        /* =====================================================
           🌈 SLOW COLOR ANIMATION
           ===================================================== */

        @keyframes rxGradientMove {{

            0% {{
                background-position:
                    0% 50%,
                    center;
            }}

            25% {{
                background-position:
                    50% 100%,
                    center;
            }}

            50% {{
                background-position:
                    100% 50%,
                    center;
            }}

            75% {{
                background-position:
                    50% 0%,
                    center;
            }}

            100% {{
                background-position:
                    0% 50%,
                    center;
            }}
        }}


        /* =====================================================
           📐 MAIN CONTENT
           ===================================================== */

        .block-container {{
            max-width: 1200px;

            padding-top: 2rem;
            padding-bottom: 3rem;
        }}


        /* =====================================================
           🧬 HEADINGS
           ===================================================== */

        h1,
        h2,
        h3,
        h4 {{
            font-weight: 700;
        }}


        /* =====================================================
           📊 STREAMLIT METRICS
           ===================================================== */

        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.91);

            padding: 16px;

            border-radius: 12px;

            box-shadow:
                0 4px 16px rgba(15, 23, 42, 0.09);

            backdrop-filter: blur(10px);

            -webkit-backdrop-filter: blur(10px);
        }}


        /* =====================================================
           📦 EXPANDERS
           ===================================================== */

        [data-testid="stExpander"] {{
            background: rgba(255, 255, 255, 0.89);

            border-radius: 10px;

            border:
                1px solid rgba(213, 222, 231, 0.85);

            margin-bottom: 8px;

            backdrop-filter: blur(10px);

            -webkit-backdrop-filter: blur(10px);
        }}


        /* =====================================================
           🔲 COMPACT METRIC SQUARES
           ===================================================== */

        .metric-square-container {{
            display: grid;

            grid-template-columns:
                repeat(auto-fit, minmax(150px, 200px));

            gap: 16px;

            margin:
                0.8rem 0 1.4rem 0;
        }}


        .metric-square {{
            background: rgba(255, 255, 255, 0.93);

            border:
                1px solid rgba(213, 222, 231, 0.85);

            border-radius: 14px;

            aspect-ratio: 1 / 1;

            max-width: 200px;

            width: 100%;

            display: flex;

            flex-direction: column;

            justify-content: center;

            align-items: center;

            text-align: center;

            padding: 16px;

            box-shadow:
                0 4px 14px rgba(15, 23, 42, 0.07);

            backdrop-filter: blur(10px);

            -webkit-backdrop-filter: blur(10px);

            transition:
                transform 0.18s ease,
                box-shadow 0.18s ease,
                border-color 0.18s ease;
        }}


        /* =====================================================
           ✨ METRIC HOVER
           ===================================================== */

        .metric-square:hover {{

            transform:
                translateY(-3px)
                scale(1.01);

            border-color:
                #8b5cf6;

            box-shadow:
                0 10px 25px
                rgba(79, 70, 229, 0.14);
        }}


        /* =====================================================
           METRIC TEXT
           ===================================================== */

        .metric-square-title {{

            font-size:
                0.88rem;

            font-weight:
                700;

            color:
                #475569;

            text-transform:
                uppercase;

            letter-spacing:
                0.04em;

            margin-bottom:
                6px;
        }}


        .metric-square-val {{

            font-size:
                2.2rem;

            font-weight:
                800;

            color:
                #0f172a;

            line-height:
                1.1;
        }}


        .metric-square-sub {{

            font-size:
                0.92rem;

            color:
                #2563eb;

            font-weight:
                600;

            margin-top:
                6px;
        }}


        /* =====================================================
           🖱️ RXINSIGHT CURSOR
           ===================================================== */

        html,
        body,
        .stApp {{
            cursor: crosshair;
        }}


        /* Interactive elements */

        button,
        a,
        input,
        textarea,
        select,
        [role="button"],
        [data-baseweb="select"],
        .stButton > button {{
            cursor: pointer !important;
        }}


        </style>
        """,
        unsafe_allow_html=True,
    )

