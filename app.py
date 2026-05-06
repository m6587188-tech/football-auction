import streamlit as st
import random
import firebase_admin

from firebase_admin import credentials
from firebase_admin import db

from streamlit_autorefresh import st_autorefresh
from players import PLAYERS

# =========================
# FIREBASE INIT
# =========================

if not firebase_admin._apps:

    cred = credentials.Certificate(
        "firebase_key.json"
    )

    firebase_admin.initialize_app(
        cred,
        {
            "databaseURL":
            "https://football-auction-1327d-default-rtdb.asia-southeast1.firebasedatabase.app/"
        }
    )

# =========================
# DATABASE REFERENCES
# =========================

auction_ref = db.reference("auction")

teams_ref = db.reference("teams")

logs_ref = db.reference("logs")

# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="Football Auction Multiplayer",
    layout="wide"
)

# =========================
# AUTO REFRESH
# =========================

st_autorefresh(
    interval=2000,
    key="refresh"
)

# =========================
# CONFIG
# =========================

ADMIN_PASSWORD = "1234"

MAX_SQUAD_SIZE = 17

# =========================
# CSS
# =========================

st.markdown("""

<style>

.main {
    background-color: #020617;
    color: white;
}

.big-title {

    text-align:center;

    font-size:50px;

    font-weight:bold;

    color:#38bdf8;
}

.card {

    background:#0f172a;

    border-radius:18px;

    padding:18px;

    border:1px solid #334155;
}

.timer {

    font-size:55px;

    font-weight:bold;

    text-align:center;

    color:#38bdf8;
}

.center {
    text-align:center;
}

.bid-btn button {

    width:100%;

    height:60px;

    font-size:22px;

    border-radius:12px;
}

</style>

""", unsafe_allow_html=True)

# =========================
# INITIALIZE DATABASE
# =========================

auction_data = auction_ref.get()

if auction_data is None:

    first_player = random.choice(
        PLAYERS
    )

    auction_ref.set({

        "current_player":
        first_player,

        "highest_bid":
        first_player["value"],

        "highest_bidder":
        "No bids",

        "timer":
        60,

        "auction_phase":
        "bidding",

        "pause_timer":
        15,

        "auction_paused":
        False
    })

# =========================
# LOAD LIVE DATA
# =========================

auction = auction_ref.get()

current_player = auction["current_player"]

highest_bid = auction["highest_bid"]

highest_bidder = auction["highest_bidder"]

timer = auction["timer"]

auction_phase = auction["auction_phase"]

pause_timer = auction["pause_timer"]

auction_paused = auction["auction_paused"]

teams = teams_ref.get()

if teams is None:
    teams = {}

logs = logs_ref.get()

if logs is None:
    logs = []

# =========================
# FUNCTIONS
# =========================

def format_money(amount):

    if amount >= 1000:

        return f"€{amount/1000:.1f}B"

    return f"€{amount}M"


def add_log(text):

    current_logs = logs_ref.get()

    if current_logs is None:
        current_logs = []

    current_logs.insert(0, text)

    logs_ref.set(current_logs[:10])


def next_player():

    available = PLAYERS.copy()

    for team in teams.values():

        for p in team["players"]:

            available = [
                x for x in available
                if x["name"] != p["name"]
            ]

    if len(available) == 0:

        st.success("🏆 Auction Finished")

        st.stop()

    player = random.choice(available)

    auction_ref.update({

        "current_player":
        player,

        "highest_bid":
        player["value"],

        "highest_bidder":
        "No bids",

        "timer":
        60,

        "auction_phase":
        "bidding"
    })


def sell_player():

    player = current_player

    if highest_bidder == "No bids":

        add_log(
            f"❌ {player['name']} went UNSOLD"
        )

        auction_ref.update({

            "auction_phase":
            "pause",

            "pause_timer":
            15
        })

        return

    team_data = teams_ref.child(
        highest_bidder
    ).get()

    players = team_data["players"]

    players.append(player)

    teams_ref.child(
        highest_bidder
    ).update({

        "players":
        players,

        "purse":
        team_data["purse"] - highest_bid
    })

    add_log(
        f"🏆 {highest_bidder} bought {player['name']} for {format_money(highest_bid)}"
    )

    auction_ref.update({

        "auction_phase":
        "pause",

        "pause_timer":
        15
    })

# =========================
# SIDEBAR
# =========================

st.sidebar.title("⚙ Settings")

view_mode = st.sidebar.selectbox(
    "Mode",
    ["Player", "Admin"]
)

team_name = st.sidebar.text_input(
    "Team Name"
)

# =========================
# ADMIN LOGIN
# =========================

is_admin = False

if view_mode == "Admin":

    password = st.sidebar.text_input(
        "Password",
        type="password"
    )

    if password == ADMIN_PASSWORD:

        is_admin = True

# =========================
# TEAM CREATE
# =========================

if team_name:

    if team_name not in teams:

        teams_ref.child(team_name).set({

            "purse":
            1000,

            "players":
            []
        })

        teams = teams_ref.get()

# =========================
# TIMER LOGIC
# ONLY ADMIN CONTROLS TIMER
# =========================

if is_admin:

    if not auction_paused:

        if auction_phase == "bidding":

            if timer > 0:

                auction_ref.update({
                    "timer":
                    timer - 1
                })

            else:

                sell_player()

        elif auction_phase == "pause":

            if pause_timer > 0:

                auction_ref.update({
                    "pause_timer":
                    pause_timer - 1
                })

            else:

                next_player()

# =========================
# TITLE
# =========================

st.markdown("""

<div class='big-title'>

⚽ Football Auction Multiplayer

</div>

""", unsafe_allow_html=True)

st.divider()

# =========================
# PLAYER DISPLAY
# =========================

c1, c2, c3 = st.columns([2,1,1])

with c1:

    st.markdown(f"""

    <div class='card'>

    <h1>{current_player['name']}</h1>

    <h2>{current_player['club']}</h2>

    <h3>{current_player['position']}</h3>

    <h2>Base Price:
    {format_money(current_player['value'])}
    </h2>

    </div>

    """, unsafe_allow_html=True)

with c2:

    st.markdown(f"""

    <div class='card center'>

    <h2>Highest Bid</h2>

    <h1>{format_money(highest_bid)}</h1>

    <h3>{highest_bidder}</h3>

    </div>

    """, unsafe_allow_html=True)

with c3:

    if auction_phase == "bidding":

        st.markdown(f"""

        <div class='card'>

        <h2 class='center'>Timer</h2>

        <div class='timer'>

        {timer}s

        </div>

        </div>

        """, unsafe_allow_html=True)

    else:

        st.markdown(f"""

        <div class='card'>

        <h2 class='center'>Next Player</h2>

        <div class='timer'>

        {pause_timer}s

        </div>

        </div>

        """, unsafe_allow_html=True)

# =========================
# PAUSED
# =========================

if auction_paused:

    st.warning("⏸ Auction Paused")

# =========================
# PLAYER VIEW
# =========================

if view_mode == "Player":

    st.divider()

    st.subheader("💸 Place Bid")

    b1, b2, b3, b4, b5 = st.columns(5)

    increments = [5,10,20,50,100]

    for col, amount in zip(
        [b1,b2,b3,b4,b5],
        increments
    ):

        with col:

            if st.button(f"+{amount}"):

                if team_name:

                    team = teams[team_name]

                    if len(team["players"]) < MAX_SQUAD_SIZE:

                        bid = highest_bid + amount

                        if bid <= team["purse"]:

                            auction_ref.update({

                                "highest_bid":
                                bid,

                                "highest_bidder":
                                team_name,

                                "timer":
                                30
                            })

                            add_log(
                                f"💸 {team_name} bid {format_money(bid)}"
                            )

    st.divider()

    if team_name:

        team = teams[team_name]

        st.subheader(
            f"🏟 {team_name}"
        )

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "Budget Left",
                format_money(team["purse"])
            )

        with c2:

            spent = 1000 - team["purse"]

            st.metric(
                "Spent",
                format_money(spent)
            )

        st.write(
            f"Squad Size: {len(team['players'])}/{MAX_SQUAD_SIZE}"
        )

        st.subheader("Players")

        for p in team["players"]:

            st.write(
                f"• {p['name']}"
            )

# =========================
# ADMIN VIEW
# =========================

if is_admin:

    st.divider()

    st.subheader("🛠 Admin Controls")

    a1, a2, a3 = st.columns(3)

    with a1:

        if st.button("⏭ Skip"):

            next_player()

    with a2:

        if st.button("⏸ Pause"):

            auction_ref.update({
                "auction_paused":
                True
            })

    with a3:

        if st.button("▶ Resume"):

            auction_ref.update({
                "auction_paused":
                False
            })

    st.divider()

    st.subheader("👥 Teams")

    for name, data in teams.items():

        st.markdown(f"""

        <div class='card'>

        <h2>{name}</h2>

        <p>Purse:
        {format_money(data['purse'])}</p>

        <p>Players:
        {len(data['players'])}</p>

        </div>

        """, unsafe_allow_html=True)

        for p in data["players"]:

            st.write(
                f"• {p['name']}"
            )

# =========================
# LOGS
# =========================

st.divider()

st.subheader("📜 Auction Logs")

for log in logs[:10]:

    st.write(log)