import streamlit as st
from typing import List, Dict
import textwrap

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

/* Tables */
.xxx-table thead tr th {
    background-color: #2a1824 !important;
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
# Session-state helpers
# =========================

if "auth_ok" not in st.session_state:
    st.session_state["auth_ok"] = False

if "affiliate_programs" not in st.session_state:
    # each item: {id, name, niche, geo_focus, signup_url, status, notes}
    st.session_state["affiliate_programs"] = []

if "ad_creatives" not in st.session_state:
    # each item: {id, program_id, title, angle, headline, body, call_to_action, placement_type}
    st.session_state["ad_creatives"] = []

if "next_program_id" not in st.session_state:
    st.session_state["next_program_id"] = 1

if "next_ad_id" not in st.session_state:
    st.session_state["next_ad_id"] = 1


# =========================
# UI helpers
# =========================

def render_header():
    st.markdown(
        """
        <div class="xxx-header">
            <div class="xxx-logo">🔥</div>
            <div class="xxx-title">THE XXX AD POSTER</div>
            <div class="xxx-subtitle">
                Manage your affiliate accounts & build clean, compliant ad copy for adult offers.
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
            Store no sensitive data here. Use for planning, not passwords.
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
        # super simple demo auth – you can replace with secrets or OAuth later
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
# Data helpers
# =========================

def add_affiliate_program(
    name: str,
    niche: str,
    geo_focus: str,
    signup_url: str,
    status: str,
    notes: str,
):
    pid = st.session_state["next_program_id"]
    st.session_state["next_program_id"] += 1
    st.session_state["affiliate_programs"].append(
        {
            "id": pid,
            "name": name.strip(),
            "niche": niche.strip(),
            "geo_focus": geo_focus.strip(),
            "signup_url": signup_url.strip(),
            "status": status.strip(),
            "notes": notes.strip(),
        }
    )


def add_ad_creative(
    program_id: int,
    title: str,
    angle: str,
    headline: str,
    body: str,
    call_to_action: str,
    placement_type: str,
):
    aid = st.session_state["next_ad_id"]
    st.session_state["next_ad_id"] += 1
    st.session_state["ad_creatives"].append(
        {
            "id": aid,
            "program_id": program_id,
            "title": title.strip(),
            "angle": angle.strip(),
            "headline": headline.strip(),
            "body": body.strip(),
            "call_to_action": call_to_action.strip(),
            "placement_type": placement_type.strip(),
        }
    )


def get_program_by_id(pid: int) -> Dict:
    for p in st.session_state["affiliate_programs"]:
        if p["id"] == pid:
            return p
    return {}


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
        headline = f\"This {offer_type.title()} Offer Is Making Adults Smile\"\"
    elif hook_style == "Discreet / Privacy":
        headline = "100% Discreet · For Adults Only"
    elif hook_style == "Limited-Time":
        headline = f"{offer_type.title()} Deals Ending Soon"
    else:
        headline = f"New For {audience.capitalize()}"

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
                    Use this control panel to map out your adult-friendly affiliate programs,
                    keep track of signups, and craft clean, compliant ad copy for traffic
                    networks and social platforms.
                </p>
                <ul>
                    <li><strong>Affiliate Programs:</strong> log where you’re signed up and what’s pending.</li>
                    <li><strong>Ad Creatives:</strong> store headlines, angles, and body copy for each offer.</li>
                    <li><strong>Export / Copy:</strong> quickly copy winning ads into your campaigns.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div class="xxx-card">
                <h3>Quick Start</h3>
                <ol>
                    <li>Go to <strong>Affiliate Programs</strong> and add your offers.</li>
                    <li>Then move to <strong>Ad Builder</strong> to generate 3–5 angles.</li>
                    <li>Copy ads into your traffic networks (manual or via copy-paste).</li>
                    <li>Return here to update statuses as approvals come in.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_footer()


def page_affiliate_programs():
    render_header()
    st.subheader("🎯 Affiliate Programs & Accounts")
    st.markdown(
        "Use this section to keep track of the adult-friendly programs you’ve applied to or joined. "
        "This does not automatically sign you up; it helps you organize everything."
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

        submitted = st.form_submit_button("➕ Add / Update Program")
        if submitted:
            if not name or not signup_url:
                st.error("Please enter at least a program name and signup URL.")
            else:
                add_affiliate_program(name, niche, geo_focus, signup_url, status, notes)
                st.success("Program added to your list.")

    st.markdown("---")
    st.markdown("### Your Program List")

    programs = st.session_state["affiliate_programs"]
    if not programs:
        st.info("No programs added yet. Use the form above to add your first one.")
    else:
        for p in programs:
            with st.expander(f"{p['name']}  ·  {p['status']}"):
                st.write(f"**Category:** {p['niche']}")
                st.write(f"**GEO Focus:** {p['geo_focus']}")
                st.write(f"**Signup / Login URL:** {p['signup_url']}")
                if p["notes"]:
                    st.write(f"**Notes:** {p['notes']}")
                st.markdown(
                    f"[Open Program Page]({p['signup_url']})",
                    unsafe_allow_html=False,
                )

    render_footer()


def page_ad_builder():
    render_header()
    st.subheader("📝 Ad Builder – THE XXX AD POSTER")
    st.markdown(
        "Generate short, platform-friendly ad copy for your offers. "
        "All language here is kept non-explicit and focused on benefits and privacy."
    )

    programs = st.session_state["affiliate_programs"]
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
            ["Curiosity", "Discreet / Privacy", "Limited-Time", "Audience-Focused"],
            index=1,
        )

        auto_generate = st.checkbox("Auto-generate copy from this brief", value=True)

        manual_headline = st.text_input("Headline (optional, overrides auto)")
        manual_body = st.text_area("Body Text (optional, overrides auto)", height=120)
        manual_cta = st.text_input("Call To Action", "Tap to explore today’s offers.")

        ad_title = st.text_input("Internal Ad Name / Label", "Main Angle – Mobile Banner")

        submitted = st.form_submit_button("✨ Generate & Save Ad")

    if submitted:
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

        add_ad_creative(
            program_id=chosen_program_id,
            title=ad_title,
            angle=hook_style,
            headline=headline,
            body=body,
            call_to_action=cta,
            placement_type=placement_type,
        )
        st.success("Ad creative generated and saved below.")

    st.markdown("---")
    st.markdown("### Saved Ad Creatives")

    ads = st.session_state["ad_creatives"]
    if not ads:
        st.info("No ads yet. Use the form above to generate your first creative.")
    else:
        for ad in ads:
            program = get_program_by_id(ad["program_id"])
            with st.expander(f"{ad['title']} · {program.get('name', 'Unknown Program')}"):
                st.write(f"**Program:** {program.get('name', '')}")
                st.write(f"**Placement:** {ad['placement_type']}")
                st.write(f"**Angle:** {ad['angle']}")
                st.markdown("**Headline:**")
                st.markdown(f"> {ad['headline']}")
                st.markdown("**Body:**")
                st.text(ad["body"])
                st.markdown("**CTA:**")
                st.markdown(f"> {ad['call_to_action']}")

    render_footer()


def page_export_copy():
    render_header()
    st.subheader("📦 Export & Copy-Paste Center")
    st.markdown(
        "Use this section to quickly grab ad sets for launching in traffic networks. "
        "You can copy blocks directly or export text to paste into another tool."
    )

    ads = st.session_state["ad_creatives"]
    if not ads:
        st.info("No ads available yet. Create some on the Ad Builder page.")
        render_footer()
        return

    programs = st.session_state["affiliate_programs"]
    program_names = {p["id"]: p["name"] for p in programs}

    ad_labels = [
        f"{ad['title']} – {program_names.get(ad['program_id'], 'Unknown Program')}"
        for ad in ads
    ]
    ad_choice = st.selectbox("Choose an ad creative to view / copy", ad_labels)
    chosen_index = ad_labels.index(ad_choice)
    chosen_ad = ads[chosen_index]
    program_name = program_names.get(chosen_ad["program_id"], "Unknown Program")

    st.markdown("### Selected Ad Creative")
    st.write(f"**Program:** {program_name}")
    st.write(f"**Placement:** {chosen_ad['placement_type']}")
    st.write(f"**Angle:** {chosen_ad['angle']}")

    block = textwrap.dedent(
        f"""
        [{program_name}] – {chosen_ad['title']}

        HEADLINE:
        {chosen_ad['headline']}

        BODY:
        {chosen_ad['body']}

        CTA:
        {chosen_ad['call_to_action']}
        """
    ).strip()

    st.text_area("Copy-ready block", block, height=200)
    st.info("Select all and copy this block into your traffic source or ad manager.")

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
            ["Dashboard", "Affiliate Programs", "Ad Builder", "Export / Copy"],
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
    elif page == "Export / Copy":
        page_export_copy()
    else:
        page_dashboard()


# =========================
# Entry point
# =========================

if __name__ == "__main__":
    if not st.session_state.get("auth_ok", False):
        login_page()
    else:
        main_app()
