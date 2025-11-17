import sqlite3
import textwrap
import json
from typing import Dict, List

import pandas as pd
import streamlit as st
import requests

# =========================
# Page config & base styles
# =========================

st.set_page_config(
    page_title="THE XXX AD POSTER",
    page_icon="🔥",
    layout="wide",
)

APP_CSS = """
<style>
body, .stApp {
    background-color: #050506;
    color: #f5f5f5;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.block-container { padding-top: 1.5rem; }

/* Header */
.xxx-header {
    text-align:center;
    padding: 0.75rem 0 0.25rem 0;
}
.xxx-logo {
    font-size: 3.5rem;
    text-shadow:
        0 0 8px rgba(255,80,140,0.7),
        0 0 16px rgba(255,0,90,0.5);
}
.xxx-title {
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #ff4d94;
    text-shadow:
        0 0 8px rgba(255,80,140,0.9),
        0 0 16px rgba(255,0,90,0.7);
}
.xxx-subtitle {
    font-size: 0.95rem;
    opacity: 0.85;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: radial-gradient(circle at top, #240016 0%, #050506 55%, #000 100%);
}
.sidebar-logo {
    text-align:center;
    font-size: 1rem;
    font-weight: 700;
    margin: 0.75rem 0 1.2rem 0;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    padding: 0.6rem 0.4rem;
    border-radius: 14px;
    background: radial-gradient(circle at 30% 0%, #3c001a 0%, #050506 55%, #000 100%);
    border: 1px solid rgba(255,80,140,0.45);
    box-shadow:
        0 0 10px rgba(255,80,140,0.4),
        0 0 18px rgba(0,0,0,0.9),
        inset 0 0 6px rgba(0,0,0,0.7);
}

/* Cards */
.xxx-card {
    border-radius: 14px;
    border: 1px solid rgba(255,80,140,0.55);
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.9rem;
    background: radial-gradient(circle at top, #171217 0%, #050506 55%, #000 100%);
    box-shadow:
        0 0 10px rgba(255,80,140,0.35),
        0 0 23px rgba(0,0,0,0.9);
}
.xxx-card h3 {
    margin-top: 0;
}

/* Buttons */
div.stButton > button {
    border-radius: 999px;
    border: 1px solid #ff8fc0;
    background: linear-gradient(135deg, #ff4d94, #c40052);
    color: #ffffff;
    font-weight: 600;
    padding: 0.35rem 1.1rem;
    box-shadow: 0 0 14px rgba(255,77,148,0.7);
}
div.stButton > button:hover {
    border-color: #ffffff;
    box-shadow:
        0 0 18px rgba(255,143,192,0.9),
        0 0 26px rgba(255,0,90,0.7);
}

/* Login card */
.login-card {
    max-width: 440px;
    margin: 0 auto;
    padding: 1.25rem 1.4rem;
    border-radius: 14px;
    border: 1px solid rgba(255,80,140,0.55);
    background: radial-gradient(circle at top, #171217 0%, #050506 55%, #000 100%);
    box-shadow:
        0 0 18px rgba(255,80,140,0.35),
        0 0 26px rgba(0,0,0,0.95);
}
.login-title {
    text-align:center;
    font-weight: 700;
    color: #ff4d94;
    margin-bottom: 0.6rem;
}

/* Footer */
.xxx-footer {
    text-align:center;
    font-size: 0.8rem;
    color: #aaaaaa;
    margin-top: 2.8rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255,80,140,0.45);
    opacity: 0.9;
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)


# =========================
# DB helpers (SQLite)
# =========================

DB_PATH = "xxx_ad_poster.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table: str, col_name: str, col_def: str):
    """Add column if it does not exist (for upgrades)."""
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    cols = [row[1] for row in cur.fetchall()]
    if col_name not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    # Programs
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS affiliate_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            niche TEXT,
            geo_focus TEXT,
            signup_url TEXT NOT NULL,
            status TEXT,
            notes TEXT
        )
        """
    )

    # Ads (with traffic_source + campaign_notes)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_creatives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            title TEXT,
            angle TEXT,
            headline TEXT,
            body TEXT,
            call_to_action TEXT,
            placement_type TEXT,
            traffic_source TEXT,
            campaign_notes TEXT,
            FOREIGN KEY (program_id) REFERENCES affiliate_programs (id)
        )
        """
    )

    # Performance (with impressions + revenue)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ad_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id INTEGER NOT NULL UNIQUE,
            impressions INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            leads INTEGER DEFAULT 0,
            sales INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0.0,
            FOREIGN KEY (ad_id) REFERENCES ad_creatives (id)
        )
        """
    )

    # Ensure new columns exist if DB is older
    ensure_column(conn, "ad_creatives", "traffic_source", "TEXT")
    ensure_column(conn, "ad_creatives", "campaign_notes", "TEXT")
    ensure_column(conn, "ad_performance", "impressions", "INTEGER DEFAULT 0")
    ensure_column(conn, "ad_performance", "revenue", "REAL DEFAULT 0.0")

    conn.commit()
    conn.close()


def fetch_programs() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM affiliate_programs ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_program(name, niche, geo_focus, signup_url, status, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO affiliate_programs (name, niche, geo_focus, signup_url, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, niche, geo_focus, signup_url, status, notes),
    )
    conn.commit()
    conn.close()


def get_program_by_id(pid: int) -> Dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM affiliate_programs WHERE id = ?", (pid,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else {}


def fetch_ads() -> List[sqlite3.Row]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT a.*, p.name AS program_name
        FROM ad_creatives a
        LEFT JOIN affiliate_programs p ON a.program_id = p.id
        ORDER BY a.id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_ad(
    program_id,
    title,
    angle,
    headline,
    body,
    call_to_action,
    placement_type,
    traffic_source,
    campaign_notes,
) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ad_creatives (
            program_id, title, angle, headline, body,
            call_to_action, placement_type, traffic_source, campaign_notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            program_id,
            title,
            angle,
            headline,
            body,
            call_to_action,
            placement_type,
            traffic_source,
            campaign_notes,
        ),
    )
    ad_id = cur.lastrowid

    # initialize performance row
    cur.execute(
        """
        INSERT OR IGNORE INTO ad_performance (ad_id, impressions, clicks, leads, sales, revenue)
        VALUES (?, 0, 0, 0, 0, 0.0)
        """,
        (ad_id,),
    )

    conn.commit()
    conn.close()
    return ad_id


def get_performance_for_ad(ad_id: int) -> Dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM ad_performance WHERE ad_id = ?",
        (ad_id,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "ad_id": ad_id,
        "impressions": 0,
        "clicks": 0,
        "leads": 0,
        "sales": 0,
        "revenue": 0.0,
    }


def update_performance(
    ad_id: int,
    impressions: int,
    clicks: int,
    leads: int,
    sales: int,
    revenue: float,
):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO ad_performance (ad_id, impressions, clicks, leads, sales, revenue)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(ad_id) DO UPDATE SET
            impressions = excluded.impressions,
            clicks = excluded.clicks,
            leads = excluded.leads,
            sales = excluded.sales,
            revenue = excluded.revenue
        """,
        (ad_id, impressions, clicks, leads, sales, revenue),
    )
    conn.commit()
    conn.close()


def fetch_programs_df() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM affiliate_programs ORDER BY id", conn)
    conn.close()
    return df


def fetch_ads_with_metrics_df() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        """
        SELECT
            a.id AS ad_id,
            a.title,
            a.angle,
            a.headline,
            a.body,
            a.call_to_action,
            a.placement_type,
            a.traffic_source,
            a.campaign_notes,
            p.name AS program_name,
            perf.impressions,
            perf.clicks,
            perf.leads,
            perf.sales,
            perf.revenue
        FROM ad_creatives a
        LEFT JOIN affiliate_programs p ON a.program_id = p.id
        LEFT JOIN ad_performance perf ON perf.ad_id = a.id
        ORDER BY a.id
        """,
        conn,
    )
    conn.close()
    return df


# =========================
# Session-state helpers
# =========================

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if "zapier_webhook_url" not in st.session_state:
    st.session_state["zapier_webhook_url"] = ""


# =========================
# UI Helpers
# =========================

def render_header():
    st.markdown(
        """
        <div class="xxx-header">
            <div class="xxx-logo">🔥</div>
            <div class="xxx-title">THE XXX AD POSTER</div>
            <div class="xxx-subtitle">
                Manage affiliate programs, track performance & build clean ad creatives for adult offers.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")


def render_footer():
    st.markdown(
        """
        <div class="xxx-footer">
            © 2025 THE XXX AD POSTER · Built with Python + Streamlit.<br/>
            No passwords or sensitive data should be stored here – use it as a planning toolkit.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Auth
# =========================

def login_page():
    render_header()
    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔒 Creator Login</div>', unsafe_allow_html=True)

    username = st.text_input("Username", placeholder="admin")
    password = st.text_input("Password", type="password")

    if st.button("Log In"):
        admin_user = st.secrets.get("ADMIN_USERNAME", "admin")
        admin_pw = st.secrets.get("ADMIN_PASSWORD", "xxx-poster")

        if username == admin_user and password == admin_pw:
            st.session_state["auth_ok"] = True
            st.success("Access granted. Loading THE XXX AD POSTER…")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials.")

    st.markdown("</div>", unsafe_allow_html=True)
    render_footer()


# =========================
# Zapier helper
# =========================

def trigger_zap(event_name: str, payload: Dict):
    """
    Send a JSON payload to a Zapier Catch Hook.

    Priority:
    1) st.secrets["ZAPIER_WEBHOOK_URL"]
    2) st.session_state["zapier_webhook_url"]
    """
    url = st.secrets.get("ZAPIER_WEBHOOK_URL") or st.session_state.get(
        "zapier_webhook_url", ""
    )
    if not url:
        return
    data = {"event": event_name, **payload}
    try:
        requests.post(url, json=data, timeout=3)
    except Exception as e:
        st.warning(f"Zapier webhook error: {e}")


# =========================
# Ad text generator (local)
# =========================

def generate_ad_from_brief(
    offer_name: str,
    offer_type: str,
    audience: str,
    promise: str,
    hook_style: str,
) -> Dict[str, str]:
    """
    Simple, rule-based generator for short adult-friendly ads.
    All language is non-explicit and focuses on benefits, privacy, and discretion.
    """
    if not audience.strip():
        audience = "adults who want a more exciting private life"

    if not promise.strip():
        promise = "add more fun and excitement without drama"

    if offer_type.lower() in ["toys", "toy", "products"]:
        category_phrase = "adult products"
    elif offer_type.lower() in ["cams", "live"]:
        category_phrase = "live entertainment"
    elif offer_type.lower() in ["dating", "meets"]:
        category_phrase = "adults-only connections"
    else:
        category_phrase = "adult offers"

    if hook_style == "Curiosity":
        headline = f"This {offer_type.title()} Offer Is Making Adults Smile"
    elif hook_style == "Discreet / Privacy":
        headline = "100% Discreet · For Adults Only"
    elif hook_style == "Limited-Time":
        headline = f"{offer_type.title()} Deals Ending Soon"
    elif hook_style == "Audience-Focused":
        headline = f"New For {audience.capitalize()}"
    else:
        headline = f"Explore Trusted {category_phrase.title()}"

    body_lines = [
        f"{offer_name} is for {audience} who want to {promise}.",
        f"Browse trusted {category_phrase} with fast, discreet service.",
        "No pressure, no drama — just adults choosing what works for them.",
    ]
    body = " ".join(body_lines)

    cta = "Tap to explore today’s offers."

    return {
        "headline": headline,
        "body": textwrap.fill(body, width=70),
        "cta": cta,
    }


# =========================
# AI-powered generator
# =========================

def generate_ad_with_ai(
    provider: str,
    offer_name: str,
    offer_type: str,
    audience: str,
    promise: str,
    hook_style: str,
) -> Dict[str, str]:
    """
    Use OpenAI / Claude / Gemini if keys are configured.
    Falls back to local generator if anything fails.
    """
    base = generate_ad_from_brief(offer_name, offer_type, audience, promise, hook_style)

    if provider == "Built-in (no API)":
        return base

    brief = f'''
You are an experienced adult affiliate copywriter. Write a short, non-explicit ad
for an adult offer. Focus on benefits, privacy, and discretion. NO explicit words.

Offer name: {offer_name}
Offer type: {offer_type}
Audience: {audience}
Main promise: {promise}
Hook style: {hook_style}

Return ONLY valid JSON with keys: headline, body, cta.
'''

    try:
        if provider == "OpenAI":
            api_key = st.secrets.get("OPENAI_API_KEY")
            if not api_key:
                return base
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": "gpt-4.1-mini",
                "messages": [
                    {"role": "system", "content": "You write short, clean ad copy."},
                    {"role": "user", "content": brief.strip()},
                ],
                "temperature": 0.7,
            }
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return {
                "headline": parsed.get("headline", base["headline"]),
                "body": parsed.get("body", base["body"]),
                "cta": parsed.get("cta", base["cta"]),
            }

        elif provider == "Claude (Anthropic)":
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
            if not api_key:
                return base
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 400,
                "messages": [
                    {"role": "user", "content": brief.strip()},
                ],
            }
            resp = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=20,
            )
            data = resp.json()
            text_blocks = [
                block.get("text", "")
                for block in data.get("content", [])
                if block.get("type") == "text"
            ]
            content = "".join(text_blocks)
            parsed = json.loads(content)
            return {
                "headline": parsed.get("headline", base["headline"]),
                "body": parsed.get("body", base["body"]),
                "cta": parsed.get("cta", base["cta"]),
            }

        elif provider == "Gemini":
            api_key = st.secrets.get("GEMINI_API_KEY")
            if not api_key:
                return base
            url = (
                "https://generativelanguage.googleapis.com/v1beta/"
                "models/gemini-1.5-flash:generateContent"
            )
            params = {"key": api_key}
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": brief.strip()}
                        ]
                    }
                ]
            }
            resp = requests.post(url, params=params, json=payload, timeout=20)
            data = resp.json()
            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            parsed = json.loads(text)
            return {
                "headline": parsed.get("headline", base["headline"]),
                "body": parsed.get("body", base["body"]),
                "cta": parsed.get("cta", base["cta"]),
            }
        else:
            return base
    except Exception as e:
        st.warning(f"AI generation failed ({provider}): {e}")
        return base


# =========================
# Pages
# =========================

def page_dashboard():
    render_header()
    col1, col2 = st.columns([1.3, 1])

    with col1:
        st.markdown(
            """
            <div class="xxx-card">
                <h3>Welcome to THE XXX AD POSTER</h3>
                <p>
                    This is your private control panel for adult affiliate work:
                </p>
                <ul>
                    <li><strong>Affiliate Programs:</strong> Track who you’ve applied with and who approved you.</li>
                    <li><strong>Ad Creatives:</strong> Generate clean, non-explicit headlines and body copy (with AI if you like).</li>
                    <li><strong>A/B Split Tester:</strong> Compare ads by CTR, CR, and EPC per traffic source.</li>
                    <li><strong>Performance:</strong> Log impressions, clicks, leads & sales to see what’s working.</li>
                    <li><strong>Campaign Notes:</strong> Save GEO, device, bid, and placement details per ad.</li>
                    <li><strong>Zapier:</strong> Fire webhooks on new ads and metric updates.</li>
                    <li><strong>Strategy:</strong> Step-by-step GEO & vertical roadmap for Toys, Dating & Cams.</li>
                    <li><strong>Links & Resources:</strong> Signup shortcuts for ad networks & affiliate programs.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        programs = fetch_programs()
        ads = fetch_ads()

        st.markdown('<div class="xxx-card">', unsafe_allow_html=True)
        st.markdown("### Snapshot", unsafe_allow_html=True)
        st.write(f"**Programs tracked:** {len(programs)}")
        st.write(f"**Ad creatives saved:** {len(ads)}")

        df_ads = fetch_ads_with_metrics_df()
        if not df_ads.empty:
            df_ads_filled = df_ads.fillna(0)
            total_impr = int(df_ads_filled["impressions"].sum())
            total_clicks = int(df_ads_filled["clicks"].sum())
            total_leads = int(df_ads_filled["leads"].sum())
            total_sales = int(df_ads_filled["sales"].sum())
            total_revenue = float(df_ads_filled["revenue"].sum())

            st.write(f"**Total impressions logged:** {total_impr}")
            st.write(f"**Total clicks logged:** {total_clicks}")
            st.write(f"**Total leads logged:** {total_leads}")
            st.write(f"**Total sales logged:** {total_sales}")
            st.write(f"**Total revenue logged:** ${total_revenue:,.2f}")

            if total_impr > 0:
                ctr = (total_clicks / total_impr) * 100
                st.write(f"**Overall CTR:** {ctr:.2f}%")
            if total_clicks > 0:
                cr_sales = (total_sales / total_clicks) * 100
                epc = total_revenue / total_clicks
                st.write(f"**Overall CR (sales/click):** {cr_sales:.2f}%")
                st.write(f"**Overall EPC:** ${epc:.3f}")
        else:
            st.write("No performance data yet. Start adding ads and metrics.")
        st.markdown("</div>", unsafe_allow_html=True)

    render_footer()


def page_affiliate_programs():
    render_header()
    st.subheader("🎯 Affiliate Programs & Accounts")
    st.markdown(
        "Use this section to track which adult-friendly affiliate programs and networks "
        "you’re researching, applied to, or already approved with."
    )

    with st.form("program_form"):
        st.markdown("### Add / Track a Program")
        name = st.text_input("Program / Network Name")
        col1, col2 = st.columns(2)
        with col1:
            niche = st.selectbox(
                "Main Category",
                ["Toys & Products", "Dating", "Cams & Live", "Other Adult"],
            )
        with col2:
            geo_focus = st.text_input("Main GEO Focus (e.g., US, UK/CA, Worldwide)", "US / English")

        signup_url = st.text_input("Signup / Login URL", placeholder="https://...")
        status = st.selectbox(
            "Status",
            ["Researching", "Applied", "Approved", "Rejected", "Paused"],
            index=0,
        )
        notes = st.text_area("Notes (requirements, payout model, etc.)", height=80)

        submitted = st.form_submit_button("➕ Add Program")
        if submitted:
            if not name or not signup_url:
                st.error("Please enter at least a program name and signup URL.")
            else:
                insert_program(
                    name.strip(),
                    niche.strip(),
                    geo_focus.strip(),
                    signup_url.strip(),
                    status.strip(),
                    notes.strip(),
                )
                st.success("Program added.")
                st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Your Program List")

    programs = fetch_programs()
    if not programs:
        st.info("No programs added yet. Use the form above to add your first one.")
    else:
        for p in programs:
            with st.expander(f"{p['name']} · {p['status']}"):
                st.write(f"**Category:** {p['niche']}")
                st.write(f"**GEO Focus:** {p['geo_focus']}")
                st.write(f"**Signup / Login URL:** {p['signup_url']}")
                if p["notes"]:
                    st.write(f"**Notes:** {p['notes']}")
                st.markdown(f"[Open Program Page]({p['signup_url']})")

    render_footer()


def page_ad_builder():
    render_header()
    st.subheader("📝 Ad Builder – THE XXX AD POSTER")
    st.markdown(
        "Generate short, adult-friendly ad copy for your offers. "
        "Language is non-explicit and focuses on benefits, privacy, and discretion."
    )

    programs = fetch_programs()
    if not programs:
        st.warning("Add at least one affiliate program on the 'Affiliate Programs' page first.")
        render_footer()
        return

    program_labels = [f"{p['name']} (#{p['id']})" for p in programs]
    program_ids = [p["id"] for p in programs]

    col_top1, col_top2 = st.columns([1.4, 1])
    with col_top1:
        program_choice = st.selectbox("Attach Ad To Program", program_labels)
        chosen_index = program_labels.index(program_choice)
        chosen_program_id = program_ids[chosen_index]
        chosen_program = get_program_by_id(chosen_program_id)
        st.info(f"Building ad for: **{chosen_program.get('name', '')}**")

    with col_top2:
        placement_type = st.selectbox(
            "Placement Type",
            ["Banner (300x250 / 300x100 / 728x90)", "Native / Widget", "Text Only", "Social-Friendly"],
        )
        traffic_source = st.selectbox(
            "Traffic Source / Network",
            ["ExoClick", "JuicyAds", "TrafficJunky", "Adsterra", "Other / Mixed"],
        )

    with st.form("ad_form"):
        st.markdown("### Ad Brief")
        offer_name = st.text_input("Offer / Product Name", value=chosen_program.get("name", ""))
        offer_type = st.selectbox("Offer Type", ["Toys", "Dating", "Cams", "Other"], index=0)
        audience = st.text_input("Target Audience (short)", "adults who want more fun in private")
        promise = st.text_input(
            "Main Promise / Outcome",
            "add more excitement and confidence without drama",
        )
        hook_style = st.selectbox(
            "Hook Style",
            [
                "Curiosity",
                "Discreet / Privacy",
                "Limited-Time",
                "Audience-Focused",
                "Mix: Use multiple angles",
            ],
            index=1,
        )

        ai_provider = st.selectbox(
            "AI Engine for Copy",
            ["Built-in (no API)", "OpenAI", "Claude (Anthropic)", "Gemini"],
            help="Built-in requires no keys. The others need API keys in Streamlit secrets.",
        )

        auto_generate = st.checkbox("Auto-generate copy from this brief", value=True)

        manual_headline = st.text_input("Headline (optional, overrides auto for single ad)")
        manual_body = st.text_area("Body Text (optional, overrides auto for single ad)", height=120)
        manual_cta = st.text_input("Call To Action", "Tap to explore today’s offers.")

        ad_title = st.text_input("Internal Ad Name / Label", "Main Angle – Mobile Banner")

        campaign_notes = st.text_area(
            "Campaign Notes (GEO, device, bid, placements, etc.)",
            placeholder="e.g. US mobile only, SmartCPM $0.15, exclude in-video zones, evenings 6–11pm",
            height=80,
        )

        num_variants = st.slider(
            "How many variants from this brief?",
            min_value=1,
            max_value=5,
            value=1,
            help="Use 1 for a single ad, or generate multiple variants with different angles.",
        )

        submitted = st.form_submit_button("✨ Generate & Save")

    if submitted:
        if num_variants == 1:
            # Single ad
            if auto_generate:
                gen = generate_ad_with_ai(
                    ai_provider, offer_name, offer_type, audience, promise, hook_style
                )
                headline = manual_headline.strip() or gen["headline"]
                body = manual_body.strip() or gen["body"]
                cta = manual_cta.strip() or gen["cta"]
            else:
                if not manual_headline or not manual_body:
                    st.error("If auto-generate is off, please fill in both headline and body.")
                    render_footer()
                    return
                headline = manual_headline.strip()
                body = manual_body.strip()
                cta = manual_cta.strip()

            ad_id = insert_ad(
                program_id=chosen_program_id,
                title=ad_title.strip(),
                angle=hook_style.strip(),
                headline=headline,
                body=body,
                call_to_action=cta,
                placement_type=placement_type.strip(),
                traffic_source=traffic_source.strip(),
                campaign_notes=campaign_notes.strip(),
            )
            trigger_zap(
                "new_ad_created",
                {
                    "ad_id": ad_id,
                    "program_id": chosen_program_id,
                    "title": ad_title.strip(),
                    "traffic_source": traffic_source.strip(),
                },
            )
            st.success("Ad creative generated and saved.")
        else:
            # Multi-variant generator
            if not auto_generate:
                st.error("Multiple variants require auto-generate to be enabled.")
                render_footer()
                return

            base_hooks = ["Curiosity", "Discreet / Privacy", "Limited-Time", "Audience-Focused"]

            if hook_style == "Mix: Use multiple angles":
                hooks_sequence = [base_hooks[i % len(base_hooks)] for i in range(num_variants)]
            else:
                hooks_sequence = [hook_style for _ in range(num_variants)]

            created_ids = []
            for i, hs in enumerate(hooks_sequence, start=1):
                gen = generate_ad_with_ai(
                    ai_provider, offer_name, offer_type, audience, promise, hs
                )
                headline = gen["headline"]
                body = gen["body"]
                cta = manual_cta.strip() or gen["cta"]

                if hook_style == "Mix: Use multiple angles":
                    title_variant = f"{ad_title.strip()} – {hs} v{i}"
                else:
                    title_variant = f"{ad_title.strip()} v{i}"

                ad_id = insert_ad(
                    program_id=chosen_program_id,
                    title=title_variant,
                    angle=hs,
                    headline=headline,
                    body=body,
                    call_to_action=cta,
                    placement_type=placement_type.strip(),
                    traffic_source=traffic_source.strip(),
                    campaign_notes=campaign_notes.strip(),
                )
                created_ids.append(ad_id)

            trigger_zap(
                "bulk_ads_created",
                {
                    "program_id": chosen_program_id,
                    "count": len(created_ids),
                    "traffic_source": traffic_source.strip(),
                    "ad_ids": created_ids,
                },
            )
            st.success(f"{num_variants} ad variants generated and saved.")

    st.markdown("---")
    st.markdown("### Saved Ad Creatives")

    ads = fetch_ads()
    if not ads:
        st.info("No ads yet. Use the form above to generate your first creative.")
    else:
        for ad in ads:
            perf = get_performance_for_ad(ad["id"])
            with st.expander(f"{ad['title']} · {ad['program_name'] or 'Unknown Program'}"):
                st.write(f"**Program:** {ad['program_name']}")
                st.write(f"**Placement:** {ad['placement_type']}")
                st.write(f"**Traffic Source:** {ad['traffic_source'] or 'N/A'}")
                st.write(f"**Angle:** {ad['angle']}")
                if ad["campaign_notes"]:
                    st.write(f"**Campaign Notes:** {ad['campaign_notes']}")
                st.markdown("**Headline:**")
                st.markdown(f"> {ad['headline']}")
                st.markdown("**Body:**")
                st.text(ad["body"])
                st.markdown("**CTA:**")
                st.markdown(f"> {ad['call_to_action']}")
                st.write(
                    f"**Performance so far:** "
                    f"{perf.get('impressions', 0)} impressions · "
                    f"{perf.get('clicks', 0)} clicks · "
                    f"{perf.get('leads', 0)} leads · "
                    f"{perf.get('sales', 0)} sales · "
                    f"${perf.get('revenue', 0.0):.2f} revenue"
                )

    render_footer()


def page_performance():
    render_header()
    st.subheader("📊 Performance Tracker")
    st.markdown(
        "Log impressions, clicks, leads, sales, and revenue per ad creative so you can see "
        "what’s working by angle and traffic source."
    )

    ads = fetch_ads()
    if not ads:
        st.info("No ads yet. Create some on the 'Ad Builder' page first.")
        render_footer()
        return

    ad_labels = [
        f"{ad['id']} – {ad['title']} ({ad['program_name'] or 'Unknown Program'})"
        for ad in ads
    ]
    ad_ids = [ad["id"] for ad in ads]

    ad_choice = st.selectbox("Select Ad to Update", ad_labels)
    idx = ad_labels.index(ad_choice)
    chosen_ad_id = ad_ids[idx]
    chosen_ad = [a for a in ads if a["id"] == chosen_ad_id][0]

    perf = get_performance_for_ad(chosen_ad_id)

    st.markdown("### Current Ad")
    st.write(f"**Program:** {chosen_ad['program_name']}")
    st.write(f"**Traffic Source:** {chosen_ad['traffic_source'] or 'N/A'}")
    st.write(f"**Title:** {chosen_ad['title']}")
    if chosen_ad["campaign_notes"]:
        st.write(f"**Campaign Notes:** {chosen_ad['campaign_notes']}")
    st.write(f"**Headline:** {chosen_ad['headline']}")

    st.markdown("---")
    st.markdown("### Update Performance (Totals)")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        impressions = st.number_input(
            "Impressions",
            min_value=0,
            value=int(perf.get("impressions", 0)),
            step=1,
        )
    with col2:
        clicks = st.number_input(
            "Clicks",
            min_value=0,
            value=int(perf.get("clicks", 0)),
            step=1,
        )
    with col3:
        leads = st.number_input(
            "Leads",
            min_value=0,
            value=int(perf.get("leads", 0)),
            step=1,
        )
    with col4:
        sales = st.number_input(
            "Sales",
            min_value=0,
            value=int(perf.get("sales", 0)),
            step=1,
        )
    with col5:
        revenue = st.number_input(
            "Revenue ($)",
            min_value=0.0,
            value=float(perf.get("revenue", 0.0)),
            step=0.01,
            format="%.2f",
        )

    if st.button("💾 Save Metrics"):
        update_performance(chosen_ad_id, impressions, clicks, leads, sales, revenue)
        trigger_zap(
            "performance_updated",
            {
                "ad_id": chosen_ad_id,
                "impressions": impressions,
                "clicks": clicks,
                "leads": leads,
                "sales": sales,
                "revenue": revenue,
            },
        )
        st.success("Performance updated.")

    st.markdown("---")
    st.markdown("### Per-Ad Overview")

    df = fetch_ads_with_metrics_df()
    if df.empty:
        st.info("No performance data yet.")
    else:
        df_show = df.copy().fillna(0)
        df_show["CTR_%"] = df_show.apply(
            lambda r: (r["clicks"] / r["impressions"] * 100) if r["impressions"] else 0.0,
            axis=1,
        )
        df_show["CR_sales_%"] = df_show.apply(
            lambda r: (r["sales"] / r["clicks"] * 100) if r["clicks"] else 0.0,
            axis=1,
        )
        df_show["EPC"] = df_show.apply(
            lambda r: (r["revenue"] / r["clicks"]) if r["clicks"] else 0.0,
            axis=1,
        )
        st.dataframe(
            df_show[
                [
                    "ad_id",
                    "program_name",
                    "traffic_source",
                    "title",
                    "campaign_notes",
                    "impressions",
                    "clicks",
                    "leads",
                    "sales",
                    "revenue",
                    "CTR_%",
                    "CR_sales_%",
                    "EPC",
                ]
            ]
        )

    st.markdown("---")
    st.markdown("### Per-Network Summary (CTR, CR, EPC)")

    if df.empty:
        st.info("No data yet for network summaries.")
    else:
        df_net = df.copy().fillna(0)
        df_net["traffic_source"] = df_net["traffic_source"].replace("", "Unknown")
        grouped = df_net.groupby("traffic_source", dropna=False).agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            leads=("leads", "sum"),
            sales=("sales", "sum"),
            revenue=("revenue", "sum"),
        )
        grouped = grouped.reset_index()

        grouped["CTR_%"] = grouped.apply(
            lambda r: (r["clicks"] / r["impressions"] * 100) if r["impressions"] else 0.0,
            axis=1,
        )
        grouped["CR_sales_%"] = grouped.apply(
            lambda r: (r["sales"] / r["clicks"] * 100) if r["clicks"] else 0.0,
            axis=1,
        )
        grouped["EPC"] = grouped.apply(
            lambda r: (r["revenue"] / r["clicks"]) if r["clicks"] else 0.0,
            axis=1,
        )

        st.dataframe(
            grouped[
                [
                    "traffic_source",
                    "impressions",
                    "clicks",
                    "leads",
                    "sales",
                    "revenue",
                    "CTR_%",
                    "CR_sales_%",
                    "EPC",
                ]
            ]
        )

    render_footer()


def page_ab_split():
    render_header()
    st.subheader("🧪 A/B Split Tester")
    st.markdown(
        "Use this to compare multiple creatives on **CTR, CR and EPC**.\n\n"
        "You still run traffic in the ad network — this is your analysis board "
        "to see which IDs are actually winning."
    )

    df = fetch_ads_with_metrics_df()
    if df.empty:
        st.info("No ads or metrics yet. Create ads and log performance first.")
        render_footer()
        return

    df = df.fillna(0)

    programs = fetch_programs()
    program_filter = st.selectbox(
        "Filter by Program",
        ["All programs"] + [p["name"] for p in programs],
    )

    if program_filter != "All programs":
        df = df[df["program_name"] == program_filter]

    traffic_sources = ["All sources"] + sorted(list(set(df["traffic_source"].fillna("Unknown"))))
    src_filter = st.selectbox("Filter by Traffic Source", traffic_sources)
    if src_filter != "All sources":
        df = df[df["traffic_source"] == src_filter]

    ad_options = [
        f"{int(row.ad_id)} – {row.title} ({row.program_name or 'Unknown'})"
        for _, row in df.iterrows()
    ]
    selected_labels = st.multiselect(
        "Select 2–6 ads to compare",
        ad_options,
    )
    selected_ids = []
    for label in selected_labels:
        ad_id = int(label.split("–")[0].strip())
        selected_ids.append(ad_id)

    if len(selected_ids) < 2:
        st.info("Pick at least 2 ads to run a comparison.")
        render_footer()
        return

    metric_choice = st.selectbox(
        "Primary KPI",
        ["CTR_%", "CR_sales_%", "EPC"],
        help="CTR = clicks/impressions; CR = sales/clicks; EPC = revenue/click.",
    )

    df_sel = df[df["ad_id"].isin(selected_ids)].copy()
    df_sel["CTR_%"] = df_sel.apply(
        lambda r: (r["clicks"] / r["impressions"] * 100) if r["impressions"] else 0.0,
        axis=1,
    )
    df_sel["CR_sales_%"] = df_sel.apply(
        lambda r: (r["sales"] / r["clicks"] * 100) if r["clicks"] else 0.0,
        axis=1,
    )
    df_sel["EPC"] = df_sel.apply(
        lambda r: (r["revenue"] / r["clicks"]) if r["clicks"] else 0.0,
        axis=1,
    )

    if not df_sel.empty:
        winner_idx = df_sel[metric_choice].idxmax()
        winner_row = df_sel.loc[winner_idx]
        st.success(
            f"🏆 Current winner on **{metric_choice}**: "
            f"Ad #{int(winner_row['ad_id'])} – {winner_row['title']}"
        )

    st.markdown("### Comparison Table")
    st.dataframe(
        df_sel[
            [
                "ad_id",
                "program_name",
                "traffic_source",
                "title",
                "impressions",
                "clicks",
                "leads",
                "sales",
                "revenue",
                "CTR_%",
                "CR_sales_%",
                "EPC",
            ]
        ]
    )

    st.info(
        "Tip: You can treat the top 1–2 winners as your **‘keep scaling’** group and "
        "pause the others in the ad network UI."
    )

    render_footer()


def page_export_copy():
    render_header()
    st.subheader("📦 Export & Copy Center")
    st.markdown(
        "Grab ad text blocks for copy-paste into traffic platforms, and export your data as CSV."
    )

    ads = fetch_ads()
    if not ads:
        st.info("No ads available yet. Create some on the Ad Builder page.")
    else:
        ad_labels = [
            f"{ad['id']} – {ad['title']} ({ad['program_name'] or 'Unknown Program'})"
            for ad in ads
        ]
        ad_ids = [ad["id"] for ad in ads]

        ad_choice = st.selectbox("Choose an ad creative to view / copy", ad_labels)
        idx = ad_labels.index(ad_choice)
        chosen_ad_id = ad_ids[idx]
        chosen_ad = [a for a in ads if a["id"] == chosen_ad_id][0]

        st.markdown("### Selected Ad Creative")
        st.write(f"**Program:** {chosen_ad['program_name']}")
        st.write(f"**Placement:** {chosen_ad['placement_type']}")
        st.write(f"**Traffic Source:** {chosen_ad['traffic_source'] or 'N/A'}")
        if chosen_ad["campaign_notes"]:
            st.write(f"**Campaign Notes:** {chosen_ad['campaign_notes']}")
        st.write(f"**Angle:** {chosen_ad['angle']}")

        block = textwrap.dedent(
            f"""
            [{chosen_ad['program_name']}] – {chosen_ad['title']}

            TRAFFIC / CAMPAIGN:
            Source: {chosen_ad['traffic_source'] or 'N/A'}
            Notes: {chosen_ad['campaign_notes'] or 'n/a'}

            HEADLINE:
            {chosen_ad['headline']}

            BODY:
            {chosen_ad['body']}

            CTA:
            {chosen_ad['call_to_action']}
            """
        ).strip()

        st.text_area("Copy-ready block", block, height=260)
        st.info("Select all and copy this block into your traffic source or ad manager.")

    st.markdown("---")
    st.markdown("### CSV Export")

    col1, col2 = st.columns(2)
    with col1:
        df_prog = fetch_programs_df()
        if df_prog.empty:
            st.write("No programs to export yet.")
        else:
            csv_prog = df_prog.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Programs CSV",
                data=csv_prog,
                file_name="xxx_affiliate_programs.csv",
                mime="text/csv",
            )
    with col2:
        df_ads = fetch_ads_with_metrics_df()
        if df_ads.empty:
            st.write("No ads / metrics to export yet.")
        else:
            csv_ads = df_ads.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Ads & Metrics CSV",
                data=csv_ads,
                file_name="xxx_ads_with_performance.csv",
                mime="text/csv",
            )

    render_footer()


def page_links_resources():
    render_header()
    st.subheader("🔗 Links & Resources – Signup Hubs")
    st.markdown(
        "Quick access to popular adult-friendly **ad networks** and **affiliate programs**. "
        "Always review each platform’s terms, legal requirements, and age restrictions."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🚦 Adult Ad Networks")
        st.markdown(
            """
- ExoClick – https://www.exoclick.com/
- JuicyAds – https://juicyads.com/
- TrafficJunky – https://www.trafficjunky.com/
- TrafficStars – https://trafficstars.com/
- Adsterra – https://adsterra.com/
- EroAdvertising – https://www.eroadvertising.com/
            """
        )

        st.markdown("### 🧪 Useful Tools (Tracking etc.)")
        st.markdown(
            """
- Voluum – https://voluum.com/
- BeMob – https://bemob.com/
- Binom – https://binom.org/
            """
        )

    with col2:
        st.markdown("### 💰 Adult Affiliate Networks")
        st.markdown(
            """
- CrakRevenue – https://www.crakrevenue.com/
- CPAMatica – https://cpamatica.io/
- StripCash – https://stripcash.com/
- CherryCash – https://cherrycash.com/
- AdultFriendFinder Affiliates – https://www.affiliatefriendfinder.com/
            """
        )

        st.markdown("### 🛒 Toys & Ecommerce Affiliate Programs")
        st.markdown(
            """
- Lovehoney Affiliates – https://www.lovehoneygroup.com/affiliates/
- Adam & Eve Affiliate – https://www.adamandeve.com/affiliates
- EdenFantasys Affiliate – https://www.edenfantasys.com/affiliate/
            """
        )

    st.markdown("---")
    st.info(
        "Tip: when you sign up, add each network as a Program in the **Affiliate Programs** section, "
        "with notes on payout model (CPA/RevShare/CPL) and any restrictions."
    )

    render_footer()


def page_integrations():
    render_header()
    st.subheader("⚙️ Integrations – AI & Zapier")
    st.markdown(
        "Configure optional integrations. The app works fine with the built-in generator "
        "and without webhooks if you prefer to keep it simple."
    )

    st.markdown("### 🔄 Zapier Webhook")
    st.markdown(
        "You can fire a Zapier Catch Hook whenever:\n"
        "- a new ad is created\n"
        "- performance metrics are updated\n\n"
        "Set the URL here, or store it as `ZAPIER_WEBHOOK_URL` in Streamlit secrets."
    )

    zap_url = st.text_input(
        "Zapier Catch Hook URL",
        value=st.session_state.get("zapier_webhook_url", ""),
        placeholder="https://hooks.zapier.com/hooks/catch/XXXX/YYYY",
    )
    if st.button("Save Zapier URL"):
        st.session_state["zapier_webhook_url"] = zap_url.strip()
        st.success("Zapier URL saved in session (for long-term, add it to Streamlit secrets).")

    if st.button("Test Zapier Webhook"):
        trigger_zap("test_ping", {"message": "test_ping_from_xxx_ad_poster"})
        st.info("Test event sent. Check your Zap history in Zapier.")

    st.markdown("---")
    st.markdown("### 🤖 AI APIs for Copy")

    st.markdown(
        "The Ad Builder can optionally use external AI for copy:\n\n"
        "- OpenAI\n"
        "- Claude (Anthropic)\n"
        "- Gemini (Google)\n\n"
        "Add these keys to your Streamlit secrets (secrets.toml):\n"
        "- OPENAI_API_KEY\n"
        "- ANTHROPIC_API_KEY\n"
        "- GEMINI_API_KEY\n\n"
        "Then in the Ad Builder, choose your engine. If anything fails or a key is missing, "
        "the app falls back to the built-in generator."
    )

    render_footer()


def page_strategy():
    render_header()
    st.subheader("🧠 Strategy: GEOs, Verticals & Payouts")
    st.markdown(
        "This tab is your quick-reference playbook for Toys, Dating and Cams across "
        "English-speaking markets."
    )

    # Toys
    st.markdown("### 1️⃣ Toys & Sexual Wellness – Main Vertical")
    st.markdown(
        """
Primary GEOs for toys:

- 🇺🇸 United States
- 🇬🇧 United Kingdom
- 🇨🇦 Canada
- 🇦🇺 Australia

Why start here:

- Sex-toy market is huge and growing.
- Easier to stay inside payment/legal rules vs hardcore content.
- Works great with banner and native traffic.
"""
    )
    st.markdown(
        """
Suggested stack:

- Offers: Lovehoney, Adam & Eve, EdenFantasys, plus toy/ecom offers from big networks.
- Traffic: ExoClick, JuicyAds, TrafficStars, Adsterra.
- Payout: CPA (typical $25–$50+ per sale).
"""
    )

    # Dating
    st.markdown("### 2️⃣ Adult Dating – High EPC, Higher Costs")
    st.markdown(
        """
Best starter GEOs:

- 🇺🇸 US
- 🇬🇧 UK

Then expand to:

- 🇨🇦 CA
- 🇦🇺 AU

Strategy:

- Use CPL (email submit / signup) to start – easier conversions, faster feedback.
- Warm traffic with quizzes, “are you their type?”, personality prelanders.
- Test Tier-2 English GEOs for cheaper clicks once funnel is converting.
"""
    )

    # Cams
    st.markdown("### 3️⃣ Cams / Live Streaming – Backend Money")
    st.markdown(
        """
Core GEOs:

- 🇺🇸 US
- 🇬🇧 UK
- 🇨🇦 CA
- 🇦🇺 AU

Payout:

- Rev-share for long-term whale value.
- Hybrid (small CPA + rev-share) for a mix of upfront + backend.

Offers:

- StripCash (Stripchat)
- Chaturbate
- BongaCash
- LiveJasmin / AWEmpire
"""
    )

    # Payout summary
    st.markdown("### 4️⃣ Payout Cheat-Sheet")
    st.table(
        pd.DataFrame(
            [
                ["Toys", "Rare", "⭐ Best", "OK", "CPA"],
                ["Dating", "⭐ Best starter", "⚠️ Risky", "Slow", "CPL"],
                ["Cams", "Easy but low", "Good", "⭐ Highest lifetime", "Rev-Share / Hybrid"],
            ],
            columns=["Vertical", "CPL", "CPA", "Rev-Share", "You Should Choose"],
        )
    )

    st.markdown(
        """
Quick decisions:

- TOYS → use **CPA**
- DATING → start with **CPL**
- CAMS → lean on **Rev-Share** (or hybrid Rev+CPA)

This combo gives you:

- Fast daily cashflow (CPL + CPA)
- Mid-term ROI (CPA toys)
- Long-term passive income (cam rev-share)
"""
    )

    render_footer()


# =========================
# Sidebar & router
# =========================

def main_app():
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-logo">THE XXX AD POSTER</div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Navigation**")
        page = st.radio(
            "",
            [
                "Dashboard",
                "Affiliate Programs",
                "Ad Builder",
                "Performance",
                "A/B Split Tester",
                "Export / Copy",
                "Strategy",
                "Links & Resources",
                "Integrations",
            ],
        )

        st.markdown("---")
        if st.button("Log Out"):
            st.session_state["auth_ok"] = False
            st.experimental_rerun()

    if page == "Dashboard":
        page_dashboard()
    elif page == "Affiliate Programs":
        page_affiliate_programs()
    elif page == "Ad Builder":
        page_ad_builder()
    elif page == "Performance":
        page_performance()
    elif page == "A/B Split Tester":
        page_ab_split()
    elif page == "Export / Copy":
        page_export_copy()
    elif page == "Strategy":
        page_strategy()
    elif page == "Links & Resources":
        page_links_resources()
    elif page == "Integrations":
        page_integrations()
    else:
        page_dashboard()


# =========================
# Entry point
# =========================

if __name__ == "__main__":
    init_db()
    if not st.session_state.get("auth_ok", False):
        login_page()
    else:
        main_app()



