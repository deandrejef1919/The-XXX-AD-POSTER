import sqlite3
import textwrap
from typing import Dict, List

import pandas as pd
import streamlit as st

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

    # In case the DB was created with an older version, ensure new columns exist
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
        # simple demo auth – change via Streamlit secrets on deployment
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
# Ad text generator
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
                    <li><strong>Ad Creatives:</strong> Generate clean, non-explicit headlines and body copy.</li>
                    <li><strong>Performance:</strong> Log impressions, clicks, leads & sales to see what’s working.</li>
                    <li><strong>Campaign Notes:</strong> Save GEO, device, bid, and placement details per ad.</li>
                    <li><strong>Export:</strong> Download CSVs of programs & ads for backup or sharing.</li>
                    <li><strong>Links & Resources:</strong> Jump straight to signup pages for ad networks & affiliate programs.</li>
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
            # Single ad logic
            if auto_generate:
                gen = generate_ad_from_brief(offer_name, offer_type, audience, promise, hook_style)
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

            insert_ad(
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

            for i, hs in enumerate(hooks_sequence, start=1):
                gen = generate_ad_from_brief(offer_name, offer_type, audience, promise, hs)
                headline = gen["headline"]
                body = gen["body"]
                cta = manual_cta.strip() or gen["cta"]

                if hook_style == "Mix: Use multiple angles":
                    title_variant = f"{ad_title.strip()} – {hs} v{i}"
                else:
                    title_variant = f"{ad_title.strip()} v{i}"

                insert_ad(
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
        if st.button("⬇️ Download Programs CSV"):
            df_prog = fetch_programs_df()
            if df_prog.empty:
                st.warning("No programs to export yet.")
            else:
                csv = df_prog.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Save Programs CSV",
                    data=csv,
                    file_name="xxx_affiliate_programs.csv",
                    mime="text/csv",
                )
    with col2:
        if st.button("⬇️ Download Ads + Metrics CSV"):
            df_ads = fetch_ads_with_metrics_df()
            if df_ads.empty:
                st.warning("No ads / metrics to export yet.")
            else:
                csv = df_ads.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Save Ads & Metrics CSV",
                    data=csv,
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

    # Ad Networks
    with col1:
        st.markdown("### 🚦 Adult Ad Networks")
        st.markdown(
            """
- [ExoClick](https://www.exoclick.com/) – Large adult ad network for banners, native, pops.
- [JuicyAds](https://juicyads.com/) – “Sexy advertising network” with many adult publishers.
- [TrafficJunky](https://www.trafficjunky.com/) – Media buying for Pornhub network & partners.
- [TrafficStars](https://trafficstars.com/) – SSP with adult tube, cam & site inventory.
- [Adsterra](https://adsterra.com/) – Mainstream + adult-friendly formats (pops, push, banners).
- [EroAdvertising](https://www.eroadvertising.com/) – Long-running adult-focused ad network.
            """
        )

        st.markdown("### 🧪 Useful Tools (Tracking etc.)")
        st.markdown(
            """
- [Voluum](https://voluum.com/) – Affiliate campaign tracker.
- [BeMob](https://bemob.com/) – Tracker suitable for smaller budgets.
- [Binom](https://binom.org/) – Self-hosted tracker (more advanced users).
            """
        )

    # Affiliate Networks
    with col2:
        st.markdown("### 💰 Adult Affiliate Networks")
        st.markdown(
            """
- [CrakRevenue](https://www.crakrevenue.com/) – Large adult network (dating, cams, toys).
- [CPAMatica](https://cpamatica.io/) – Strong in adult dating offers.
- [StripCash](https://stripcash.com/) – Affiliate program for Stripchat (cams).
- [CherryCash](https://cherrycash.com/) – Adult streaming / platform offers.
- [AdultFriendFinder Affiliate](https://www.affiliatefriendfinder.com/) – Adult dating offers.
            """
        )

        st.markdown("### 🛒 Toys & Ecommerce Affiliate Programs")
        st.markdown(
            """
- [Lovehoney Affiliates](https://www.lovehoneygroup.com/affiliates/) – Global sex toy brand.
- [Adam & Eve Affiliate](https://www.adamandeve.com/affiliates) – Big U.S. adult store.
- [EdenFantasys Affiliate](https://www.edenfantasys.com/affiliate/) – Online toy store program.
- Check your main CPA network (e.g., CrakRevenue) for additional toy/ecom offers.
            """
        )

    st.markdown("---")
    st.info(
        "Tip: when you sign up, add each network as a Program in the **Affiliate Programs** section, "
        "with notes on payout model (CPA/RevShare/CPL) and any restrictions."
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
                "Export / Copy",
                "Links & Resources",
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
    elif page == "Export / Copy":
        page_export_copy()
    elif page == "Links & Resources":
        page_links_resources()
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



