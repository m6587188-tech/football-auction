import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh
from players import PLAYERS

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Football Auction V6",
    layout="wide"
)

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(
    interval=1000,
    key="auction_refresh"
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

    text-align: center;

    font-size: 55px;

    font-weight: bold;

    color: #38bdf8;
}

.card {

    background: #0f172a;

    border-radius: 20px;

    padding: 25px;

    border: 1px solid #334155;

    box-shadow: 0 0 15px rgba(0,0,0,0.4);
}

.timer {

    font-size: 55px;

    font-weight: bold;

    color: #38bdf8;

    text-align: center;
}

.center {
    text-align:center;
}

.bid-btn button {

    width: 100%;

    height: 65px;

    font-size: 24px;

    border-radius: 15px;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================
if "teams" not in st.session_state:
    st.session_state.teams = {}

if "logs" not in st.session_state:
    st.session_state.logs = []

if "available_players" not in st.session_state:
    st.session_state.available_players = PLAYERS.copy()

if "current_player" not in st.session_state:
    st.session_state.current_player = random.choice(
        st.session_state.available_players
    )

if "highest_bid" not in st.session_state:
    st.session_state.highest_bid = (
        st.session_state.current_player["value"]
    )

if "highest_bidder" not in st.session_state:
    st.session_state.highest_bidder = "No bids"

if "timer" not in st.session_state:
    st.session_state.timer = 60

if "auction_phase" not in st.session_state:
    st.session_state.auction_phase = "bidding"

if "pause_timer" not in st.session_state:
    st.session_state.pause_timer = 10

if "auction_paused" not in st.session_state:
    st.session_state.auction_paused = False

if "starting_budget" not in st.session_state:
    st.session_state.starting_budget = 1000

# =========================
# FUNCTIONS
# =========================
def format_money(amount):

    if amount >= 1000:

        billions = amount / 1000

        return f"€{billions:.1f}B"

    return f"€{amount}M"


def add_log(text):

    st.session_state.logs.insert(0, text)


def next_player():

    if len(st.session_state.available_players) == 0:

        st.balloons()

        st.success("🏆 Auction Finished")

        leaderboard = []

        for name, data in st.session_state.teams.items():

            total = sum(
                p["value"]
                for p in data["players"]
            )

            leaderboard.append((name, total))

        leaderboard.sort(
            key=lambda x: x[1],
            reverse=True
        )

        st.subheader("🏅 Final Leaderboard")

        for idx, (team, score) in enumerate(leaderboard):

            st.write(
                f"{idx+1}. {team} — {score} Points"
            )

        st.stop()

    st.session_state.current_player = random.choice(
        st.session_state.available_players
    )

    st.session_state.highest_bid = (
        st.session_state.current_player["value"]
    )

    st.session_state.highest_bidder = "No bids"

    st.session_state.timer = 60

    st.session_state.auction_phase = "bidding"


def sell_player():

    player = st.session_state.current_player

    winner = st.session_state.highest_bidder

    if winner == "No bids":

        add_log(
            f"❌ {player['name']} went UNSOLD"
        )

        st.session_state.available_players.remove(
            player
        )

        st.session_state.auction_phase = "pause"

        st.session_state.pause_timer = 10

        return

    st.session_state.teams[winner]["players"].append(
        player
    )

    st.session_state.teams[winner]["purse"] -= (
        st.session_state.highest_bid
    )

    st.session_state.available_players.remove(
        player
    )

    add_log(
        f"🏆 {winner} bought {player['name']} for {format_money(st.session_state.highest_bid)}"
    )

    st.session_state.auction_phase = "pause"

    st.session_state.pause_timer = 10

# =========================
# TIMER LOGIC
# =========================
if not st.session_state.auction_paused:

    if st.session_state.auction_phase == "bidding":

        st.session_state.timer -= 1

        if st.session_state.timer <= 0:

            sell_player()

    elif st.session_state.auction_phase == "pause":

        st.session_state.pause_timer -= 1

        if st.session_state.pause_timer <= 0:

            next_player()

# =========================
# SIDEBAR
# =========================
st.sidebar.title("⚙ Auction Settings")

view_mode = st.sidebar.selectbox(
    "Choose View",
    ["Player", "Admin"]
)

team_name = st.sidebar.text_input(
    "Your Team Name"
)

# =========================
# ADMIN
# =========================
is_admin = False

if view_mode == "Admin":

    password = st.sidebar.text_input(
        "Admin Password",
        type="password"
    )

    if password == ADMIN_PASSWORD:

        is_admin = True

        st.sidebar.subheader("💰 Auction Budget")

        st.session_state.starting_budget = st.sidebar.number_input(
            "Starting Purse (Millions)",
            min_value=100,
            value=1000,
            step=100
        )

# =========================
# TEAM CREATION
# =========================
if team_name:

    if team_name not in st.session_state.teams:

        st.session_state.teams[team_name] = {

            "purse": st.session_state.starting_budget,

            "players": []
        }

# =========================
# TITLE
# =========================
st.markdown(
    """
    <div class='big-title'>
    ⚽ Football Auction V6
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# =========================
# PLAYER DISPLAY
# =========================
player = st.session_state.current_player

c1, c2, c3 = st.columns([2,1,1])

with c1:

    st.markdown(
        f"""
        <div class='card'>

        <h1>{player['name']}</h1>

        <h2>{player['club']}</h2>

        <h3>{player['position']}</h3>

        <h2>Base Price: {format_money(player['value'])}</h2>

        </div>
        """,
        unsafe_allow_html=True
    )

with c2:

    st.markdown(
        f"""
        <div class='card center'>

        <h2>Highest Bid</h2>

        <h1>{format_money(st.session_state.highest_bid)}</h1>

        <h3>{st.session_state.highest_bidder}</h3>

        </div>
        """,
        unsafe_allow_html=True
    )

with c3:

    if st.session_state.auction_phase == "bidding":

        st.markdown(
            f"""
            <div class='card'>

            <h2 class='center'>Timer</h2>

            <div class='timer'>
            {st.session_state.timer}s
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            f"""
            <div class='card'>

            <h2 class='center'>Next Player In</h2>

            <div class='timer'>
            {st.session_state.pause_timer}s
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# PAUSED
# =========================
if st.session_state.auction_paused:

    st.warning("⏸ Auction Paused")

# =========================
# PLAYER VIEW
# =========================
if view_mode == "Player":

    st.divider()

    st.subheader("💸 Place Bid")

    if st.session_state.auction_phase == "bidding":

        b1, b2, b3, b4, b5 = st.columns(5)

        increments = [5,10,20,50,100]

        for col, amount in zip(
            [b1,b2,b3,b4,b5],
            increments
        ):

            with col:

                st.markdown(
                    "<div class='bid-btn'>",
                    unsafe_allow_html=True
                )

                if st.button(f"+{amount}"):

                    if team_name:

                        team = st.session_state.teams[team_name]

                        if len(team["players"]) < MAX_SQUAD_SIZE:

                            bid = (
                                st.session_state.highest_bid
                                + amount
                            )

                            if bid <= team["purse"]:

                                st.session_state.highest_bid = bid

                                st.session_state.highest_bidder = team_name

                                if st.session_state.timer > 30:

                                    st.session_state.timer = 30

                                add_log(
                                    f"💸 {team_name} bid {format_money(bid)}"
                                )

                                st.rerun()

                st.markdown(
                    "</div>",
                    unsafe_allow_html=True
                )

    st.divider()

    if team_name:

        team = st.session_state.teams[team_name]

        st.subheader(f"🏟 {team_name}")

        x1, x2 = st.columns(2)

        with x1:

            st.metric(
                "💰 Budget Left",
                format_money(team["purse"])
            )

        with x2:

            spent = (
                st.session_state.starting_budget
                - team["purse"]
            )

            st.metric(
                "💸 Money Spent",
                format_money(spent)
            )

        st.write(
            f"👥 Squad Size: {len(team['players'])}/{MAX_SQUAD_SIZE}"
        )

        st.subheader("📋 Your Players")

        for p in team["players"]:

            st.write(
                f"• {p['name']} ({p['position']})"
            )

# =========================
# ADMIN VIEW
# =========================
if is_admin:

    st.divider()

    st.subheader("🛠 Admin Controls")

    a1, a2, a3 = st.columns(3)

    with a1:

        if st.button("🎲 Skip Player"):

            st.session_state.available_players.remove(
                st.session_state.current_player
            )

            next_player()

            st.rerun()

    with a2:

        if st.button("⏸ Pause"):

            st.session_state.auction_paused = True

            st.rerun()

    with a3:

        if st.button("▶ Resume"):

            st.session_state.auction_paused = False

            st.rerun()

    st.divider()

    st.subheader("👥 All Teams")

    for name, data in st.session_state.teams.items():

        st.markdown(
            f"""
            <div class='card'>

            <h2>{name}</h2>

            <p>Budget: {format_money(data['purse'])}</p>

            <p>Players: {len(data['players'])}</p>

            </div>
            """,
            unsafe_allow_html=True
        )

        for p in data["players"]:

            st.write(
                f"• {p['name']} ({p['position']})"
            )

        st.divider()

# =========================
# LOGS
# =========================
st.divider()

st.subheader("📜 Auction Logs")

for log in st.session_state.logs[:15]:

    st.write(log)