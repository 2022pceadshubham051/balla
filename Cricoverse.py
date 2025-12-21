"""
CRICOVERSE - Professional Hand Cricket Telegram Bot
A feature-rich, group-based Hand Cricket game engine
Single file implementation - Part 1 of 10
"""

import logging
import asyncio
import random
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
from enum import Enum

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatMember
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, Forbidden

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ChatMember,
    InputMediaPhoto
)
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# CRITICAL: Set your bot token and owner ID here
BOT_TOKEN = "8428604292:AAGOkKYweTyb-moVTMPCrQkAgRPwIhQ1s5k"
OWNER_ID = 7460266461  # Replace with your Telegram user ID
SUPPORT_GROUP_ID = -1002707382739  # Replace with your support group ID

# Game Constants
class GamePhase(Enum):
    IDLE = "idle"
    TEAM_JOINING = "team_joining"
    HOST_SELECTION = "host_selection"
    CAPTAIN_SELECTION = "captain_selection"
    TEAM_EDIT = "team_edit"
    OVER_SELECTION = "over_selection"
    TOSS = "toss"
    MATCH_IN_PROGRESS = "match_in_progress"
    INNINGS_BREAK = "innings_break"
    MATCH_ENDED = "match_ended"
    SUPER_OVER = "super_over"

class MatchEvent(Enum):
    DOT_BALL = "dot"
    RUNS_1 = "1run"
    RUNS_2 = "2runs"
    RUNS_3 = "3runs"
    RUNS_4 = "4runs"
    RUNS_5 = "5runs"
    RUNS_6 = "6runs"
    WICKET = "wicket"
    NO_BALL = "noball"
    WIDE = "wide"
    FREE_HIT = "freehit"
    DRS_REVIEW = "drs_review"
    DRS_OUT = "drs_out"
    DRS_NOT_OUT = "drs_notout"
    INNINGS_BREAK = "innings_break"
    VICTORY = "victory"

# GIF URLs for match events
GIFS = {
    MatchEvent.DOT_BALL: [
        "https://t.me/cricoverse/48"
    ],
    MatchEvent.RUNS_1: [
        "https://t.me/cricoverse/47"
    ],
    MatchEvent.RUNS_2: [
        "https://t.me/cricoverse/46",
        "https://t.me/cricoverse/45",
    ],
    MatchEvent.RUNS_3: [
        "https://t.me/cricoverse/44"
    ],
    MatchEvent.RUNS_4: [
        "https://t.me/cricoverse/39",
        "https://t.me/cricoverse/40",
        "https://t.me/cricoverse/41",
        "https://t.me/cricoverse/42"
    ],
    MatchEvent.RUNS_5: [
        "https://t.me/cricoverse/43"
    ],
    MatchEvent.RUNS_6: [
        "https://t.me/cricoverse/16",
        "https://t.me/cricoverse/17",
        "https://t.me/cricoverse/18",
        "https://t.me/cricoverse/19",
        "https://t.me/cricoverse/20",
        "https://t.me/cricoverse/21",
        "https://t.me/cricoverse/22",
        "https://t.me/cricoverse/23",
        "https://t.me/cricoverse/24",
    ],
    MatchEvent.WICKET: [
        "https://t.me/cricoverse/27",
        "https://t.me/cricoverse/28",
        "https://t.me/cricoverse/29",
        "https://t.me/cricoverse/30",
        "https://t.me/cricoverse/31",
        "https://t.me/cricoverse/32",
        "https://t.me/cricoverse/33",
        "https://t.me/cricoverse/34",
        "https://t.me/cricoverse/35",
        "https://t.me/cricoverse/36"
    ],
    MatchEvent.NO_BALL: [
        "https://tenor.com/bBvYA.gif"
    ],
    MatchEvent.WIDE: [
        "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExbWdubjB0YmVuZnMwdXBwODg5MzZ0cjFsNWl4ZXN1MzltOW1yZng5dCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YtI7H5jotPvh9Z09t6/giphy.gif"
    ],
    MatchEvent.FREE_HIT: [
        "https://t.me/cricoverse/42"
    ],
    MatchEvent.DRS_REVIEW: [
        "https://t.me/cricoverse/37"
    ],
    MatchEvent.DRS_OUT: [
        "https://pin.it/4HD5YcJOA"
    ],
    MatchEvent.DRS_NOT_OUT: [
        "https://tenor.com/bOVyJ.gif"
    ],
    MatchEvent.INNINGS_BREAK: [
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExamVxZW82NjQ4eGliN2FzdjNka3d0a3k5cHIwb2Z1NmQ0eDhvNWp0dCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/fEcrGaUxQut19MBGAm/giphy.gif"
    ],
    MatchEvent.VICTORY: [
        "https://pin.it/7mnhh5b11",
        "https://pin.it/6TshMcDa0"
    ],
    "cheer":  ["https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcTFudnkxcWhzZmFlazQ2MHN6emY2c3JjY3J4MWV2Z2JjdzRkcGVyOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/humidv0MqqdO5ZoYhn/giphy.gif" ]

}

# --- GLOBAL HELPER FUNCTION ---
def get_user_tag(user):
    """Returns a clickable HTML link for the user"""
    if not user:
        return "Unknown"
    # Clean the name to prevent HTML errors
    first_name = user.first_name.replace("<", "&lt;").replace(">", "&gt;")
    return f"<a href='tg://user?id={user.id}'>{first_name}</a>"

# 🎨 GLOBAL MEDIA ASSETS (Safe Placeholders)
MEDIA_ASSETS = {
    "welcome": "https://t.me/cricoverse/5",
    "help": "https://t.me/cricoverse/6",
    "mode_select": "https://t.me/cricoverse/7",
    "joining": "https://t.me/cricoverse/8",
    "host": "https://t.me/cricoverse/9",
    "stats": "https://t.me/cricoverse/11",
    "squads": "https://t.me/cricoverse/15",
    "toss": "https://t.me/cricoverse/10",
    "h2h": "https://t.me/cricoverse/12",
    "botstats": "https://placehold.co/600x400/2c3e50/ffffff.png?text=System+Dashboard",
    "scorecard": "https://t.me/cricoverse/14" # Scorecard BG
}

# Commentary templates
# Ultimate Professional English Commentary (Expanded)
COMMENTARY = {
    "dot": [
        "Solid defense! No run conceded. 🧱",
        "Beaten! That was a jaffa! 🔥",
        "Straight to the fielder. Dot ball. 😐",
        "Swing and a miss! The batsman had no clue. 💨",
        "Dot ball. Pressure is building up on the batting side! 😰",
        "Respect the bowler! Good delivery in the corridor of uncertainty. 🙌",
        "No run there. Excellent fielding inside the circle. 🤐",
        "Played back to the bowler. 🤚",
        "A loud shout for LBW, but turned down. Dot ball. 🔉",
        "Good line and length. The batsman leaves it alone. 👀",
        "Can't get it through the gap. Frustration growing! 😤",
        "Top class bowling! Giving nothing away. 🔒",
        "Defended with a straight bat. Textbook cricket. 📚",
        "The batsman is struggling to time the ball. 🐢",
        "Another dot! The required run rate is creeping up. 📈"
    ],
    "single": [
        "Quick single! Good running between the wickets. 🏃‍♂️",
        "Push and run! Strike rotated smartly. 🔄",
        "Just a single added to the tally. 1️⃣",
        "Good call! One run completed safely. 👟",
        "Direct hit missed! That was close. 🎯",
        "Tucked away off the hips for a single. 🏏",
        "Dropped at his feet and they scamper through. ⚡",
        "Fielder fumbles, and they steal a run. 🤲",
        "Sensible batting. Taking the single on offer. 🧠",
        "Driven to long-on for one. 🚶",
        "Smart cricket! Rotating the strike to keep the scoreboard ticking. ⏱️",
        "A little hesitation, but they make it in the end. 😅"
    ],
    "double": [
        "In the gap! They will get two easily. ✌️",
        "Great running between the wickets! Two runs added. 🏃‍♂️🏃‍♂️",
        "Pushed hard for the second! Excellent fitness shown. 💪",
        "Fielder was slow to react! They steal a couple. 😴",
        "Two runs added. Good placement into the deep. ⚡",
        "They turn for the second run immediately! Aggressive running. ⏩",
        "Misfield allows them to come back for two. 🤦‍♂️",
        "Good throw from the deep, but the batsman is safe. ⚾",
        "Calculated risk taken for the second run! ✅",
        "The fielder cuts it off, but they get a couple. 🛡️"
    ],
    "triple": [
        "Superb fielding effort! Saved the boundary just in time. 🛑 3 runs.",
        "They are running hard! Three runs taken. 🏃‍♂️💨",
        "Excellent stamina! Pushing for the third run. 🔋",
        "Just short of the boundary! 3 runs added to the score. 🚧",
        "The outfield is slow, the ball stops just before the rope. 🐢",
        "Great relay throw! But they collect three runs. 🤝"
    ],
    "boundary": [
        "CRACKING SHOT! Raced to the fence like a bullet! 🚀 FOUR!",
        "What timing! Found the gap perfectly. 🏎️ 4 Runs!",
        "Beautiful Cover Drive! That is a textbook shot! 😍",
        "The fielder is just a spectator! That's a boundary! 👀",
        "One bounce and over the rope! Four runs! 🎾",
        "Misfield and four! The bowler is absolutely furious. 😠",
        "Surgical precision! Cut away past point for FOUR! 🔪",
        "Pulled away powerfully! No chance for the fielder. 🤠",
        "Straight down the ground! Umpire had to duck! 🦆 FOUR!",
        "Edged but it flies past the slip cordon! Lucky boundary. 🍀",
        "Swept away fine! The fielder gives chase in vain. 🧹",
        "That was pure elegance! Caressed to the boundary. ✨",
        "Power and placement! A terrific shot for four. 💪",
        "Short ball punished! Dispatched to the fence. 👮‍♂️",
        "Drilled through the covers! What a sound off the bat! 🔊"
    ],
    "five": [
        "FIVE RUNS! Overthrows! Bonus runs for the team. 🎁",
        "Comedy of errors on the field! 5 runs conceded. 🤡",
        "Running for five! Incredible stamina displayed! 🏃‍♂️💨",
        "Bonus runs! The batting team is delighted with that gift. 🎉",
        "Throw hits the stumps and deflects away! 5 runs! 🎱"
    ],
    "six": [
        "HUGE! That's out of the stadium! 🌌 SIX!",
        "Muscle power! Sent into orbit! 💪",
        "MAXIMUM! What a clean connection! 💥",
        "It's raining sixes! Destruction mode activated! 🔨",
        "Helicopter Shot! That is magnificent! 🚁",
        "That's a monster hit! The bowler looks devastated. 😭",
        "Gone with the wind! High and handsome! 🌬️",
        "That ball is in the parking lot! Fetch that! 🚗",
        "Clean striking! It's landed in the top tier! 🏟️",
        "Upper cut sails over third man! What a shot! ✂️",
        "Smoked down the ground! That is a massive six! 🚬",
        "The crowd catches it! That's a fan favorite shot! 🙌",
        "Pick that up! Sent traveling into the night sky! 🚀",
        "Pure timing! He didn't even try to hit that hard. 🪄",
        "The bowler missed the yorker, and it's gone for SIX! 📏"
    ],
    "wicket": [
        "OUT! Game over for the batsman! ❌",
        "Clean Bowled! Shattered the stumps! 🪵",
        "Caught! Fielder makes no mistake. Wicket! 👐",
        "Gone! The big fish is in the net! 🎣",
        "Edged and taken! A costly mistake by the batsman. 🏏",
        "Stumping! Lightning fast hands by the keeper! ⚡",
        "Run Out! A terrible mix-up in the middle. 🚦",
        "LBW! That looked plumb! The finger goes up! ☝️",
        "Caught and Bowled! Great reflexes by the bowler! 🤲",
        "Hit Wicket! Oh no, he stepped on his own stumps! 😱",
        "The partnership is broken! Massive moment in the game. 💔",
        "He has holed out to the deep! End of a good innings. 🔚",
        "Golden Duck! He goes back without troubling the scorers. 🦆",
        "The stumps are taking a walk! cartwheeling away! 🤸‍♂️",
        "What a catch! He plucked that out of thin air! 🦅"
    ],
    "noball": [
        "NO BALL! Overstepped the line! 🚨",
        "Free Hit coming up! A free swing for the batsman! 🔥",
        "Illegal delivery. Umpire signals No Ball. 🙅‍♂️",
        "That was a beamer! Dangerous delivery. No Ball. 🤕",
        "Bowler loses his grip. No Ball called. 🧼"
    ],
    "wide": [
        "Wide Ball! Radar is off. 📡",
        "Too wide! Extra run conceded. 🎁",
        "Wayward delivery. Drifting down the leg side. 🚌",
        "Too high! Umpire signals a wide for height. 🦒",
        "Spilled down the leg side. Keeper collects it. Wide. 🧤"
    ]
}

# Data storage paths
DATA_DIR = "cricoverse_data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MATCHES_FILE = os.path.join(DATA_DIR, "matches.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
ACHIEVEMENTS_FILE = os.path.join(DATA_DIR, "achievements.json")
GROUPS_FILE = os.path.join(DATA_DIR, "groups.json")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Global data structures
active_matches: Dict[int, 'Match'] = {}
user_data: Dict[int, Dict] = {}
match_history: List[Dict] = []
player_stats: Dict[int, Dict] = {}
achievements: Dict[int, List[str]] = {}
registered_groups: Dict[int, Dict] = {}
bot_start_time = time.time()

# Initialize data structures from files
def load_data():
    """Load all data from JSON files"""
    global user_data, match_history, player_stats, achievements, registered_groups
    
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                user_data = {int(k): v for k, v in json.load(f).items()}
        
        if os.path.exists(MATCHES_FILE):
            with open(MATCHES_FILE, 'r') as f:
                match_history = json.load(f)
        
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r') as f:
                player_stats = {int(k): v for k, v in json.load(f).items()}
        
        if os.path.exists(ACHIEVEMENTS_FILE):
            with open(ACHIEVEMENTS_FILE, 'r') as f:
                achievements = {int(k): v for k, v in json.load(f).items()}
        
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, 'r') as f:
                registered_groups = {int(k): v for k, v in json.load(f).items()}
        
        logger.info("Data loaded successfully")
    except Exception as e:
        logger.error(f"Error loading data: {e}")

def save_data():
    """Save all data to JSON files"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(user_data, f, indent=2)
        
        with open(MATCHES_FILE, 'w') as f:
            json.dump(match_history, f, indent=2)
        
        with open(STATS_FILE, 'w') as f:
            json.dump(player_stats, f, indent=2)
        
        with open(ACHIEVEMENTS_FILE, 'w') as f:
            json.dump(achievements, f, indent=2)
        
        with open(GROUPS_FILE, 'w') as f:
            json.dump(registered_groups, f, indent=2)
        
        logger.info("Data saved successfully")
    except Exception as e:
        logger.error(f"Error saving data: {e}")

# Initialize player stats for a user
def init_player_stats(user_id: int):
    """Initialize stats structure for a new player"""
    if user_id not in player_stats:
        player_stats[user_id] = {
            "matches_played": 0,
            "matches_won": 0,
            "total_runs": 0,
            "total_balls_faced": 0,
            "total_wickets": 0,
            "total_balls_bowled": 0,
            "total_runs_conceded": 0,
            "centuries": 0,
            "half_centuries": 0,
            "highest_score": 0,
            "best_bowling": {"wickets": 0, "runs": 999},
            "dot_balls_bowled": 0,
            "dot_balls_faced": 0,
            "boundaries": 0,
            "sixes": 0,
            "ducks": 0,
            "last_5_scores": [],
            "last_5_wickets": [],
            "venue_stats": {},
            "vs_player_stats": {},
            "total_timeouts": 0,
            "total_no_balls": 0,
            "total_wides": 0
        }
        save_data()

# Player class to track individual player performance in a match
class Player:
    """Represents a player in the match"""
    def __init__(self, user_id: int, username: str, first_name: str):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.runs = 0
        self.balls_faced = 0
        self.wickets = 0
        self.balls_bowled = 0
        self.runs_conceded = 0
        self.is_out = False
        self.dismissal_type = None
        self.dot_balls_faced = 0
        self.dot_balls_bowled = 0
        self.boundaries = 0
        self.sixes = 0
        self.overs_bowled = 0
        self.maiden_overs = 0
        self.no_balls = 0
        self.wides = 0
        self.has_bowled_this_over = False
        self.batting_timeouts = 0
        self.bowling_timeouts = 0
        self.is_bowling_banned = False
    
    def get_strike_rate(self) -> float:
        """Calculate batting strike rate"""
        if self.balls_faced == 0:
            return 0.0
        return round((self.runs / self.balls_faced) * 100, 2)
    
    def get_economy(self) -> float:
        """Calculate bowling economy rate"""
        if self.balls_bowled == 0:
            return 0.0
        overs = self.balls_bowled / 6
        if overs == 0:
            return 0.0
        return round(self.runs_conceded / overs, 2)
    
    def get_bowling_average(self) -> float:
        """Calculate bowling average"""
        if self.wickets == 0:
            return 0.0
        return round(self.runs_conceded / self.wickets, 2)

# Team class
class Team:
    """Represents a team in the match"""
    def __init__(self, name: str):
        self.name = name
        self.players: List[Player] = []
        self.captain_id: Optional[int] = None
        self.score = 0
        self.wickets = 0
        self.overs = 0.0
        self.balls = 0
        self.extras = 0
        self.drs_remaining = 1
        
        # Real Cricket Support
        self.current_batsman_idx: Optional[int] = None      # Striker
        self.current_non_striker_idx: Optional[int] = None  # Non-Striker
        self.out_players_indices = set() # Track who is out
        
        self.current_bowler_idx: Optional[int] = None
        self.penalty_runs = 0
        self.bowler_history: List[int] = []

    def is_all_out(self):
        # 1 player needs to remain not out to partner. If (Total - Out) < 2, then All Out.
        return (len(self.players) - len(self.out_players_indices)) < 2

    def swap_batsmen(self):
        """Swap Striker and Non-Striker"""
        if self.current_batsman_idx is not None and self.current_non_striker_idx is not None:
            self.current_batsman_idx, self.current_non_striker_idx = self.current_non_striker_idx, self.current_batsman_idx

    def add_player(self, player: Player):
        self.players.append(player)
    
    def remove_player(self, user_id: int) -> bool:
        for i, player in enumerate(self.players):
            if player.user_id == user_id:
                self.players.pop(i)
                return True
        return False
    
    def get_player(self, user_id: int) -> Optional[Player]:
        for player in self.players:
            if player.user_id == user_id:
                return player
        return None
    
    def get_player_by_serial(self, serial: int) -> Optional[Player]:
        if 1 <= serial <= len(self.players):
            return self.players[serial - 1]
        return None
    
    def get_available_bowlers(self) -> List[Player]:
        available = []
        last_bowler_idx = self.bowler_history[-1] if self.bowler_history else None
        
        for i, player in enumerate(self.players):
            if not player.is_bowling_banned and i != last_bowler_idx:
                available.append(player)
        return available
    
    def update_overs(self):
        """Update overs correctly - ball 1 = 0.1"""
        self.balls += 1
        complete_overs = (self.balls - 1) // 6  # -1 to make first ball = 0.1
        balls_in_over = ((self.balls - 1) % 6) + 1
        self.overs = complete_overs + (balls_in_over / 10)
    
    def get_current_over_balls(self) -> int:
        """Get balls in current over (1-6)"""
        return ((self.balls - 1) % 6) + 1 if self.balls > 0 else 0
    
    def complete_over(self):
        """Complete the current over"""
        remaining_balls = 6 - (self.balls % 6)
        self.balls += remaining_balls
        self.overs = self.balls // 6

# Match class - Core game engine
class Match:
    """Main match class that handles all game logic"""
    def __init__(self, group_id: int, group_name: str):
        self.group_id = group_id
        self.group_name = group_name
        self.phase = GamePhase.TEAM_JOINING
        self.match_id = f"{group_id}_{int(time.time())}"
        self.created_at = datetime.now()
        self.last_activity = time.time()  # Track last move time
        
        # Teams
        self.team_x = Team("Team X")
        self.team_y = Team("Team Y")
        self.editing_team: Optional[str] = None  # 'X' ya 'Y' store karega
        
        # Match settings
        self.host_id: Optional[int] = None
        self.total_overs = 0
        self.toss_winner: Optional[Team] = None
        self.batting_first: Optional[Team] = None
        self.bowling_first: Optional[Team] = None
        self.current_batting_team: Optional[Team] = None
        self.current_bowling_team: Optional[Team] = None
        
        # Match state
        self.innings = 1
        self.target = 0
        self.is_free_hit = False
        self.last_wicket_ball = None
        self.drs_in_progress = False
        self.team_x_timeout_used = False
        self.team_y_timeout_used = False
        
        # Timers and messages
        self.team_join_end_time: Optional[float] = None
        self.main_message_id: Optional[int] = None
        self.join_phase_task: Optional[asyncio.Task] = None
        
        # Ball tracking
        self.current_ball_data: Dict = {}
        self.ball_timeout_task: Optional[asyncio.Task] = None
        self.batsman_selection_task: Optional[asyncio.Task] = None
        self.bowler_selection_task: Optional[asyncio.Task] = None
        
        # Waiting states
        self.waiting_for_batsman = False
        self.waiting_for_bowler = False
        self.batsman_selection_time: Optional[float] = None
        self.bowler_selection_time: Optional[float] = None
        
        # Super over
        self.is_super_over = False
        self.super_over_batting_team: Optional[Team] = None
        
        # Match log
        self.ball_by_ball_log: List[Dict] = []
        self.match_events: List[str] = []
    
    def get_team_by_name(self, name: str) -> Optional[Team]:
        """Get team by name"""
        if name == "Team X":
            return self.team_x
        elif name == "Team Y":
            return self.team_y
        return None
    
    def get_other_team(self, team: Team) -> Team:
        """Get the opposing team"""
        if team == self.team_x:
            return self.team_y
        return self.team_x
    
    def get_captain(self, team: Team) -> Optional[Player]:
        """Get team captain"""
        if team.captain_id:
            return team.get_player(team.captain_id)
        return None
    
    def add_event(self, event: str):
        """Add event to match log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.match_events.append(f"[{timestamp}] {event}")
    
    def get_required_run_rate(self) -> float:
        """Calculate required run rate for chasing team"""
        if self.innings != 2 or not self.current_batting_team:
            return 0.0
        
        runs_needed = self.target - self.current_batting_team.score
        balls_remaining = (self.total_overs * 6) - self.current_batting_team.balls
        
        if balls_remaining <= 0:
            return 0.0
        
        overs_remaining = balls_remaining / 6
        return round(runs_needed / overs_remaining, 2)
    
    def is_innings_complete(self) -> bool:
        """Check if current innings is complete"""
        if not self.current_batting_team or not self.current_bowling_team:
            return False
        
        # All out
        if self.current_batting_team.wickets >= len(self.current_batting_team.players) - 1:
            return True
        
        # Overs complete
        if self.current_batting_team.balls >= self.total_overs * 6:
            return True
        
        # Target chased in second innings
        if self.innings == 2 and self.current_batting_team.score >= self.target:
            return True
        
        return False
    
    def get_match_summary(self) -> str:
        """Generate detailed match summary"""
        summary_lines = []
        summary_lines.append("=" * 40)
        summary_lines.append("MATCH SUMMARY")
        summary_lines.append("=" * 40)
        summary_lines.append("")
        
        # First innings
        first_team = self.batting_first
        if first_team:
            summary_lines.append(f"{first_team.name}: {first_team.score}/{first_team.wickets}")
            summary_lines.append(f"Overs: {first_team.overs}")
            summary_lines.append("")
        
        # Second innings
        if self.innings >= 2:
            second_team = self.get_other_team(first_team)
            summary_lines.append(f"{second_team.name}: {second_team.score}/{second_team.wickets}")
            summary_lines.append(f"Overs: {second_team.overs}")
            summary_lines.append("")
        
        summary_lines.append("=" * 40)
        return "\n".join(summary_lines)

# Utility functions
def get_random_gif(event: MatchEvent) -> str:
    """Get random GIF for an event"""
    gifs = GIFS.get(event, [])
    if gifs:
        return random.choice(gifs)
    return ""

def get_random_commentary(event_type: str) -> str:
    """Get random commentary for an event"""
    comments = COMMENTARY.get(event_type, [])
    if comments:
        return random.choice(comments)
    return ""

def format_overs(balls: int) -> str:
    """Format balls to overs - First ball = 0.1"""
    if balls == 0:
        return "0.0"
    
    complete_overs = (balls - 1) // 6
    balls_in_over = ((balls - 1) % 6) + 1
    
    return f"{complete_overs}.{balls_in_over}"

def balls_to_float_overs(balls: int) -> float:
    """Convert balls to float overs"""
    return balls // 6 + (balls % 6) / 10

async def update_joining_board(context: ContextTypes.DEFAULT_TYPE, chat_id: int, match: Match):
    """
    Updates the Joining Board safely (Handling Photo Caption vs Text)
    """
    if not match.main_message_id: return

    # Generate fresh text
    text = get_team_join_message(match)
    
    # Buttons
    keyboard = [
        [InlineKeyboardButton("🔵 Join Team X", callback_data="join_team_x"),
         InlineKeyboardButton("🔴 Join Team Y", callback_data="join_team_y")],
        [InlineKeyboardButton("🚪 Leave Team", callback_data="leave_team")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        # Try editing as Photo Caption first (Since we are using Images)
        await context.bot.edit_message_caption(
            chat_id=chat_id,
            message_id=match.main_message_id,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        error_str = str(e).lower()
        
        # Agar "message is not modified" error hai, toh ignore karo (Sab same hai)
        if "message is not modified" in error_str:
            return
            
        # Agar error aaya ki "there is no caption" implies it's a TEXT message (Fallback)
        # Toh hum text edit karenge
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=match.main_message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
        except Exception as text_e:
            # Agar phir bhi fail hua, toh log karo par crash mat hone do
            pass

async def refresh_game_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, match: Match, caption: str, reply_markup: InlineKeyboardMarkup = None, media_key: str = None):
    """Smart Update: Edits existing message safely with HTML"""
    
    # Try editing first
    if match.main_message_id:
        try:
            if media_key and media_key in MEDIA_ASSETS:
                media = InputMediaPhoto(media=MEDIA_ASSETS[media_key], caption=caption, parse_mode=ParseMode.HTML)
                await context.bot.edit_message_media(
                    chat_id=chat_id,
                    message_id=match.main_message_id,
                    media=media,
                    reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=match.main_message_id,
                    text=caption,
                    reply_markup=reply_markup,
                    parse_mode=ParseMode.HTML
                )
            return
        except Exception:
            pass # Edit failed (message deleted/too old), send new

    # Fallback: Send New
    try:
        if media_key and media_key in MEDIA_ASSETS:
            msg = await context.bot.send_photo(chat_id=chat_id, photo=MEDIA_ASSETS[media_key], caption=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        else:
            msg = await context.bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        
        match.main_message_id = msg.message_id
        try: await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
        except: pass
    except Exception as e:
        logger.error(f"Send failed: {e}")


# Is function ko add karo

# Important: Is function ko call karne ke liye niche wala update_team_edit_message use karo
async def update_team_edit_message(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Show Team Edit Panel (Final Fixed Version)"""
    
    # 1. Team List Text Generate Karo
    text = f"⚙️ <b>TEAM SETUP</b>\n━━━━━━━━━━━━━━━━━━━━━━\n"
    
    text += f"🔵 <b>Team X:</b>\n"
    for i, p in enumerate(match.team_x.players, 1):
        text += f"  {i}. {p.first_name}\n"
    if not match.team_x.players: text += "  (Empty)\n"
        
    text += f"\n🔴 <b>Team Y:</b>\n"
    for i, p in enumerate(match.team_y.players, 1):
        text += f"  {i}. {p.first_name}\n"
    if not match.team_y.players: text += "  (Empty)\n"
    text += "\n"

    # 2. Logic: Buttons based on State
    if match.editing_team:
        # --- SUB-MENU (Jab Edit Mode ON hai) ---
        text += f"🟢 <b>EDITING TEAM {match.editing_team}</b>\n"
        text += f"👉 Reply to user with <code>/add</code> to add.\n"
        text += f"👉 Reply to user with <code>/remove</code> to remove.\n"
        text += "👉 Click button below when done."
        
        # 'Done' button wapas Main Menu le jayega
        keyboard = [[InlineKeyboardButton(f"✅ Done with Team {match.editing_team}", callback_data="edit_back")]]
        
    else:
        # --- MAIN MENU (Team Select Karo) ---
        text += "👇 <b>Select a team to edit:</b>"
        keyboard = [
            # Note: Buttons ab 'edit_team_x' use kar rahe hain (no _mode)
            [InlineKeyboardButton("✏️ Edit Team X", callback_data="edit_team_x"), 
             InlineKeyboardButton("✏️ Edit Team Y", callback_data="edit_team_y")],
            [InlineKeyboardButton("✅ Finalize & Start", callback_data="team_edit_done")]
        ]

    await refresh_game_message(context, group_id, match, text, InlineKeyboardMarkup(keyboard), media_key="squads")

async def set_edit_team_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Edit Buttons & Set State Correctly"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    if user.id != match.host_id:
        await query.answer("⚠️ Only Host can edit!", show_alert=True)
        return

    # Button Logic (State Set Karo)
    if query.data == "edit_team_x":
        match.editing_team = "X"
    elif query.data == "edit_team_y":
        match.editing_team = "Y"
    elif query.data == "edit_back":
        match.editing_team = None # Back to Main Menu

    # UI Update Karo
    await update_team_edit_message(context, chat.id, match)

async def notify_support_group(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send notification to support group"""
    try:
        await context.bot.send_message(
            chat_id=SUPPORT_GROUP_ID,
            text=message
        )
    except Exception as e:
        logger.error(f"Failed to notify support group: {e}")

# --- CHEER COMMAND ---
async def cheer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cheer for a player by tagging them!"""
    chat = update.effective_chat
    user = update.effective_user
    
    # 1. Detect Target User
    target_name = "everyone"
    if update.message.reply_to_message:
        target_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        # Handle mentions like @username or text
        target_name = " ".join(context.args)

    # 2. Cheer Message
    cheer_msg = f"🎉 <b>CHEER SQUAD</b> 🎉\n"
    cheer_msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    cheer_msg += f"📣 <b>{user.first_name}</b> is screaming for <b>{target_name}</b>!\n\n"
    cheer_msg += "<i>\"COME ON! YOU GOT THIS! SHOW YOUR POWER! 🏏🔥\"</i>\n"
    cheer_msg += "━━━━━━━━━━━━━━━━━━━━━━"

    # 3. Send GIF
    await update.message.reply_animation(
        animation=MEDIA_ASSETS.get("cheer", "https://media.giphy.com/media/l41Yh18f5T01X55zW/giphy.gif"),
        caption=cheer_msg,
        parse_mode=ParseMode.HTML
    )


# --- SCORECARD COMMAND (Match Summary Style) ---
async def scorecard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed Match Scorecard with Top 3 Performers"""
    chat = update.effective_chat
    
    # 1. Check for Active Match
    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No live match running! Use /mystats for career stats.")
        return

    match = active_matches[chat.id]
    
    # --- Helper Functions for Top 3 ---
    def get_top_batsmen(team):
        # Sort by: Runs (High to Low), then Strike Rate
        return sorted(team.players, key=lambda p: (-p.runs, -p.get_strike_rate()))[:3]

    def get_top_bowlers(team):
        # Filter bowlers who have bowled at least 1 ball
        active_bowlers = [p for p in team.players if p.balls_bowled > 0]
        # Sort by: Wickets (High to Low), then Economy (Low to High)
        return sorted(active_bowlers, key=lambda p: (-p.wickets, p.get_economy()))[:3]

    # --- Generate Scorecard Text ---
    summary = "📊 <b>LIVE MATCH SCORECARD</b> 📊\n"
    summary += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # --- Team X Section ---
    summary += f"🔵 <b>{match.team_x.name}</b>: {match.team_x.score}/{match.team_x.wickets} ({match.team_x.overs})\n"
    
    # Top 3 Batting (Team X)
    summary += "🏏 <i>Batting</i>\n"
    top_bat_x = get_top_batsmen(match.team_x)
    if top_bat_x:
        for p in top_bat_x:
            status = "*" if not p.is_out else ""
            summary += f"• {p.first_name}{status}: <b>{p.runs}</b> ({p.balls_faced})\n"
    else:
        summary += "• <i>No batting data yet</i>\n"

    # Top 3 Bowling (Team X)
    summary += "⚾ <i>Bowling</i>\n"
    top_bowl_x = get_top_bowlers(match.team_x)
    if top_bowl_x:
        for p in top_bowl_x:
            summary += f"• {p.first_name}: <b>{p.wickets}/{p.runs_conceded}</b> ({format_overs(p.balls_bowled)})\n"
    else:
        summary += "• <i>No bowling data yet</i>\n"

    summary += "━━━━━━━━━━━━━━━━━━━━━━\n"

    # --- Team Y Section ---
    summary += f"🔴 <b>{match.team_y.name}</b>: {match.team_y.score}/{match.team_y.wickets} ({match.team_y.overs})\n"
    
    # Top 3 Batting (Team Y)
    summary += "🏏 <i>Batting</i>\n"
    top_bat_y = get_top_batsmen(match.team_y)
    if top_bat_y:
        for p in top_bat_y:
            status = "*" if not p.is_out else ""
            summary += f"• {p.first_name}{status}: <b>{p.runs}</b> ({p.balls_faced})\n"
    else:
        summary += "• <i>No batting data yet</i>\n"

    # Top 3 Bowling (Team Y)
    summary += "⚾ <i>Bowling</i>\n"
    top_bowl_y = get_top_bowlers(match.team_y)
    if top_bowl_y:
        for p in top_bowl_y:
            summary += f"• {p.first_name}: <b>{p.wickets}/{p.runs_conceded}</b> ({format_overs(p.balls_bowled)})\n"
    else:
        summary += "• <i>No bowling data yet</i>\n"
        
    summary += "━━━━━━━━━━━━━━━━━━━━━━"

    # 3. Send Image with Caption
    await update.message.reply_photo(
        photo=MEDIA_ASSETS.get("scorecard"),
        caption=summary,
        parse_mode=ParseMode.HTML
    )

async def cleanup_inactive_matches(context: ContextTypes.DEFAULT_TYPE):
    """Auto-end matches inactive for > 15 minutes"""
    current_time = time.time()
    inactive_threshold = 15 * 60  # 15 Minutes in seconds
    chats_to_remove = []

    # Check all active matches
    for chat_id, match in active_matches.items():
        if current_time - match.last_activity > inactive_threshold:
            chats_to_remove.append(chat_id)
            try:
                # Send Time Out Message
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⏰ <b>Game Timeout!</b>\nMatch ended automatically due to 15 mins of inactivity.",
                    parse_mode=ParseMode.HTML
                )
                # Unpin message
                if match.main_message_id:
                    await context.bot.unpin_chat_message(chat_id=chat_id, message_id=match.main_message_id)
            except Exception as e:
                logger.error(f"Error ending inactive match {chat_id}: {e}")

    # Remove from memory
    for chat_id in chats_to_remove:
        if chat_id in active_matches:
            del active_matches[chat_id]

async def game_timer(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, player_type: str, player_name: str):
    """Handles 45s timer with Penalties & Disqualification"""
    try:
        # Wait 30 seconds
        await asyncio.sleep(30)
        
        # Warning
        await context.bot.send_message(group_id, f"⏳ <b>Hurry Up {player_name}!</b> 15 seconds left!", parse_mode=ParseMode.HTML)
        
        # Wait remaining 15 seconds
        await asyncio.sleep(15)
        
        # --- TIMEOUT HAPPENED ---
        await handle_timeout_penalties(context, group_id, match, player_type)
            
    except asyncio.CancelledError:
        pass # Timer stopped safely because player played

async def handle_timeout_penalties(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, player_type: str):
    """Process Penalties for Timeouts"""
    bat_team = match.current_batting_team
    bowl_team = match.current_bowling_team
    
    # --- BOWLER TIMEOUT ---
    if player_type == "bowler":
        bowler = bowl_team.players[bowl_team.current_bowler_idx]
        bowler.bowling_timeouts += 1
        
        # Case A: Disqualification (3 Timeouts)
        if bowler.bowling_timeouts >= 3:
            msg = f"🚫 <b>DISQUALIFIED!</b> {bowler.first_name} timed out 3 times!\n"
            msg += "⚠️ <b>The over will RESTART with a new bowler.</b>"
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            # Reset Balls for this over (Over restart logic)
            # Example: If balls were 3.2 (20 balls), reset to 3.0 (18 balls)
            current_over_balls = bowl_team.get_current_over_balls()
            bowl_team.balls -= current_over_balls
            
            # Remove bowler from attack
            bowl_team.current_bowler_idx = None
            bowler.is_bowling_banned = True # Ban for this match (optional, or just this over)
            
            # Request New Bowler
            match.current_ball_data = {} # Clear ball data
            await request_bowler_selection(context, group_id, match)
            return

        # Case B: No Ball (Standard Timeout)
        else:
            bat_team.score += 1 # Penalty Run
            bat_team.extras += 1
            match.is_free_hit = True # Activate Free Hit
            
            msg = f"⏰ <b>BOWLER TIMEOUT!</b> ({bowler.bowling_timeouts}/3)\n"
            msg += "🚫 <b>Result:</b> NO BALL! (+1 Run)\n"
            msg += "⚡ <b>Next ball is a FREE HIT!</b>"
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            # Reset inputs to allow re-bowl (No ball doesn't count legal ball)
            match.current_ball_data = {"bowler_id": bowler.user_id, "bowler_number": None, "group_id": group_id}
            
            # Restart Bowler Timer for re-bowl
            match.ball_timeout_task = asyncio.create_task(game_timer(context, group_id, match, "bowler", bowler.first_name))
            
            # Notify Bowler again
            try: await context.bot.send_message(bowler.user_id, "⚠️ <b>Timeout! It's a No Ball. Bowl again!</b>", parse_mode=ParseMode.HTML)
            except: pass

    # --- BATSMAN TIMEOUT ---
    elif player_type == "batsman":
        striker = bat_team.players[bat_team.current_batsman_idx]
        striker.batting_timeouts += 1
        
        # Case A: Hit Wicket (3 Timeouts)
        if striker.batting_timeouts >= 3:
            msg = f"🚫 <b>DISMISSED!</b> {striker.first_name} timed out 3 times.\n"
            msg += "❌ <b>Result:</b> HIT WICKET (OUT)!"
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            # Trigger Wicket Logic Manually
            match.current_ball_data["batsman_number"] = match.current_ball_data["bowler_number"] # Force match numbers to trigger out
            await process_ball_result(context, group_id, match)
            
        # Case B: Penalty Runs (-6 Runs)
        else:
            bat_team.score -= 6
            bat_team.score = max(0, bat_team.score) # Score negative nahi jayega
            
            msg = f"⏰ <b>BATSMAN TIMEOUT!</b> ({striker.batting_timeouts}/3)\n"
            msg += "📉 <b>Penalty:</b> -6 Runs!\n"
            msg += f"📊 <b>Score:</b> {bat_team.score}/{bat_team.wickets}\n"
            msg += "🔄 <b>Ball Counted.</b> (Dot Ball)"
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            # Count ball but no runs (Treat as Dot Ball)
            bowl_team.update_overs()
            match.current_ball_data = {} # Reset
            
            if bowl_team.get_current_over_balls() == 0:
                await check_over_complete(context, group_id, match)
            else:
                await execute_ball(context, group_id, match)

async def taunt_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Light Taunt"""

    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No active match right now.")
        return

    taunts = [
        "😏 Is that all you got? We're just warming up!",
        "🤔 Did you even practice? This is too easy!",
        "😎 Thanks for the practice session! Who's next?",
        "🎭 Are we playing cricket or waiting for miracles?",
        "⚡ Blink and you'll miss our victory! Too fast for you?"
    ]

    msg = (
        f"💬 <b>{user.first_name}</b> throws a taunt!\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{random.choice(taunts)}"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def celebrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Celebration GIF"""

    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No active match right now.")
        return

    celebration_gifs = [
        "https://media.giphy.com/media/g9582DNuQppxC/giphy.gif",
        "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "https://media.giphy.com/media/Is1O1TWV0LEJi/giphy.gif"
    ]

    caption = (
        f"🎉 <b>{user.first_name}</b> celebrates in style! 🎊\n\n"
        "<i>\"YESSS! That's how it's done!\"</i> 🔥"
    )

    await update.message.reply_animation(
        animation=random.choice(celebration_gifs),
        caption=caption,
        parse_mode=ParseMode.HTML
    )


async def huddle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Team Motivation"""

    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No active match right now.")
        return

    huddle_messages = [
        "🔥 <b>COME ON TEAM!</b> We got this! Let's show them what we're made of! 💪",
        "⚡ <b>FOCUS UP!</b> One ball at a time. We're in this together! 🤝",
        "🎯 <b>STAY CALM!</b> Stick to the plan. Victory is ours! 🏆",
        "💥 <b>LET'S GO!</b> Time to dominate! Show no mercy! ⚔️",
        "🌟 <b>BELIEVE!</b> We've trained for this. Execute perfectly! ✨"
    ]

    msg = (
        f"📣 <b>{user.first_name}</b> calls a team huddle!\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{random.choice(huddle_messages)}"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


# Start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message with Support Notification"""
    user = update.effective_user
    chat = update.effective_chat
    
    is_new_user = False
    
    # User Init logic
    if user.id not in user_data:
        user_data[user.id] = {
            "user_id": user.id,
            "username": user.username or "",
            "first_name": user.first_name,
            "started_at": datetime.now().isoformat(),
            "total_matches": 0
        }
        init_player_stats(user.id)
        save_data()
        is_new_user = True

        # 📢 NOTIFY SUPPORT GROUP (New User)
        if chat.type == "private":
            try:
                await context.bot.send_message(
                    chat_id=SUPPORT_GROUP_ID,
                    text=f"🆕 <b>New User Started Bot</b>\n👤 {user.first_name} (<a href='tg://user?id={user.id}'>{user.id}</a>)\n🎈 @{user.username}",
                    parse_mode=ParseMode.HTML
                )
            except Exception: pass

    welcome_text = "🏏 <b>WELCOME TO CRICOVERSE</b> 🏏\n"
    welcome_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    welcome_text += "The ultimate Hand Cricket experience on Telegram.\n\n"
    welcome_text += "🔥 <b>Features:</b>\n"
    welcome_text += "• 🏟 Group Matches\n"
    welcome_text += "• 📺 DRS System\n"
    welcome_text += "• 📊 Career Stats\n"
    welcome_text += "• 🎙 Live Commentary\n\n"
    welcome_text += "👇 <b>How to Play:</b>\n"
    welcome_text += "Add me to your group and type <code>/game</code> to start!"

    
    if chat.type == "private":
        await update.message.reply_photo(photo=MEDIA_ASSETS["welcome"], caption=welcome_text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text("Bot is ready! Use /game to start.")

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help menu with Image"""
    msg = "❓ <b>CRICOVERSE GUIDE</b> ❓\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "🛠 <b>Host Commands:</b>\n"
    msg += "• <code>/game</code> - Start Match\n"
    msg += "• <code>/extend 60</code> - Add time\n"
    msg += "• <code>/endmatch</code> - Force stop\n\n"
    
    msg += "🧢 <b>Captain Commands:</b>\n"
    msg += "• <code>/batting 1</code> - Select Batsman\n"
    msg += "• <code>/bowling 1</code> - Select Bowler\n"
    msg += "• <code>/drs</code> - Take Review\n\n"
    
    msg += "📊 <b>General:</b>\n"
    msg += "• <code>/mystats</code> - Career Stats\n"
    msg += "• <code>/players</code> - Match Squads"
    
    await update.message.reply_photo(
        photo=MEDIA_ASSETS["help"],
        caption=msg,
        parse_mode=ParseMode.HTML
    )

# Game command - Entry point
async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Game start menu with New Group Notification"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        await update.message.reply_text("This command only works in groups!")
        return
    
    if chat.id in active_matches:
        await update.message.reply_text("⚠️ Match already in progress!")
        return
        
    # Check if New Group
    if chat.id not in registered_groups:
        registered_groups[chat.id] = {"group_id": chat.id, "group_name": chat.title, "total_matches": 0}
        save_data()
        
        # 📢 NOTIFY SUPPORT GROUP (New Group)
        try:
            invite_link = ""
            try: invite_link = await context.bot.export_chat_invite_link(chat.id)
            except: pass
            
            msg = f"🆕 <b>Bot Added to New Group</b>\n"
            msg += f"fw <b>{chat.title}</b>\n"
            msg += f"🆔 <code>{chat.id}</code>\n"
            msg += f"👤 Added by: {user.first_name}\n"
            if invite_link: msg += f"🔗 {invite_link}"
            
            await context.bot.send_message(chat_id=SUPPORT_GROUP_ID, text=msg, parse_mode=ParseMode.HTML)
        except Exception: pass
    
    keyboard = [
        [InlineKeyboardButton("👥 Team Mode", callback_data="mode_team")],
        [InlineKeyboardButton("🏆 Tournament (Soon)", callback_data="mode_tournament")]
    ]
    
    msg = "🎮 <b>SELECT GAME MODE</b> 🎮\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Choose how you want to play today!"
    
    await update.message.reply_photo(
        photo=MEDIA_ASSETS["mode_select"],
        caption=msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

# Callback query handler for mode selection
async def mode_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game mode selection safely"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    # ✅ FIX: Check if match is already active in this group
    if chat.id in active_matches:
        await query.message.edit_reply_markup(reply_markup=None) # Hide buttons of old menu
        await query.message.reply_text("⚠️ A match is already in progress in this group!", quote=True)
        return
    
    if query.data == "mode_solo":
        await query.edit_message_text("Solo Mode is coming soon. Please try Team Mode!")
        return
    
    if query.data == "mode_tournament":
        await query.edit_message_text("Tournament Mode is coming soon. Please try Team Mode!")
        return
    
    if query.data == "mode_team":
        # Start team mode
        await start_team_mode(query, context, chat, user)

async def start_team_mode(query, context: ContextTypes.DEFAULT_TYPE, chat, user):
    """Initialize team mode with Fancy Image"""
    # Create new match
    match = Match(chat.id, chat.title)
    active_matches[chat.id] = match
    
    # Set time (2 minutes)
    match.team_join_end_time = time.time() + 120
    
    # Buttons
    keyboard = [
        [InlineKeyboardButton("🔵 Join Team X", callback_data="join_team_x"),
         InlineKeyboardButton("🔴 Join Team Y", callback_data="join_team_y")],
        [InlineKeyboardButton("🚪 Leave Team", callback_data="leave_team")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Fancy Text
    text = get_team_join_message(match)
    
    # Send using Master Function (With Image)
    await refresh_game_message(context, chat.id, match, text, reply_markup, media_key="joining")
    
    # Start Timer
    match.join_phase_task = asyncio.create_task(
        team_join_countdown(context, chat.id, match)
    )

def get_team_join_message(match: Match) -> str:
    """Generate Professional Joining List"""
    remaining = max(0, int(match.team_join_end_time - time.time()))
    minutes = remaining // 60
    seconds = remaining % 60
    
    total_p = len(match.team_x.players) + len(match.team_y.players)
    
    msg = "🏆 <b>CRICOVERSE MATCH REGISTRATION</b> 🏆\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"⏳ <b>Time Remaining:</b> <code>{minutes:02d}:{seconds:02d}</code>\n"
    msg += f"👥 <b>Total Players:</b> {total_p}\n\n"
    
    # Team X List
    msg += "🔵 <b>TEAM X</b>\n"
    if match.team_x.players:
        for i, p in enumerate(match.team_x.players, 1):
            msg += f"  ├ {i}. {p.first_name}\n"
    else:
        msg += "  └ <i>Waiting for players...</i>\n"
    
    msg += "\n"
    
    # Team Y List
    msg += "🔴 <b>TEAM Y</b>\n"
    if match.team_y.players:
        for i, p in enumerate(match.team_y.players, 1):
            msg += f"  ├ {i}. {p.first_name}\n"
    else:
        msg += "  └ <i>Waiting for players...</i>\n"
            
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "<i>Click buttons below to join your squad!</i>"
    
    return msg

async def team_join_countdown(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Countdown timer that updates the Board safely"""
    try:
        warning_sent = False
        while True:
            # ✅ FIX: Agar Phase Joining nahi hai, to Timer band kar do
            if match.phase != GamePhase.TEAM_JOINING:
                break

            remaining = match.team_join_end_time - time.time()
            
            # 30 Seconds Warning
            if remaining <= 30 and remaining > 20 and not warning_sent:
                await context.bot.send_message(
                    group_id, 
                    "⚠️ <b>Hurry Up! Only 30 seconds left to join!</b>", 
                    parse_mode=ParseMode.HTML
                )
                warning_sent = True

            # Time Up
            if remaining <= 0:
                await end_team_join_phase(context, group_id, match)
                break
            
            # Wait 10 seconds
            await asyncio.sleep(10)
            
            # ✅ FIX: Update karne se pehle phir check karo
            if match.phase == GamePhase.TEAM_JOINING:
                await update_joining_board(context, group_id, match)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Timer error: {e}")

async def end_team_join_phase(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """End joining phase and start Host Selection"""
    total_players = len(match.team_x.players) + len(match.team_y.players)
    
    # Min 4 Players Check
    if total_players < 4:
        await context.bot.send_message(
            chat_id=group_id,
            text="❌ <b>Match Cancelled!</b>\nYou need at least 4 players (2 per team) to start.",
            parse_mode=ParseMode.HTML
        )
        try: await context.bot.unpin_chat_message(group_id, match.main_message_id)
        except: pass
        del active_matches[group_id]
        return
    
    match.phase = GamePhase.HOST_SELECTION
    
    keyboard = [[InlineKeyboardButton("🙋‍♂️ I Want to be Host", callback_data="become_host")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    host_text = f"✅ <b>REGISTRATION CLOSED!</b>\n"
    host_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    host_text += f"Total Players: <b>{total_players}</b>\n\n"
    host_text += "<b>Who wants to be the Host?</b>\n"
    host_text += "<i>Host will select overs and finalize the teams.</i>"
    
    # Send with Host Image and Pin
    await refresh_game_message(context, group_id, match, host_text, reply_markup, media_key="host")

# Team join/leave callback handlers
async def team_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle team join/leave with tagging alerts & Auto-Update"""
    query = update.callback_query
    
    # Quick answer to stop loading animation
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        return
    
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TEAM_JOINING:
        await context.bot.send_message(chat.id, "⚠️ Joining phase has ended!")
        return
    
    # Initialize User Data
    if user.id not in user_data:
        user_data[user.id] = {
            "user_id": user.id,
            "username": user.username or "",
            "first_name": user.first_name,
            "started_at": datetime.now().isoformat(),
            "total_matches": 0
        }
        init_player_stats(user.id)
        save_data()

    user_tag = f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
    alert_msg = ""
    updated = False

    # JOIN LOGIC
    if query.data == "join_team_x":
        if not match.team_x.get_player(user.id):
            if match.team_y.get_player(user.id):
                match.team_y.remove_player(user.id)
            
            player = Player(user.id, user.username or "", user.first_name)
            match.team_x.add_player(player)
            alert_msg = f"✅ {user_tag} joined <b>Team X</b>!"
            updated = True
    
    elif query.data == "join_team_y":
        if not match.team_y.get_player(user.id):
            if match.team_x.get_player(user.id):
                match.team_x.remove_player(user.id)
            
            player = Player(user.id, user.username or "", user.first_name)
            match.team_y.add_player(player)
            alert_msg = f"✅ {user_tag} joined <b>Team Y</b>!"
            updated = True
    
    elif query.data == "leave_team":
        if match.team_x.remove_player(user.id) or match.team_y.remove_player(user.id):
            alert_msg = f"👋 {user_tag} left the team."
            updated = True

    # 1. Send Alert in Group (Naya message)
    if alert_msg:
        await context.bot.send_message(chat.id, alert_msg, parse_mode=ParseMode.HTML)

    # 2. Update the Board (Agar change hua hai)
    if updated:
        await update_joining_board(context, chat.id, match)

# Extend command (Admins only)
async def extend_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /extend command (Text only)"""
    chat = update.effective_chat
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    try:
        seconds = int(context.args[0])
    except:
        await update.message.reply_text("Use: /extend <seconds>")
        return

    match.team_join_end_time += seconds
    
    await update.message.reply_text(
        f"⏳ <b>Time Extended!</b>\nAdded +{seconds} seconds to joining phase.",
        parse_mode=ParseMode.HTML
    )
    
    # Refresh Game Board
    text = get_team_join_message(match)
    keyboard = [
        [InlineKeyboardButton("🔵 Join Team X", callback_data="join_team_x"),
         InlineKeyboardButton("🔴 Join Team Y", callback_data="join_team_y")],
        [InlineKeyboardButton("🚪 Leave Team", callback_data="leave_team")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use master function to keep it at bottom and pinned
    await refresh_game_message(context, chat.id, match, text, reply_markup=reply_markup, media_key="joining")

# Host selection callback
# Host selection callback
async def host_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Host Selection safely with 4-20 Overs"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        return
        
    match = active_matches[chat.id]
    
    # Check if someone is already host
    if match.host_id is not None:
        await query.answer("Host already selected!", show_alert=True)
        return

    # Set Host
    match.host_id = user.id
    match.host_name = user.first_name
    match.last_activity = time.time()  # Reset timer
    
    match.phase = GamePhase.OVER_SELECTION
    
    # --- LOGIC FOR 4 TO 20 OVERS ---
    keyboard = []
    row = []
    # Loop from 4 to 20 (inclusive)
    for i in range(4, 21):
        # Add button to current row
        row.append(InlineKeyboardButton(f"{i}", callback_data=f"overs_{i}"))
        
        # If row has 4 buttons, add it to keyboard and start new row
        if len(row) == 4:
            keyboard.append(row)
            row = []
            
    # Add any remaining buttons
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # --- FIX: Generate User Tag ---
    user_tag = get_user_tag(user)
    
    msg = f"🎙 <b>HOST: {user_tag}</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "Host, please select the number of overs for this match.\n"
    msg += "Range: <b>4 to 20 Overs</b>"
    
    # Use Safe Refresh Function
    await refresh_game_message(context, chat.id, match, msg, reply_markup, media_key="host")


# Captain selection callback
# Captain selection callback
# Captain selection callback
async def captain_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Captain Selection and move to Toss safely"""
    query = update.callback_query
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        await query.answer("No active match.", show_alert=True)
        return
    
    match = active_matches[chat.id]
    
    # Check Phase
    if match.phase != GamePhase.CAPTAIN_SELECTION:
        await query.answer("Captain selection phase has ended.", show_alert=True)
        return
    
    # Logic for Team X
    if query.data == "captain_team_x":
        if not match.team_x.get_player(user.id):
            await query.answer("You must be in Team X!", show_alert=True)
            return
        if match.team_x.captain_id:
            await query.answer("Team X already has a captain.", show_alert=True)
            return
        match.team_x.captain_id = user.id
        await query.answer("You are Captain of Team X!")
    
    # Logic for Team Y
    elif query.data == "captain_team_y":
        if not match.team_y.get_player(user.id):
            await query.answer("You must be in Team Y!", show_alert=True)
            return
        if match.team_y.captain_id:
            await query.answer("Team Y already has a captain.", show_alert=True)
            return
        match.team_y.captain_id = user.id
        await query.answer("You are Captain of Team Y!")
    
    # Check if BOTH are selected
    if match.team_x.captain_id and match.team_y.captain_id:
        # ✅ FLOW FIX: Captains ke baad Toss aayega
        match.phase = GamePhase.TOSS
        await start_toss(query, context, match)
        
    else:
        # Update Message (Show who is selected)
        captain_x = match.team_x.get_player(match.team_x.captain_id)
        captain_y = match.team_y.get_player(match.team_y.captain_id)
        
        cap_x_name = captain_x.first_name if captain_x else "Not Selected"
        cap_y_name = captain_y.first_name if captain_y else "Not Selected"
        
        keyboard = [
            [InlineKeyboardButton("Become Captain - Team X", callback_data="captain_team_x")],
            [InlineKeyboardButton("Become Captain - Team Y", callback_data="captain_team_y")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = "🧢 <b>CAPTAIN SELECTION</b>\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"🔵 <b>Team X:</b> {cap_x_name}\n"
        msg += f"🔴 <b>Team Y:</b> {cap_y_name}\n\n"
        msg += "<i>Waiting for both captains...</i>"
        
        # ✅ FIX: Use refresh_game_message instead of risky edits
        await refresh_game_message(context, chat.id, match, msg, reply_markup, media_key="squads")

async def start_team_edit_phase(query, context: ContextTypes.DEFAULT_TYPE, match: Match):
    """Start team edit phase with Safety Checks"""
    match.phase = GamePhase.TEAM_EDIT
    
    # Safe Host Fetch
    host = match.team_x.get_player(match.host_id) or match.team_y.get_player(match.host_id)
    host_name = host.first_name if host else "Unknown"
    
    # Safe Captain Fetch
    captain_x = match.team_x.get_player(match.team_x.captain_id)
    captain_y = match.team_y.get_player(match.team_y.captain_id)
    
    cap_x_name = captain_x.first_name if captain_x else "Not Selected"
    cap_y_name = captain_y.first_name if captain_y else "Not Selected"
    
    keyboard = [
        [InlineKeyboardButton("Edit Team X", callback_data="edit_team_x")],
        [InlineKeyboardButton("Edit Team Y", callback_data="edit_team_y")],
        [InlineKeyboardButton("✅ Done - Proceed", callback_data="team_edit_done")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    edit_text = "⚙️ <b>TEAM SETUP & EDITING</b>\n"
    edit_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    edit_text += f"🎙 <b>Host:</b> {host_name}\n"
    edit_text += f"🔵 <b>Team X Captain:</b> {cap_x_name}\n"
    edit_text += f"🔴 <b>Team Y Captain:</b> {cap_y_name}\n\n"
    
    edit_text += "🔵 <b>TEAM X SQUAD:</b>\n"
    for i, player in enumerate(match.team_x.players, 1):
        role = " (C)" if player.user_id == match.team_x.captain_id else ""
        edit_text += f"{i}. {player.first_name}{role}\n"
    
    edit_text += "\n🔴 <b>TEAM Y SQUAD:</b>\n"
    for i, player in enumerate(match.team_y.players, 1):
        role = " (C)" if player.user_id == match.team_y.captain_id else ""
        edit_text += f"{i}. {player.first_name}{role}\n"
    
    edit_text += "\n"
    edit_text += "<b>Host Controls:</b>\n"
    edit_text += "• Reply to a user with <code>/add</code> to add them.\n"
    edit_text += "• Reply to a user with <code>/remove</code> to remove them.\n"
    edit_text += "• Click 'Done' when ready."
    
    # Use Master Function (Corrected Call)
    chat_id = query.message.chat.id
    await refresh_game_message(context, chat_id, match, edit_text, reply_markup=reply_markup, media_key="squads")

# Add/Remove player commands (Host only)
async def add_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add player to selected team"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TEAM_EDIT:
        await update.message.reply_text("⚠️ Team editing inactive.")
        return
        
    # Check if Host
    if user.id != match.host_id:
        await update.message.reply_text("⚠️ Only Host can add.")
        return
        
    # CRITICAL FIX: Check if mode is set
    if not match.editing_team:
        await update.message.reply_text("⚠️ Please click 'Edit Team X' or 'Edit Team Y' button first!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Usage: Reply to user with /add")
        return
    
    target = update.message.reply_to_message.from_user
    
    # Check duplicate
    if match.team_x.get_player(target.id) or match.team_y.get_player(target.id):
        await update.message.reply_text(f"⚠️ {target.first_name} is already in a team.")
        return

    # Add Player
    p = Player(target.id, target.username or "", target.first_name)
    if match.editing_team == "X":
        match.team_x.add_player(p)
        t_name = "Team X"
    else:
        match.team_y.add_player(p)
        t_name = "Team Y"
        
    await update.message.reply_text(f"✅ Added {target.first_name} to {t_name}")
    await update_team_edit_message(context, chat.id, match)

async def remove_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove player from the currently selected editing team"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TEAM_EDIT: return
    if user.id != match.host_id:
        await update.message.reply_text("⚠️ Only Host can remove players.")
        return

    # Check Active Edit Mode
    if not match.editing_team:
        await update.message.reply_text("⚠️ Pehle 'Edit Team X' ya 'Edit Team Y' button par click karein!")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("Usage: Reply to a user with /remove")
        return
    
    target_user = update.message.reply_to_message.from_user
    
    # Remove Logic
    removed = False
    if match.editing_team == "X":
        removed = match.team_x.remove_player(target_user.id)
        team_name = "Team X"
    else:
        removed = match.team_y.remove_player(target_user.id)
        team_name = "Team Y"
    
    if removed:
        await update.message.reply_text(f"🗑 {target_user.first_name} removed from <b>{team_name}</b>.", parse_mode=ParseMode.HTML)
        await update_team_edit_message(context, chat.id, match)
    else:
        await update.message.reply_text(f"⚠️ {target_user.first_name} is not in {team_name}.")

async def update_team_edit_message(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Show correct menu based on state"""
    
    # Squad List Text...
    text = f"⚙️ <b>TEAM SETUP</b>\n━━━━━━━━━━━━━━━━\n"
    text += f"🔵 <b>Team X:</b> {len(match.team_x.players)} players\n"
    for p in match.team_x.players: text += f"- {p.first_name}\n"
    text += f"\n🔴 <b>Team Y:</b> {len(match.team_y.players)} players\n"
    for p in match.team_y.players: text += f"- {p.first_name}\n"
    text += "\n"

    # MAIN LOGIC: Sub-menu vs Main Menu
    if match.editing_team:
        # Edit Mode ON
        text += f"🟢 <b>EDITING TEAM {match.editing_team}</b>\n"
        text += "👉 Reply with /add or /remove.\n"
        text += "👉 Click Back when done with this team."
        
        # Sirf Back button dikhao
        keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="edit_back")]]
    else:
        # Main Menu
        text += "👇 <b>Select a team to edit:</b>"
        keyboard = [
            [InlineKeyboardButton("✏️ Edit X", callback_data="edit_team_x"), 
             InlineKeyboardButton("✏️ Edit Y", callback_data="edit_team_y")],
            [InlineKeyboardButton("✅ Finalize Teams", callback_data="team_edit_done")]
        ]
    
    await refresh_game_message(context, group_id, match, text, InlineKeyboardMarkup(keyboard), "squads")

# Team edit done callback
async def team_edit_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish Team Edit and start Captain Selection"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TEAM_EDIT:
        await query.answer("Team edit phase has ended.", show_alert=True)
        return
    
    if user.id != match.host_id:
        await query.answer("Only the Host can proceed.", show_alert=True)
        return
    
    # Validate teams
    if len(match.team_x.players) == 0 or len(match.team_y.players) == 0:
        await query.answer("Both teams need at least one player.", show_alert=True)
        return
    
    # ✅ FLOW FIX: Team Edit ke baad ab Captain Selection aayega
    match.phase = GamePhase.CAPTAIN_SELECTION
    
    # Prepare Captain Selection Message
    captain_x = match.team_x.get_player(match.team_x.captain_id)
    captain_y = match.team_y.get_player(match.team_y.captain_id)
    
    cap_x_name = captain_x.first_name if captain_x else "Not Selected"
    cap_y_name = captain_y.first_name if captain_y else "Not Selected"
    
    keyboard = [
        [InlineKeyboardButton("Become Captain - Team X", callback_data="captain_team_x")],
        [InlineKeyboardButton("Become Captain - Team Y", callback_data="captain_team_y")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = "🧢 <b>CAPTAIN SELECTION</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔵 <b>Team X:</b> {cap_x_name}\n"
    msg += f"🔴 <b>Team Y:</b> {cap_y_name}\n\n"
    msg += "<i>Click below to lead your team!</i>"
    
    # Update Board (Using Refresh function to be safe)
    await refresh_game_message(context, chat.id, match, msg, reply_markup, media_key="squads")

# Over selection callback
async def over_selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle over selection and move to Team Edit"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        await query.answer("No active match found.", show_alert=True)
        return
    
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.OVER_SELECTION:
        await query.answer("Over selection phase has ended.", show_alert=True)
        return
    
    if user.id != match.host_id:
        await query.answer("Only the Host can select overs.", show_alert=True)
        return
    
    # --- LOGIC ---
    try:
        data_parts = query.data.split("_")
        if len(data_parts) != 2: return
        overs_selected = int(data_parts[1])
        
        if 4 <= overs_selected <= 20:
            match.total_overs = overs_selected
            
            # ✅ FLOW FIX: Overs ke baad ab Team Edit Mode aayega
            match.phase = GamePhase.TEAM_EDIT
            await start_team_edit_phase(query, context, match)
            
        else:
            await query.answer("Overs must be between 4 and 20.", show_alert=True)
    except ValueError:
        await query.answer("Invalid format.", show_alert=True)

async def start_toss(query, context: ContextTypes.DEFAULT_TYPE, match: Match):
    """Start the toss phase safely"""
    # Try to fetch Team X Captain safely
    captain_x = match.team_x.get_player(match.team_x.captain_id)
    cap_x_name = captain_x.first_name if captain_x else "Team X Captain"
    
    keyboard = [
        [InlineKeyboardButton("Heads", callback_data="toss_heads")],
        [InlineKeyboardButton("Tails", callback_data="toss_tails")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    toss_text = "🪙 <b>TIME FOR THE TOSS</b>\n"
    toss_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    toss_text += f"📏 <b>Format:</b> {match.total_overs} Overs per side\n\n"
    toss_text += f"👤 <b>{cap_x_name}</b>, it's your call!\n"
    toss_text += "<i>Choose Heads or Tails below:</i>"
    
    # ✅ FIX: Always use refresh_game_message to switch images safely
    chat_id = match.group_id
    await refresh_game_message(context, chat_id, match, toss_text, reply_markup, media_key="toss")

# Toss callback
# Toss callback
async def toss_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle toss selection safely"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        await query.answer("No active match found.", show_alert=True)
        return
    
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TOSS:
        await query.answer("Toss phase has ended.", show_alert=True)
        return
    
    # Only Team X captain can call toss
    if user.id != match.team_x.captain_id:
        await query.answer("Only Team X Captain can call the toss.", show_alert=True)
        return
    
    # Determine toss result
    toss_result = random.choice(["heads", "tails"])
    captain_call = "heads" if query.data == "toss_heads" else "tails"
    
    if toss_result == captain_call:
        match.toss_winner = match.team_x
        winner_captain = match.team_x.get_player(match.team_x.captain_id)
    else:
        match.toss_winner = match.team_y
        winner_captain = match.team_y.get_player(match.team_y.captain_id)
    
    # Ask winner to choose bat or bowl
    keyboard = [
        [InlineKeyboardButton("🏏 Bat First", callback_data="toss_decision_bat")],
        [InlineKeyboardButton("⚾ Bowl First", callback_data="toss_decision_bowl")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    decision_text = "🪙 <b>TOSS RESULT</b>\n"
    decision_text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    decision_text += f"The coin landed on: <b>{toss_result.upper()}</b>\n\n"
    decision_text += f"🎉 <b>{match.toss_winner.name} won the toss!</b>\n"
    decision_text += f"👤 <b>Captain {winner_captain.first_name}</b>, make your choice.\n"
    decision_text += "<i>You have 30 seconds to decide.</i>"
    
    # ✅ FIX: Use refresh_game_message instead of edit_message_text
    await refresh_game_message(context, chat.id, match, decision_text, reply_markup, media_key="toss")
    
    # Set timeout for decision
    asyncio.create_task(toss_decision_timeout(context, chat.id, match))

async def toss_decision_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle toss decision timeout"""
    await asyncio.sleep(30)
    
    if match.phase != GamePhase.TOSS:
        return
    
    # Auto select bat if no decision made
    match.batting_first = match.toss_winner
    match.bowling_first = match.get_other_team(match.toss_winner)
    
    await start_match(context, group_id, match, auto_decision=True)

# Toss decision callback
async def toss_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bat/bowl decision"""
    query = update.callback_query
    await query.answer()
    
    chat = query.message.chat
    user = query.from_user
    
    if chat.id not in active_matches:
        await query.answer("No active match found.", show_alert=True)
        return
    
    match = active_matches[chat.id]
    
    if match.phase != GamePhase.TOSS:
        await query.answer("Toss phase has ended.", show_alert=True)
        return
    
    # Only toss winner captain can decide
    winner_captain = match.get_captain(match.toss_winner)
    if user.id != winner_captain.user_id:
        await query.answer("Only the toss winner captain can decide.", show_alert=True)
        return
    
    if query.data == "toss_decision_bat":
        match.batting_first = match.toss_winner
        match.bowling_first = match.get_other_team(match.toss_winner)
    else:
        match.bowling_first = match.toss_winner
        match.batting_first = match.get_other_team(match.toss_winner)
    
    await start_match(context, chat.id, match, auto_decision=False)

async def start_match(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, auto_decision: bool):
    """Start the actual match with prediction poll"""
    match.phase = GamePhase.MATCH_IN_PROGRESS
    match.current_batting_team = match.batting_first
    match.current_bowling_team = match.bowling_first
    match.innings = 1
    match.waiting_for_batsman = True

    # Cleanup the Toss Board
    if match.main_message_id:
        try:
            await context.bot.unpin_chat_message(chat_id=group_id, message_id=match.main_message_id)
            await context.bot.delete_message(chat_id=group_id, message_id=match.main_message_id)
            match.main_message_id = None
        except: pass

    # Send toss summary
    gif_url = get_random_gif(MatchEvent.INNINGS_BREAK)
    
    decision_method = "chose to" if not auto_decision else "will"
    
    toss_summary = "🏟 <b>MATCH STARTED</b>\n"
    toss_summary += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    toss_summary += f"🪙 <b>{match.toss_winner.name}</b> won the toss\n"
    toss_summary += f"🏏 <b>{match.batting_first.name}</b> {decision_method} bat first\n\n"
    toss_summary += f"📏 <b>Format:</b> {match.total_overs} Overs per side\n"
    toss_summary += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    toss_summary += "<i>Openers are walking to the crease...</i>"
    
    try:
        if gif_url:
            await context.bot.send_animation(
                chat_id=group_id,
                animation=gif_url,
                caption=toss_summary,
                parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=group_id,
                text=toss_summary,
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error sending toss summary: {e}")
        await context.bot.send_message(
            chat_id=group_id,
            text=toss_summary,
            parse_mode=ParseMode.HTML
        )
    
    # ✅ CREATE PREDICTION POLL
    await create_prediction_poll(context, group_id, match)
    
    # Wait 5 seconds
    await asyncio.sleep(5)
    
    # Request first batsman
    await request_batsman_selection(context, group_id, match)


async def request_batsman_selection(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Request batting captain to select next batsman - FIXED VERSION"""
    team = match.current_batting_team
    captain = match.get_captain(team)
    
    if not captain:
        return
    
    # Determine which batsman to select
    if team.current_batsman_idx is None:
        role = "Striker"
    elif team.current_non_striker_idx is None:
        role = "Non-Striker"
    else:
        # A batsman got out, need replacement
        role = "Next Batsman"
    
    text = f"🏏 <b>SELECT {role.upper()}</b>\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>{team.name}</b>\n\n"
    text += "<i>Available Players:</i>\n"
    
    for i, p in enumerate(team.players, 1):
        player_idx = i - 1
        
        if player_idx in team.out_players_indices:
            status = "❌ <i>OUT</i>"
        elif player_idx == team.current_batsman_idx:
            status = "⚡ <i>Striker</i>"
        elif player_idx == team.current_non_striker_idx:
            status = "👀 <i>Non-Striker</i>"
        else:
            status = "✅"
        
        text += f"<code>{i}.</code> <b>{p.first_name}</b> {status}\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📣 <b>Captain {captain.first_name}</b>\n"
    text += f"👉 Send: /batting (player serial)\n"
    text += f"📌 Example: <code>/batting 1</code>"
    
    await context.bot.send_message(group_id, text, parse_mode=ParseMode.HTML)

async def batting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Batting Selection - COMPLETELY FIXED"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No active match.")
        return
        
    match = active_matches[chat.id]
    
    if not match.waiting_for_batsman:
        await update.message.reply_text("⚠️ Not waiting for batsman selection.")
        return
    
    bat_team = match.current_batting_team
    if user.id != bat_team.captain_id:
        await update.message.reply_text("⚠️ Only Captain can select.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Usage: /batting (player serial)\nExample: <code>/batting 1</code>",
            parse_mode=ParseMode.HTML
        )
        return
        
    try:
        serial = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid number.")
        return

    if serial < 1 or serial > len(bat_team.players):
        await update.message.reply_text(f"❌ Serial must be 1 to {len(bat_team.players)}")
        return

    player_idx = serial - 1
    player = bat_team.players[player_idx]
    
    # Check if player is already out
    if player_idx in bat_team.out_players_indices:
        await update.message.reply_text(f"⚠️ {player.first_name} is already OUT!")
        return
    
    player_tag = f"<a href='tg://user?id={player.user_id}'>{player.first_name}</a>"

    # Case A: Selecting STRIKER (First batsman)
    if bat_team.current_batsman_idx is None:
        bat_team.current_batsman_idx = player_idx
        
        confirm_msg = f"✅ <b>STRIKER SELECTED</b>\n"
        confirm_msg += f"🏏 {player_tag} will face the first ball!\n\n"
        confirm_msg += f"👇 Now select the Non-Striker using /batting (serial)"
        
        await context.bot.send_message(chat.id, confirm_msg, parse_mode=ParseMode.HTML)
        
    # Case B: Selecting NON-STRIKER (Second batsman)
    elif bat_team.current_non_striker_idx is None:
        if player_idx == bat_team.current_batsman_idx:
            await update.message.reply_text("⚠️ Already selected as Striker!")
            return
            
        bat_team.current_non_striker_idx = player_idx
        match.waiting_for_batsman = False
        
        if match.batsman_selection_task:
            match.batsman_selection_task.cancel()
        
        confirm_msg = f"✅ <b>NON-STRIKER SELECTED</b>\n"
        confirm_msg += f"👀 {player_tag} will be at the other end!\n\n"
        confirm_msg += f"⚾ <b>Batting Order Complete!</b> Waiting for bowler..."
        
        await context.bot.send_message(chat.id, confirm_msg, parse_mode=ParseMode.HTML)
        
        await request_bowler_selection(context, chat.id, match)
    
    # Case C: Replacing OUT batsman (Wicket ke baad)
    else:
        # Check duplicate with existing batsmen
        if player_idx == bat_team.current_batsman_idx or player_idx == bat_team.current_non_striker_idx:
            await update.message.reply_text("⚠️ This player is already batting!")
            return
        
        # Replace the OUT striker with new batsman
        bat_team.current_batsman_idx = player_idx
        match.waiting_for_batsman = False
        
        if match.batsman_selection_task:
            match.batsman_selection_task.cancel()
        
        confirm_msg = f"✅ <b>NEW BATSMAN IN!</b>\n"
        confirm_msg += f"🏏 {player_tag} walks to the crease!\n\n"
        confirm_msg += f"🎯 Ready to face the next ball..."
        
        await context.bot.send_message(chat.id, confirm_msg, parse_mode=ParseMode.HTML)
        
        # Continue game flow
        await asyncio.sleep(2)
        
        # Check if over is complete or continue
        bowl_team = match.current_bowling_team
        if bowl_team.get_current_over_balls() == 0:
            await check_over_complete(context, chat.id, match)
        else:
            await execute_ball(context, chat.id, match)

async def players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current squads with Image"""
    chat = update.effective_chat
    if chat.id not in active_matches:
        await update.message.reply_text("No active match.")
        return
        
    match = active_matches[chat.id]
    
    msg = "📋 <b>OFFICIAL MATCH SQUADS</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += f"🔵 <b>{match.team_x.name}</b>\n"
    for i, p in enumerate(match.team_x.players, 1):
        role = " ⭐ (C)" if p.user_id == match.team_x.captain_id else ""
        msg += f"<code>{i}.</code> <b>{p.first_name}</b>{role}\n"
        
    msg += f"\n🔴 <b>{match.team_y.name}</b>\n"
    for i, p in enumerate(match.team_y.players, 1):
        role = " ⭐ (C)" if p.user_id == match.team_y.captain_id else ""
        msg += f"<code>{i}.</code> <b>{p.first_name}</b>{role}\n"
        
    await update.message.reply_photo(
        photo=MEDIA_ASSETS["squads"],
        caption=msg,
        parse_mode=ParseMode.HTML
    )

async def batsman_selection_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle batsman selection timeout"""
    try:
        await asyncio.sleep(120)  # 2 minutes
        
        if not match.waiting_for_batsman:
            return
        
        # Timeout occurred - penalty
        match.current_batting_team.score -= 6
        match.current_batting_team.penalty_runs += 6
        
        penalty_msg = "Batsman Selection Timeout\n\n"
        penalty_msg += f"{match.current_batting_team.name} penalized 6 runs for delay.\n"
        penalty_msg += f"Current Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}\n\n"
        penalty_msg += "Please select a batsman immediately."
        
        await context.bot.send_message(
            chat_id=group_id,
            text=penalty_msg
        )
        
        # Reset timer
        match.batsman_selection_time = time.time()
        match.batsman_selection_task = asyncio.create_task(
            batsman_selection_timeout(context, group_id, match)
        )
    
    except asyncio.CancelledError:
        pass

# Batting command
async def batting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Batting Selection: Striker First -> Then Non-Striker"""
    chat = update.effective_chat
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    # 1. Check if we are waiting for batsman
    if not match.waiting_for_batsman:
        await update.message.reply_text("⚠️ It is not the time to select a batsman right now.")
        return

    # 2. Check Captain
    bat_team = match.current_batting_team
    if update.effective_user.id != bat_team.captain_id:
        await update.message.reply_text("⚠️ Only the Batting Captain can select the batsman!")
        return

    # 3. Parse Serial Number
    if not context.args:
        await update.message.reply_text("Usage: /batting <serial_number>\nExample: /batting 1")
        return
    
    try:
        serial = int(context.args[0])
    except:
        await update.message.reply_text("❌ Invalid number format.")
        return

    # 4. Get Player Object
    player = bat_team.get_player_by_serial(serial)
    if not player:
        await update.message.reply_text("❌ Player not found in the team.")
        return
    
    if player.is_out:
        await update.message.reply_text(f"⚠️ {player.first_name} is already OUT!")
        return

    # --- SELECTION LOGIC ---
    
    # Case A: Selecting STRIKER
    if bat_team.current_batsman_idx is None:
        bat_team.current_batsman_idx = serial - 1
        
        msg = f"🏏 Striker Selected: {player.first_name}\n"
        msg += "👇 Now select the Non-Striker (/batting <number>)"
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        
    # Case B: Selecting NON-STRIKER
    elif bat_team.current_non_striker_idx is None:
        # Check Duplicate
        if (serial - 1) == bat_team.current_batsman_idx:
            await update.message.reply_text("⚠️ This player is already the Striker! Please select another player.")
            return
            
        bat_team.current_non_striker_idx = serial - 1
        
        # DONE! Both Selected
        match.waiting_for_batsman = False # Stop waiting
        
        msg = f"👀 Non-Striker Selected: {player.first_name}\n"
        msg += "✅ Batting Order Set! Waiting for the bowler."
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        
        # Start Bowler Selection
        await request_bowler_selection(context, chat.id, match)

    else:
        await update.message.reply_text("⚠️ Both batsmen are already at the crease!")

async def request_bowler_selection(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Request bowling captain to select bowler - FIXED"""
    bowl_team = match.current_bowling_team
    bowling_captain = match.get_captain(bowl_team)
    
    if not bowling_captain:
        return
    
    match.waiting_for_bowler = True
    
    available_bowlers = bowl_team.get_available_bowlers()
    
    text = f"⚾ <b>SELECT BOWLER</b>\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"<b>{bowl_team.name}</b>\n\n"
    
    bat_team = match.current_batting_team
    striker = bat_team.players[bat_team.current_batsman_idx] if bat_team.current_batsman_idx is not None else None
    striker_name = striker.first_name if striker else "Batsman"
    
    text += f"🎯 <b>Facing:</b> {striker_name}\n"
    text += f"📊 <b>Score:</b> {bat_team.score}/{bat_team.wickets}\n"
    text += f"🏏 <b>Over:</b> {format_overs(bowl_team.balls)}\n\n"
    
    text += "<i>Available Bowlers:</i>\n"
    
    for i, player in enumerate(bowl_team.players, 1):
        if player.is_bowling_banned:
            status = "⛔ <i>BANNED</i>"
        elif player not in available_bowlers:
            status = "⏸️ <i>Cooldown</i>"
        else:
            if player.balls_bowled > 0:
                overs = format_overs(player.balls_bowled)
                status = f"<i>({player.wickets}/{player.runs_conceded} in {overs})</i>"
            else:
                status = "✅"
        
        text += f"<code>{i}.</code> <b>{player.first_name}</b> {status}\n"
    
    text += f"\n━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📣 <b>Captain {bowling_captain.first_name}</b>\n"
    # ✅ FIX: Remove <code> tags from placeholder
    text += f"👉 Send: /bowling (player serial)\n"
    text += f"📌 Example: <code>/bowling 1</code>"
    
    await context.bot.send_message(group_id, text, parse_mode=ParseMode.HTML)

async def bowler_selection_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle bowler selection timeout"""
    try:
        await asyncio.sleep(60)  # 1 minute
        
        if not match.waiting_for_bowler:
            return
        
        # Get current bowler if any
        if match.current_bowling_team.current_bowler_idx is not None:
            bowler = match.current_bowling_team.players[match.current_bowling_team.current_bowler_idx]
            bowler.bowling_timeouts += 1
            
            timeout_count = bowler.bowling_timeouts
            
            if timeout_count >= 3:
                # Ban from bowling
                bowler.is_bowling_banned = True
                
                penalty_msg = "Bowler Selection Timeout\n\n"
                penalty_msg += f"{bowler.first_name} has timed out 3 times.\n"
                penalty_msg += f"{bowler.first_name} is now BANNED from bowling for the rest of the match.\n\n"
                penalty_msg += "No Ball called. Free Hit on next ball.\n\n"
                penalty_msg += "Please select another bowler immediately."
                
                # Add no ball
                match.current_batting_team.score += 1
                match.current_batting_team.extras += 1
                match.is_free_hit = True
                
                await context.bot.send_message(
                    chat_id=group_id,
                    text=penalty_msg
                )
            else:
                penalty_msg = "Bowler Selection Timeout\n\n"
                penalty_msg += f"{bowler.first_name} timed out ({timeout_count}/3).\n"
                penalty_msg += "No Ball called. Free Hit on next ball.\n\n"
                penalty_msg += "Please select a bowler immediately."
                
                # Add no ball
                match.current_batting_team.score += 1
                match.current_batting_team.extras += 1
                match.is_free_hit = True
                
                await context.bot.send_message(
                    chat_id=group_id,
                    text=penalty_msg
                )
        else:
            # First ball, no specific bowler to penalize
            penalty_msg = "Bowler Selection Timeout\n\n"
            penalty_msg += f"{match.current_bowling_team.name} delayed bowler selection.\n"
            penalty_msg += "6 runs penalty after this over.\n\n"
            penalty_msg += "Please select a bowler immediately."
            
            await context.bot.send_message(
                chat_id=group_id,
                text=penalty_msg
            )
        
        # Reset timer
        match.bowler_selection_time = time.time()
        match.bowler_selection_task = asyncio.create_task(
            bowler_selection_timeout(context, group_id, match)
        )
    
    except asyncio.CancelledError:
        pass

# Bowling command
async def bowling_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Bowling Selection with Tags"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.id not in active_matches: return
    match = active_matches[chat.id]
    
    if not match.waiting_for_bowler:
        await update.message.reply_text("⚠️ Not waiting for bowler selection.")
        return
    
    bowling_captain = match.get_captain(match.current_bowling_team)
    if user.id != bowling_captain.user_id:
        await update.message.reply_text("⚠️ Only Captain can select.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /bowling <number>")
        return
    
    try:
        serial = int(context.args[0])
    except: return
    
    bowler = match.current_bowling_team.get_player_by_serial(serial)
    
    if not bowler or bowler.is_bowling_banned:
        await update.message.reply_text("⚠️ Invalid bowler or BANNED.")
        return
    
    # Check consecutive overs logic
    bowler_idx = serial - 1
    if match.current_bowling_team.bowler_history:
        last_idx = match.current_bowling_team.bowler_history[-1]
        if bowler_idx == last_idx and match.current_bowling_team.get_current_over_balls() == 0:
            await update.message.reply_text("⚠️ Cannot bowl consecutive overs!")
            return

    # Set Bowler
    match.current_bowling_team.current_bowler_idx = bowler_idx
    match.waiting_for_bowler = False
    
    if match.bowler_selection_task: match.bowler_selection_task.cancel()
    
    # Tag and Confirm
    bowler_tag = f"<a href='tg://user?id={bowler.user_id}'>{bowler.first_name}</a>"
    await update.message.reply_text(f"✅ <b>Bowler Confirmed:</b> {bowler_tag} is coming to bowl!", parse_mode=ParseMode.HTML)
    
    # Execute Ball
    await execute_ball(context, chat.id, match)

async def execute_ball(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Pre-Ball Phase with GIF and DM Button"""
    
    bat_team = match.current_batting_team
    bowl_team = match.current_bowling_team
    
    striker = bat_team.players[bat_team.current_batsman_idx]
    non_striker = bat_team.players[bat_team.current_non_striker_idx]
    bowler = bowl_team.players[bowl_team.current_bowler_idx]
    
    striker_tag = f"<a href='tg://user?id={striker.user_id}'>{striker.first_name}</a>"
    non_striker_tag = f"<a href='tg://user?id={non_striker.user_id}'>{non_striker.first_name}</a>"
    bowler_tag = f"<a href='tg://user?id={bowler.user_id}'>{bowler.first_name}</a>"
    
    text = f"🏏 <b>BALL!</b>\n"
    text += "━━━━━━━━━━━━━━━\n"
    text += f"🏏 <b>Striker:</b> {striker_tag}\n"
    text += f"👀 <b>Non-Striker:</b> {non_striker_tag}\n"
    text += f"⚾ <b>Bowler:</b> {bowler_tag}\n"
    text += "━━━━━━━━━━━━━━━\n"
    
    if match.is_free_hit:
        text += "⚡ <b>FREE HIT BALL!</b>\n"
    
    text += f"📣 <b>{bowler.first_name},</b> click below to bowl!"
    
    # ✅ FIXED: Add DM Button
    keyboard = [[InlineKeyboardButton("📩 Open DM to Bowl", url=f"https://t.me/{context.bot.username}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    ball_gif = "https://t.me/cricoverse/49"
    
    try:
        await context.bot.send_animation(
            group_id, 
            animation=ball_gif,
            caption=text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
    except:
        await context.bot.send_message(group_id, text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    
    # Send DM to Bowler
    dm_text = f"🎯 <b>Over {format_overs(bowl_team.balls)}</b>\n"
    dm_text += f"Target: {striker.first_name}\n"
    dm_text += f"Score: {bat_team.score}/{bat_team.wickets}\n\n"
    
    if match.is_free_hit:
        dm_text += "⚡ <b>FREE HIT BALL!</b>\n\n"
    
    dm_text += "👉 <b>Send a number (0-6) within 45 seconds!</b>"
    
    try:
        await context.bot.send_message(bowler.user_id, dm_text, parse_mode=ParseMode.HTML)
        match.current_ball_data = {"bowler_id": bowler.user_id, "bowler_number": None, "batsman_number": None, "group_id": group_id}
        
        if match.ball_timeout_task:
            match.ball_timeout_task.cancel()
        match.ball_timeout_task = asyncio.create_task(
            game_timer(context, group_id, match, "bowler", bowler.first_name)
        )
        
    except Forbidden:
        await context.bot.send_message(
            group_id, 
            f"⚠️ {bowler_tag} needs to start the bot in DM!", 
            parse_mode=ParseMode.HTML
        )

async def process_player_number(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, number: int):
    """Handle DM Input (Bowler) & Logic"""
    user = update.effective_user
    
    # --- BOWLER INPUT LOGIC ---
    if user.id == match.current_ball_data.get("bowler_id") and match.current_ball_data.get("bowler_number") is None:
        match.current_ball_data["bowler_number"] = number
        
        # 1. Stop Bowler Timer
        if match.ball_timeout_task: match.ball_timeout_task.cancel()
        
        # 2. Confirm to Bowler (With Back Button)
        # Deep link to group (needs public username or private link logic, using generic for now)
        keyboard = [[InlineKeyboardButton("🔙 Back to Group", url="https://t.me/")]] 
        await update.message.reply_text(f"✅ <b>Ball Delivered:</b> {number}\nGo back to group!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        
        # 3. Notify Group & Tag Batsman
        bat_team = match.current_batting_team
        striker = bat_team.players[bat_team.current_batsman_idx]
        striker_tag = f"<a href='tg://user?id={striker.user_id}'>{striker.first_name}</a>"
        
        msg = f"⚾ <b>Bowler has bowled!</b>\n"
        msg += f"🏏 <b>{striker_tag}</b>, it's your turn!\n"
        msg += "👉 <b>Choose your number (0-6) here in Group!</b>\n"
        msg += "⏳ <i>You have 45 seconds!</i>"
        
        await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
        
        # 4. Start Batsman Timer (45s)
        match.ball_timeout_task = asyncio.create_task(game_timer(context, group_id, match, "batsman", striker.first_name))
        return

async def process_player_number(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, number: int):
    """Handle DM Input from Bowler"""
    user = update.effective_user
    
    # Bowler Logic
    if user.id == match.current_ball_data.get("bowler_id") and match.current_ball_data.get("bowler_number") is None:
        match.current_ball_data["bowler_number"] = number
        
        # Confirmation in DM
        await update.message.reply_text(f"✅ <b>Ball Delivered:</b> {number}", parse_mode=ParseMode.HTML)
        
        # Notify Group
        await context.bot.send_message(group_id, f"⚾ <b>{user.first_name}</b> has bowled!\n🏏 <i>Batsman, hit your shot!</i>", parse_mode=ParseMode.HTML)
        return

async def wait_for_bowler_number(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Wait for bowler to send number with reminders"""
    bowler = match.current_bowling_team.players[match.current_bowling_team.current_bowler_idx]
    
    try:
        # Wait 30 seconds
        await asyncio.sleep(30)
        
        if match.current_ball_data.get("bowler_number") is None:
            # Send reminder at 30s
            try:
                await context.bot.send_message(
                    chat_id=bowler.user_id,
                    text="Reminder: Please send your number (0-6).\n30 seconds remaining."
                )
                match.current_ball_data["bowler_reminded"] = True
            except Exception as e:
                logger.error(f"Error sending reminder to bowler: {e}")
        
        # Wait 15 more seconds
        await asyncio.sleep(15)
        
        if match.current_ball_data.get("bowler_number") is None:
            # Send reminder at 15s
            try:
                await context.bot.send_message(
                    chat_id=bowler.user_id,
                    text="Urgent: Send your number now!\n15 seconds remaining."
                )
            except Exception as e:
                logger.error(f"Error sending reminder to bowler: {e}")
        
        # Wait 10 more seconds
        await asyncio.sleep(10)
        
        if match.current_ball_data.get("bowler_number") is None:
            # Send reminder at 5s
            try:
                await context.bot.send_message(
                    chat_id=bowler.user_id,
                    text="Final warning: 5 seconds left!"
                )
            except Exception as e:
                logger.error(f"Error sending reminder to bowler: {e}")
        
        # Wait final 5 seconds
        await asyncio.sleep(5)
        
        if match.current_ball_data.get("bowler_number") is None:
            # Timeout - handle penalty
            await handle_bowler_timeout(context, group_id, match)
    
    except asyncio.CancelledError:
        pass

async def handle_bowler_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle bowler timeout penalty"""
    bowler = match.current_bowling_team.players[match.current_bowling_team.current_bowler_idx]
    bowler.bowling_timeouts += 1
    bowler.no_balls += 1
    
    timeout_count = bowler.bowling_timeouts
    
    # Add no ball
    match.current_batting_team.score += 1
    match.current_batting_team.extras += 1
    match.is_free_hit = True
    
    gif_url = get_random_gif(MatchEvent.NO_BALL)
    commentary = get_random_commentary("noball")
    
    if timeout_count >= 3:
        # Ban from bowling
        bowler.is_bowling_banned = True
        
        penalty_text = f"Over {format_overs(match.current_bowling_team.balls)}\n\n"
        penalty_text += f"Bowler Timeout - {bowler.first_name}\n\n"
        penalty_text += f"{bowler.first_name} has timed out 3 times.\n"
        penalty_text += f"{bowler.first_name} is now BANNED from bowling.\n\n"
        penalty_text += "NO BALL\n"
        penalty_text += "Free Hit on next ball\n\n"
        penalty_text += f"{commentary}\n\n"
        penalty_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}"
    else:
        penalty_text = f"Over {format_overs(match.current_bowling_team.balls)}\n\n"
        penalty_text += f"Bowler Timeout - {bowler.first_name} ({timeout_count}/3)\n\n"
        penalty_text += "NO BALL\n"
        penalty_text += "Free Hit on next ball\n\n"
        penalty_text += f"{commentary}\n\n"
        penalty_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}"
    
    try:
        if gif_url:
            await context.bot.send_animation(
                chat_id=group_id,
                animation=gif_url,
                caption=penalty_text
            )
        else:
            await context.bot.send_message(
                chat_id=group_id,
                text=penalty_text
            )
    except Exception as e:
        logger.error(f"Error sending timeout message: {e}")
        await context.bot.send_message(
            chat_id=group_id,
            text=penalty_text
        )
    
    # Continue with next ball
    await asyncio.sleep(2)
    
    if bowler.is_bowling_banned:
        # Need new bowler
        match.waiting_for_bowler = True
        await request_bowler_selection(context, group_id, match)
    else:
        # Same bowler continues
        await execute_ball(context, group_id, match)

# Handle DM messages from players
async def handle_dm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle DM messages from players during match"""
    user = update.effective_user
    message = update.message
    
    if not message.text:
        return
    
    text = message.text.strip()
    
    # Check if it's a number
    if not text.isdigit():
        return
    
    number = int(text)
    if number < 0 or number > 6:
        await message.reply_text("Please send a number between 0 and 6.")
        return
    
    # Find active match where this user is playing
    user_match = None
    user_group_id = None
    
    for group_id, match in active_matches.items():
        if match.phase == GamePhase.MATCH_IN_PROGRESS:
            batsman_idx = match.current_batting_team.current_batsman_idx
            bowler_idx = match.current_bowling_team.current_bowler_idx
            
            if batsman_idx is not None and bowler_idx is not None:
                batsman = match.current_batting_team.players[batsman_idx]
                bowler = match.current_bowling_team.players[bowler_idx]
                
                if user.id == batsman.user_id or user.id == bowler.user_id:
                    user_match = match
                    user_group_id = group_id
                    break
    
    if not user_match:
        return
    
    # Process the number
    await process_player_number(update, context, user_group_id, user_match, number)

async def process_player_number(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, number: int):
    """Process number sent by player"""
    user = update.effective_user
    
    batsman = match.current_batting_team.players[match.current_batting_team.current_batsman_idx]
    bowler = match.current_bowling_team.players[match.current_bowling_team.current_bowler_idx]
    
    # Check if bowler sent number
    if user.id == bowler.user_id and match.current_ball_data.get("bowler_number") is None:
        match.current_ball_data["bowler_number"] = number
        await update.message.reply_text(f"Your number: {number}\nWaiting for batsman...")
        
        # Cancel bowler timeout task
        if match.ball_timeout_task:
            match.ball_timeout_task.cancel()
        
        # Now request batsman number
        await request_batsman_number(context, group_id, match)
        return
    
    # Check if batsman sent number
    if user.id == batsman.user_id and match.current_ball_data.get("batsman_number") is None:
        if match.current_ball_data.get("bowler_number") is None:
            await update.message.reply_text("Please wait for bowler to send their number first.")
            return
        
        match.current_ball_data["batsman_number"] = number
        await update.message.reply_text(f"Your number: {number}\nProcessing ball...")
        
        # Cancel batsman timeout task
        if match.ball_timeout_task:
            match.ball_timeout_task.cancel()
        
        # Process ball result
        await process_ball_result(context, group_id, match)
        return

async def request_batsman_number(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Request batsman number with GIF - FIXED"""
    batsman = match.current_batting_team.players[match.current_batting_team.current_batsman_idx]
    
    batsman_tag = f"<a href='tg://user?id={batsman.user_id}'>{batsman.first_name}</a>"
    
    text = f"⚾ <b>Bowler has bowled!</b>\n"
    text += f"🏏 <b>{batsman_tag}</b>, it's your turn!\n"
    text += "👉 <b>Send your number (0-6) in this group!</b>\n"
    text += "⏳ <i>You have 45 seconds!</i>"
    
    # ✅ FIX: Add GIF
    batting_gif = "https://t.me/cricoverse/50"  # Cricket batting GIF
    
    try:
        await context.bot.send_animation(
            group_id,
            animation=batting_gif,
            caption=text,
            parse_mode=ParseMode.HTML
        )
    except:
        await context.bot.send_message(group_id, text, parse_mode=ParseMode.HTML)
    
    if match.ball_timeout_task:
        match.ball_timeout_task.cancel()
    match.ball_timeout_task = asyncio.create_task(
        game_timer(context, group_id, match, "batsman", batsman.first_name)
    )

async def wait_for_batsman_number(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Wait for batsman to send number with reminders"""
    batsman = match.current_batting_team.players[match.current_batting_team.current_batsman_idx]
    
    try:
        # Wait 30 seconds
        await asyncio.sleep(30)
        
        if match.current_ball_data.get("batsman_number") is None:
            # Send reminder at 30s
            try:
                await context.bot.send_message(
                    chat_id=batsman.user_id,
                    text="Reminder: Please send your number (0-6).\n30 seconds remaining."
                )
            except Exception as e:
                logger.error(f"Error sending reminder to batsman: {e}")
        
        # Wait 15 more seconds
        await asyncio.sleep(15)
        
        if match.current_ball_data.get("batsman_number") is None:
            # Send reminder at 15s
            try:
                await context.bot.send_message(
                    chat_id=batsman.user_id,
                    text="Urgent: Send your number now!\n15 seconds remaining."
                )
            except Exception as e:
                logger.error(f"Error sending reminder to batsman: {e}")
        
        # Wait 10 more seconds
        await asyncio.sleep(10)
        
        if match.current_ball_data.get("batsman_number") is None:
            # Send reminder at 5s
            try:
                await context.bot.send_message(
                    chat_id=batsman.user_id,
                    text="Final warning: 5 seconds left!"
                )
            except Exception as e:
                logger.error(f"Error sending reminder to batsman: {e}")
        
        # Wait final 5 seconds
        await asyncio.sleep(5)
        
        if match.current_ball_data.get("batsman_number") is None:
            # Timeout - handle penalty
            await handle_batsman_timeout(context, group_id, match)
    
    except asyncio.CancelledError:
        pass

async def handle_batsman_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle batsman timeout penalty"""
    batsman = match.current_batting_team.players[match.current_batting_team.current_batsman_idx]
    batsman.batting_timeouts += 1
    
    timeout_count = batsman.batting_timeouts
    
    # Penalty: -6 runs
    match.current_batting_team.score -= 6
    match.current_batting_team.penalty_runs += 6
    
    if timeout_count >= 3:
        # Auto out - Hit Wicket
        batsman.is_out = True
        batsman.dismissal_type = "Hit Wicket (Timeout)"
        match.current_batting_team.wickets += 1
        
        gif_url = get_random_gif(MatchEvent.WICKET)
        
        penalty_text = f"Over {format_overs(match.current_bowling_team.balls)}\n\n"
        penalty_text += f"Batsman Timeout - {batsman.first_name}\n\n"
        penalty_text += f"{batsman.first_name} has timed out 3 times.\n"
        penalty_text += "OUT - Hit Wicket\n\n"
        penalty_text += f"{batsman.first_name}: {batsman.runs} ({batsman.balls_faced})\n\n"
        penalty_text += f"6 runs penalty deducted.\n\n"
        penalty_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}"
        
        try:
            if gif_url:
                await context.bot.send_animation(
                    chat_id=group_id,
                    animation=gif_url,
                    caption=penalty_text
                )
            else:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=penalty_text
                )
        except Exception as e:
            logger.error(f"Error sending timeout wicket message: {e}")
            await context.bot.send_message(
                chat_id=group_id,
                text=penalty_text
            )
        
        # Log ball
        match.ball_by_ball_log.append({
            "over": format_overs(match.current_bowling_team.balls),
            "batsman": batsman.first_name,
            "bowler": match.current_bowling_team.players[match.current_bowling_team.current_bowler_idx].first_name,
            "result": "Wicket (Timeout)",
            "runs": -6,
            "is_wicket": True
        })
        
        await asyncio.sleep(3)
        
        # Check if innings over
        if match.is_innings_complete():
            await end_innings(context, group_id, match)
        else:
            # Request new batsman
            match.waiting_for_batsman = True
            await request_batsman_selection(context, group_id, match)
    else:
        penalty_text = f"Over {format_overs(match.current_bowling_team.balls)}\n\n"
        penalty_text += f"Batsman Timeout - {batsman.first_name} ({timeout_count}/3)\n\n"
        penalty_text += "6 runs penalty deducted.\n\n"
        penalty_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}\n\n"
        penalty_text += "Please send your number immediately!"
        
        await context.bot.send_message(
            chat_id=group_id,
            text=penalty_text
        )
        
        # Reset and wait again
        match.current_ball_data["batsman_number"] = None
        match.current_ball_data["batsman_start_time"] = time.time()
        match.ball_timeout_task = asyncio.create_task(
            wait_for_batsman_number(context, group_id, match)
        )

async def process_ball_result(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Calculate Result with Run Rate & Required Run Rate"""
    
    bat_team = match.current_batting_team
    bowl_team = match.current_bowling_team
    
    if bat_team.current_batsman_idx is None or bowl_team.current_bowler_idx is None:
        return

    bowler_num = match.current_ball_data.get("bowler_number")
    batsman_num = match.current_ball_data.get("batsman_number")
    
    if bowler_num is None or batsman_num is None:
        return
    
    striker = bat_team.players[bat_team.current_batsman_idx]
    bowler = bowl_team.players[bowl_team.current_bowler_idx]
    
    # ===== WIDE BALL CHECK (30% Chance) =====
    is_wide = random.random() < 0.30
    
    if is_wide:
        bat_team.score += 1
        bat_team.extras += 1
        
        gif_url = get_random_gif(MatchEvent.WIDE)
        commentary = get_random_commentary("wide")
        
        msg = f"🏏 <b>Over {format_overs(bowl_team.balls)}</b>\n\n"
        msg += f"🚫 <b>WIDE BALL!</b> (+1 Run)\n"
        msg += f"💬 <i>{commentary}</i>\n\n"
        msg += f"📊 <b>Score:</b> {bat_team.score}/{bat_team.wickets}"
        
        # ✅ FIXED: Add Run Rate
        current_rr = round(bat_team.score / max(bat_team.overs, 0.1), 2)
        msg += f"\n📈 <b>Run Rate:</b> {current_rr}"
        
        # ✅ FIXED: Add RRR if chasing
        if match.innings == 2:
            runs_needed = match.target - bat_team.score
            balls_left = (match.total_overs * 6) - bat_team.balls
            rrr = round((runs_needed / max(balls_left, 1)) * 6, 2) if balls_left > 0 else 0
            msg += f"\n🎯 <b>Need:</b> {runs_needed} runs in {balls_left} balls (RRR: {rrr})"
        
        try:
            if gif_url:
                await context.bot.send_animation(group_id, animation=gif_url, caption=msg, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
        except:
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
        
        # Wide doesn't count as legal ball
        match.current_ball_data = {}
        await asyncio.sleep(2)
        await execute_ball(context, group_id, match)
        return
    
    # ===== WICKET CHECK =====
    if bowler_num == batsman_num:
        if match.is_free_hit:
            # Free Hit: Half runs awarded, NOT OUT
            half_runs = batsman_num // 2
            bat_team.score += half_runs
            striker.runs += half_runs
            striker.balls_faced += 1
            bowler.balls_bowled += 1
            bowler.runs_conceded += half_runs
            
            gif_url = get_random_gif(MatchEvent.FREE_HIT)
            msg = f"⚡ <b>FREE HIT SAVE!</b> Numbers matched ({batsman_num}).\n"
            msg += f"🏃 <b>Runs Awarded:</b> {half_runs} (Half)\n"
            msg += "✅ <b>Not Out!</b>"
            
            try:
                if gif_url:
                    await context.bot.send_animation(group_id, animation=gif_url, caption=msg, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            except:
                await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            match.is_free_hit = False
            bowl_team.update_overs()
            
            match.ball_by_ball_log.append({
                "over": format_overs(bowl_team.balls - 1),
                "batsman": striker.first_name,
                "bowler": bowler.first_name,
                "result": f"Free Hit - {half_runs} runs",
                "runs": half_runs,
                "is_wicket": False
            })
            
        else:
            # NORMAL WICKET
            striker.is_out = True
            striker.dismissal_type = "Bowled"
            striker.balls_faced += 1
            bat_team.out_players_indices.add(bat_team.current_batsman_idx)
            bat_team.wickets += 1
            bowler.wickets += 1
            bowler.balls_bowled += 1
            
            if striker.runs == 0:
                striker.ducks = striker.ducks + 1 if hasattr(striker, 'ducks') else 1
            
            match.last_wicket_ball = {
                "batsman": striker,
                "bowler": bowler,
                "bowler_number": bowler_num,
                "batsman_number": batsman_num
            }
            
            gif_url = get_random_gif(MatchEvent.WICKET)
            commentary = get_random_commentary("wicket")
            
            msg = f"🏏 <b>Over {format_overs(bowl_team.balls)}</b>\n\n"
            msg += f"❌ <b>OUT!</b> {striker.first_name} is dismissed!\n"
            msg += f"📊 Score: {striker.runs} ({striker.balls_faced})\n"
            msg += f"🎯 Bowler: {bowler.first_name}\n\n"
            msg += f"💬 <i>{commentary}</i>\n\n"
            msg += f"📈 <b>Score:</b> {bat_team.score}/{bat_team.wickets}"
            
            try:
                if gif_url:
                    await context.bot.send_animation(group_id, animation=gif_url, caption=msg, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            except:
                await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
            
            bowl_team.update_overs()
            
            match.ball_by_ball_log.append({
                "over": format_overs(bowl_team.balls - 1),
                "batsman": striker.first_name,
                "bowler": bowler.first_name,
                "result": "Wicket",
                "runs": 0,
                "is_wicket": True
            })
            
            await asyncio.sleep(2)
            
            # ✅ FIXED: Offer DRS to Captain (10 seconds timeout)
            if bat_team.drs_remaining > 0:
                await offer_drs_to_captain(context, group_id, match)
                return
            else:
                # No DRS available, confirm wicket
                await confirm_wicket_and_continue(context, group_id, match)
                return
    
    # ===== RUNS SCORED =====
    else:
        runs = batsman_num
        bat_team.score += runs
        striker.runs += runs
        striker.balls_faced += 1
        bowler.balls_bowled += 1
        bowler.runs_conceded += runs
        
        if runs == 4:
            striker.boundaries = striker.boundaries + 1 if hasattr(striker, 'boundaries') else 1
        elif runs == 6:
            striker.sixes = striker.sixes + 1 if hasattr(striker, 'sixes') else 1
        
        if runs == 0:
            commentary_key = "dot"
            event = MatchEvent.DOT_BALL
            striker.dot_balls_faced += 1
            bowler.dot_balls_bowled += 1
        elif runs == 1:
            commentary_key = "single"
            event = MatchEvent.RUNS_1
        elif runs == 2:
            commentary_key = "double"
            event = MatchEvent.RUNS_2
        elif runs == 3:
            commentary_key = "triple"
            event = MatchEvent.RUNS_3
        elif runs == 4:
            commentary_key = "boundary"
            event = MatchEvent.RUNS_4
        elif runs == 5:
            commentary_key = "five"
            event = MatchEvent.RUNS_5
        else:
            commentary_key = "six"
            event = MatchEvent.RUNS_6
        
        gif_url = get_random_gif(event)
        commentary = get_random_commentary(commentary_key)
        
        msg = f"🏏 <b>Over {format_overs(bowl_team.balls)}</b>\n\n"
        if match.is_free_hit:
            msg += "⚡ <b>FREE HIT</b>\n"
            match.is_free_hit = False
        
        msg += f"🎯 <b>{runs} RUN{'S' if runs != 1 else ''}!</b>\n"
        msg += f"💬 <i>{commentary}</i>\n\n"
        msg += f"📊 <b>Score:</b> {bat_team.score}/{bat_team.wickets}"
        
        # ✅ FIXED: Add Run Rate
        current_rr = round(bat_team.score / max(bat_team.overs, 0.1), 2)
        msg += f"\n📈 <b>Run Rate:</b> {current_rr}"
        
        # ✅ FIXED: Add RRR if chasing
        if match.innings == 2:
            runs_needed = match.target - bat_team.score
            balls_left = (match.total_overs * 6) - bat_team.balls
            rrr = round((runs_needed / max(balls_left, 1)) * 6, 2) if balls_left > 0 else 0
            msg += f"\n🎯 <b>Need:</b> {runs_needed} runs in {balls_left} balls (RRR: {rrr})"
        
        try:
            if gif_url and runs > 0:
                await context.bot.send_animation(group_id, animation=gif_url, caption=msg, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
        except:
            await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
        
        bowl_team.update_overs()
        
        match.ball_by_ball_log.append({
            "over": format_overs(bowl_team.balls - 1),
            "batsman": striker.first_name,
            "bowler": bowler.first_name,
            "result": f"{runs} run{'s' if runs != 1 else ''}",
            "runs": runs,
            "is_wicket": False
        })
        
        if runs % 2 == 1:
            bat_team.swap_batsmen()
    
    match.current_ball_data = {}
    
    if bowl_team.get_current_over_balls() == 0:
        await check_over_complete(context, group_id, match)
    else:
        if match.innings == 2 and bat_team.score >= match.target:
            await end_innings(context, group_id, match)
        elif bat_team.balls >= match.total_overs * 6:
            await end_innings(context, group_id, match)
        else:
            await asyncio.sleep(2)
            await execute_ball(context, group_id, match)

async def offer_drs_to_captain(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Offer DRS to Captain with 10 second timeout"""
    batting_captain = match.get_captain(match.current_batting_team)
    batsman = match.last_wicket_ball["batsman"]
    
    captain_tag = f"<a href='tg://user?id={batting_captain.user_id}'>{batting_captain.first_name}</a>"
    
    msg = f"📺 <b>DRS AVAILABLE</b> 📺\n"
    msg += "━━━━━━━━━━━━━━━\n"
    msg += f"❌ <b>{batsman.first_name}</b> is given OUT!\n"
    msg += f"👤 Captain {captain_tag}\n\n"
    msg += f"🔄 <b>DRS Remaining:</b> {match.current_batting_team.drs_remaining}\n"
    msg += "⏱ <b>You have 10 seconds to review!</b>\n\n"
    msg += "👉 Use <code>/drs</code> to take review"
    
    await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)
    
    match.drs_in_progress = True
    match.drs_offer_time = time.time()
    
    # 10 second timeout
    asyncio.create_task(drs_timeout_handler(context, group_id, match))

async def offer_drs(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Offer DRS to batting captain after wicket"""
    batsman = match.last_wicket_ball["batsman"]
    bowler = match.last_wicket_ball["bowler"]
    
    # Check if DRS available
    if match.current_batting_team.drs_remaining <= 0:
        # No DRS available, wicket confirmed
        await confirm_wicket(context, group_id, match, drs_used=False, drs_successful=False)
        return
    
    batting_captain = match.get_captain(match.current_batting_team)
    
    gif_url = get_random_gif(MatchEvent.WICKET)
    commentary = get_random_commentary("wicket")
    
    wicket_text = f"Over {format_overs(match.current_bowling_team.balls)}\n\n"
    wicket_text += f"Bowler: {match.last_wicket_ball['bowler_number']} | Batsman: {match.last_wicket_ball['batsman_number']}\n\n"
    wicket_text += "OUT - Bowled\n\n"
    wicket_text += f"{commentary}\n\n"
    wicket_text += f"{batsman.first_name}: {batsman.runs} ({batsman.balls_faced})\n\n"
    wicket_text += f"Captain {batting_captain.first_name}: You have {match.current_batting_team.drs_remaining} DRS review.\n"
    wicket_text += "Do you want to review this decision?\n\n"
    wicket_text += "Use /drs to review (30 seconds to decide)"
    
    try:
        if gif_url:
            await context.bot.send_animation(
                chat_id=group_id,
                animation=gif_url,
                caption=wicket_text
            )
        else:
            await context.bot.send_message(
                chat_id=group_id,
                text=wicket_text
            )
    except Exception as e:
        logger.error(f"Error sending wicket message: {e}")
        await context.bot.send_message(
            chat_id=group_id,
            text=wicket_text
        )
    
    match.drs_in_progress = True
    
    # Set timeout for DRS decision
    asyncio.create_task(drs_decision_timeout(context, group_id, match))

async def drs_timeout_handler(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle 10 second DRS timeout"""
    await asyncio.sleep(10)
    
    if not match.drs_in_progress:
        return
    
    # Timeout - No DRS taken
    match.drs_in_progress = False
    
    await context.bot.send_message(
        group_id,
        "⏱ <b>DRS Timeout!</b> Decision stands. Wicket confirmed.",
        parse_mode=ParseMode.HTML
    )
    
    await asyncio.sleep(1)
    await confirm_wicket_and_continue(context, group_id, match)

async def drs_decision_timeout(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Handle DRS decision timeout"""
    await asyncio.sleep(30)
    
    if not match.drs_in_progress:
        return
    
    # No DRS taken, confirm wicket
    match.drs_in_progress = False
    await confirm_wicket(context, group_id, match, drs_used=False, drs_successful=False)

# DRS command
async def drs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /drs command - Captain only"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        await update.message.reply_text("This command only works in groups.")
        return
    
    if chat.id not in active_matches:
        await update.message.reply_text("No active match found.")
        return
    
    match = active_matches[chat.id]
    
    if not match.drs_in_progress:
        await update.message.reply_text("No DRS review available at this moment.")
        return
    
    # Check if user is batting captain
    batting_captain = match.get_captain(match.current_batting_team)
    if user.id != batting_captain.user_id:
        await update.message.reply_text(
            f"⚠️ Only {match.current_batting_team.name} Captain can request DRS."
        )
        return
    
    # Process DRS
    match.drs_in_progress = False
    match.current_batting_team.drs_remaining -= 1
    
    await process_drs_review(context, chat.id, match)


async def process_drs_review(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Process DRS with 30% overturn chance"""
    batsman = match.last_wicket_ball["batsman"]
    
    drs_text = "📺 <b>DRS REVIEW IN PROGRESS</b>\n\n"
    drs_text += "🔍 Checking with third umpire...\n"
    drs_text += "⏳ Please wait..."
    
    gif_url = get_random_gif(MatchEvent.DRS_REVIEW)
    
    try:
        if gif_url:
            msg = await context.bot.send_animation(group_id, animation=gif_url, caption=drs_text, parse_mode=ParseMode.HTML)
        else:
            msg = await context.bot.send_message(group_id, drs_text, parse_mode=ParseMode.HTML)
    except:
        msg = await context.bot.send_message(group_id, drs_text, parse_mode=ParseMode.HTML)
    
    await asyncio.sleep(3)
    
    # 30% overturn chance
    is_overturned = random.random() < 0.30
    
    if is_overturned:
        # NOT OUT
        batsman.is_out = False
        match.current_batting_team.wickets -= 1
        match.current_batting_team.out_players_indices.discard(match.current_batting_team.current_batsman_idx)
        
        gif_url = get_random_gif(MatchEvent.DRS_NOT_OUT)
        
        result_text = "📺 <b>DRS RESULT</b>\n\n"
        result_text += "✅ <b>NOT OUT!</b>\n\n"
        result_text += f"🎉 {batsman.first_name} survives!\n"
        result_text += "Decision overturned.\n\n"
        result_text += f"🔄 DRS Remaining: {match.current_batting_team.drs_remaining}"
        
        try:
            if gif_url:
                await context.bot.send_animation(group_id, animation=gif_url, caption=result_text, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(group_id, result_text, parse_mode=ParseMode.HTML)
        except:
            await context.bot.send_message(group_id, result_text, parse_mode=ParseMode.HTML)
        
        await asyncio.sleep(2)
        
        # Continue with same batsman
        if match.current_bowling_team.get_current_over_balls() == 0:
            await check_over_complete(context, group_id, match)
        else:
            await execute_ball(context, group_id, match)
    else:
        # OUT confirmed
        gif_url = get_random_gif(MatchEvent.DRS_OUT)
        
        result_text = "📺 <b>DRS RESULT</b>\n\n"
        result_text += "❌ <b>OUT!</b>\n\n"
        result_text += "Decision stands.\n\n"
        result_text += f"📊 {batsman.first_name}: {batsman.runs} ({batsman.balls_faced})\n"
        result_text += f"🔄 DRS Remaining: {match.current_batting_team.drs_remaining}"
        
        try:
            if gif_url:
                await context.bot.send_animation(group_id, animation=gif_url, caption=result_text, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(group_id, result_text, parse_mode=ParseMode.HTML)
        except:
            await context.bot.send_message(group_id, result_text, parse_mode=ParseMode.HTML)
        
        await asyncio.sleep(2)
        await confirm_wicket_and_continue(context, group_id, match)

async def confirm_wicket_and_continue(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Confirm wicket and continue game - FIXED"""
    
    # Check innings complete
    if match.current_batting_team.is_all_out() or match.current_batting_team.balls >= match.total_overs * 6:
        await end_innings(context, group_id, match)
        return
    
    # Check if target chased
    if match.innings == 2 and match.current_batting_team.score >= match.target:
        await end_innings(context, group_id, match)
        return
    
    # Request new batsman (replace the OUT striker)
    match.waiting_for_batsman = True
    
    await asyncio.sleep(1)
    await request_batsman_selection(context, group_id, match)


async def confirm_wicket(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, drs_used: bool, drs_successful: bool):
    """Confirm wicket and update match state"""
    batsman = match.last_wicket_ball["batsman"]
    bowler = match.last_wicket_ball["bowler"]
    
    # Mark batsman as out
    batsman.is_out = True
    batsman.dismissal_type = "Bowled"
    match.current_batting_team.wickets += 1
    bowler.wickets += 1
    
    if drs_used and not drs_successful:
        gif_url = get_random_gif(MatchEvent.DRS_OUT)
        
        result_text = "DRS Result\n\n"
        result_text += "Decision: OUT\n\n"
        result_text += "The original decision stands.\n\n"
        result_text += f"{batsman.first_name}: {batsman.runs} ({batsman.balls_faced})\n\n"
        result_text += f"DRS Remaining: {match.current_batting_team.drs_remaining}\n\n"
        result_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}"
        
        try:
            if gif_url:
                await context.bot.send_animation(
                    chat_id=group_id,
                    animation=gif_url,
                    caption=result_text
                )
            else:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=result_text
                )
        except Exception as e:
            logger.error(f"Error sending DRS out message: {e}")
            await context.bot.send_message(
                chat_id=group_id,
                text=result_text
            )
    else:
        wicket_confirm_text = f"Wicket Confirmed\n\n"
        wicket_confirm_text += f"{batsman.first_name}: {batsman.runs} ({batsman.balls_faced})\n"
        wicket_confirm_text += f"Bowler: {bowler.first_name}\n\n"
        wicket_confirm_text += f"Score: {match.current_batting_team.score}/{match.current_batting_team.wickets}"
        
        await context.bot.send_message(
            chat_id=group_id,
            text=wicket_confirm_text
        )
    
    # Update stats
    batsman.balls_faced += 1
    bowler.balls_bowled += 1
    match.current_bowling_team.update_overs()
    
    # Check for duck
    if batsman.runs == 0:
        batsman.ducks += 1
    
    # Log ball
    match.ball_by_ball_log.append({
        "over": format_overs(match.current_bowling_team.balls - 1),
        "batsman": batsman.first_name,
        "bowler": bowler.first_name,
        "result": "Wicket",
        "runs": 0,
        "is_wicket": True
    })
    
    await asyncio.sleep(2)
    
    # Check if innings over
    if match.is_innings_complete():
        await end_innings(context, group_id, match)
    else:
        # Request new batsman
        match.waiting_for_batsman = True
        await request_batsman_selection(context, group_id, match)

async def check_over_complete(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """End of Over with Timeout Option"""
    
    bat_team = match.current_batting_team
    bowl_team = match.current_bowling_team
    
    striker = bat_team.players[bat_team.current_batsman_idx]
    non_striker = bat_team.players[bat_team.current_non_striker_idx]
    bowler = bowl_team.players[bowl_team.current_bowler_idx]
    
    bowl_team.bowler_history.append(bowl_team.current_bowler_idx)
    
    rr = round(bat_team.score / max(bat_team.overs, 1), 2)
    
    summary = f"🏏 <b>OVER COMPLETE</b> 🏏\n"
    summary += "━━━━━━━━━━━━━━━\n"
    summary += f"📊 Score: <b>{bat_team.score}/{bat_team.wickets}</b>\n"
    summary += f"📈 Run-Rate: {rr}\n"
    summary += f"🏏 Strike: {striker.first_name} ({striker.runs}*)\n"
    summary += f"👀 Non-Strike: {non_striker.first_name} ({non_striker.runs})\n"
    summary += f"⚾ Bowler: {bowler.first_name} ({bowler.wickets}/{bowler.runs_conceded})"
    
    # Check if timeout available
    timeout_available = False
    if bat_team == match.team_x and not match.team_x_timeout_used:
        timeout_available = True
    elif bat_team == match.team_y and not match.team_y_timeout_used:
        timeout_available = True
    
    if timeout_available:
        summary += f"\n\n⏸ Host can take Strategic Timeout: /timeout"
    
    await context.bot.send_message(group_id, summary, parse_mode=ParseMode.HTML)
    
    await asyncio.sleep(2)
    
    if bat_team.balls >= match.total_overs * 6:
        await end_innings(context, group_id, match)
    elif match.innings == 2 and bat_team.score >= match.target:
        await end_innings(context, group_id, match)
    else:
        bowl_team.current_bowler_idx = None
        await request_bowler_selection(context, group_id, match)

async def timeout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Strategic Timeout - Host Only"""
    
    chat = update.effective_chat
    user = update.effective_user

    # 1️⃣ Check active match
    if chat.id not in active_matches:
        await update.message.reply_text("⚠️ No active match running.")
        return

    match = active_matches[chat.id]

    # 2️⃣ Check host
    if user.id != match.host_id:
        await update.message.reply_text("⚠️ Only the Host can call a strategic timeout!")
        return

    # 3️⃣ Check match state safety
    if not match.current_batting_team or not match.current_bowling_team:
        await update.message.reply_text("⚠️ Timeout not allowed at this stage.")
        return

    bat_team = match.current_batting_team

    # 4️⃣ Initialize timeout flags (safe init)
    if not hasattr(match, "team_x_timeout_used"):
        match.team_x_timeout_used = False
    if not hasattr(match, "team_y_timeout_used"):
        match.team_y_timeout_used = False

    # 5️⃣ Check if timeout already used
    if bat_team == match.team_x and match.team_x_timeout_used:
        await update.message.reply_text("⚠️ Team X has already used its timeout!")
        return
    if bat_team == match.team_y and match.team_y_timeout_used:
        await update.message.reply_text("⚠️ Team Y has already used its timeout!")
        return

    # 6️⃣ Mark timeout as used
    if bat_team == match.team_x:
        match.team_x_timeout_used = True
    else:
        match.team_y_timeout_used = True

    match.last_activity = time.time()  # prevent auto-cleanup

    # 7️⃣ Timeout message
    msg = (
        "⏸ <b>STRATEGIC TIMEOUT</b> ⏸\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡 <b>{bat_team.name}</b> takes a break!\n\n"
        "⏱ <b>Duration:</b> 60 Seconds\n\n"
        "✅ Strike can be changed\n"
        "✅ Bowler can be changed\n"
        "✅ Team discussion allowed\n\n"
        "<i>Game will resume automatically...</i>"
    )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    # 8️⃣ Pause game for 60 seconds
    await asyncio.sleep(60)

    # 9️⃣ Resume announcement
    await context.bot.send_message(
        chat.id,
        "⏱ <b>Timeout Over!</b>\nGame resuming now...",
        parse_mode=ParseMode.HTML
    )

    await asyncio.sleep(2)

    # 🔟 Force new bowler selection (strategy impact)
    match.current_bowling_team.current_bowler_idx = None
    match.waiting_for_bowler = True

    await request_bowler_selection(context, chat.id, match)

async def end_innings(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """End current innings"""
    if match.innings == 1:
        # First innings complete
        first_innings_score = match.current_batting_team.score
        match.target = first_innings_score + 1
        
        gif_url = get_random_gif(MatchEvent.INNINGS_BREAK)
        
        innings_summary = "End of First Innings\n\n"
        innings_summary += f"{match.current_batting_team.name}: {match.current_batting_team.score}/{match.current_batting_team.wickets}\n"
        innings_summary += f"Overs: {format_overs(match.current_batting_team.balls)}\n\n"
        
        # Top scorer
        top_scorer = max(match.current_batting_team.players, key=lambda p: p.runs)
        innings_summary += f"Top Scorer: {top_scorer.first_name} - {top_scorer.runs} ({top_scorer.balls_faced})\n\n"
        
        # Best bowler
        bowling_team_players = [p for p in match.current_bowling_team.players if p.balls_bowled > 0]
        if bowling_team_players:
            best_bowler = max(bowling_team_players, key=lambda p: p.wickets)
            innings_summary += f"Best Bowler: {best_bowler.first_name} - {best_bowler.wickets}/{best_bowler.runs_conceded}\n\n"
        
        innings_summary += f"Target: {match.target} runs\n\n"
        innings_summary += "Innings break - 30 seconds"
        
        try:
            if gif_url:
                await context.bot.send_animation(
                    chat_id=group_id,
                    animation=gif_url,
                    caption=innings_summary
                )
            else:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=innings_summary
                )
        except Exception as e:
            logger.error(f"Error sending innings summary: {e}")
            await context.bot.send_message(
                chat_id=group_id,
                text=innings_summary
            )
        
        # Wait 30 seconds
        await asyncio.sleep(30)
        
        # Swap teams
        match.innings = 2
        match.current_batting_team = match.get_other_team(match.current_batting_team)
        match.current_bowling_team = match.get_other_team(match.current_bowling_team)
        
        # Start second innings
        second_innings_text = "Second Innings Begins\n\n"
        second_innings_text += f"{match.current_batting_team.name} needs {match.target} runs to win\n"
        second_innings_text += f"Overs: {match.total_overs}\n\n"
        second_innings_text += "Good luck!"
        
        await context.bot.send_message(
            chat_id=group_id,
            text=second_innings_text
        )
        
        await asyncio.sleep(2)
        
        # Request first batsman
        match.waiting_for_batsman = True
        await request_batsman_selection(context, group_id, match)
    else:
        # Second innings complete - determine winner
        await determine_match_winner(context, group_id, match)

async def determine_match_winner(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Determine winner with proper stats update"""
    first = match.batting_first
    second = match.get_other_team(first)
    
    winner = None
    loser = None
    margin = ""
    
    if second.score >= match.target:
        winner = second
        loser = first
        wickets_left = len(second.players) - second.wickets - len(second.out_players_indices)
        margin = f"{wickets_left} Wickets"
    elif first.score > second.score:
        winner = first
        loser = second
        margin = f"{first.score - second.score} Runs"
    else:
        await context.bot.send_message(group_id, "🤝 <b>MATCH TIED!</b>", parse_mode=ParseMode.HTML)
        # Update stats for tied match
        await update_player_stats_after_match(match, None, None)
        save_match_to_history(match, "TIE", "TIE")
        del active_matches[group_id]
        return

    # ✅ UPDATE PLAYER STATS
    await update_player_stats_after_match(match, winner, loser)
    
    # ✅ SAVE MATCH TO HISTORY
    save_match_to_history(match, winner.name, loser.name)
    
    # Send Victory Message with GIF
    await send_victory_message(context, group_id, match, winner, loser, margin)
    
    # Send Player of the Match
    await send_potm_message(context, group_id, match)
    
    # Cleanup
    try:
        if match.main_message_id:
            await context.bot.unpin_chat_message(chat_id=group_id, message_id=match.main_message_id)
    except: pass
    
    del active_matches[group_id]

async def start_super_over(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Start Super Over for tied match"""
    super_over_text = "Match Tied\n\n"
    super_over_text += f"Both teams scored {match.current_batting_team.score} runs!\n\n"
    super_over_text += "SUPER OVER\n\n"
    super_over_text += "Each team will play 1 over.\n"
    super_over_text += "Higher score wins.\n"
    super_over_text += "No DRS in Super Over.\n\n"
    super_over_text += "Starting in 10 seconds..."
    
    await context.bot.send_message(
        chat_id=group_id,
        text=super_over_text
    )
    
    await asyncio.sleep(10)
    
    match.is_super_over = True
    match.phase = GamePhase.SUPER_OVER
    
    # Reset for super over (to be continued in next part)
    # This will be implemented in Part 9

async def send_match_summary(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, winner: Team, loser: Team):
    """Send detailed match summary with player statistics"""
    
    # Batting summary for both teams
    summary_text = "Match Summary\n"
    summary_text += "=" * 40 + "\n\n"
    
    # First innings batting
    summary_text += f"{match.batting_first.name} Batting\n"
    summary_text += "-" * 40 + "\n"
    for player in match.batting_first.players:
        if player.balls_faced > 0 or player.is_out:
            status = "out" if player.is_out else "not out"
            sr = player.get_strike_rate()
            summary_text += f"{player.first_name}: {player.runs} ({player.balls_faced}) - {status}"
            if player.boundaries > 0:
                summary_text += f" [{player.boundaries}x4"
                if player.sixes > 0:
                    summary_text += f", {player.sixes}x6"
                summary_text += "]"
            summary_text += f" SR: {sr}\n"
    
    summary_text += f"\nTotal: {match.batting_first.score}/{match.batting_first.wickets}\n"
    summary_text += f"Overs: {format_overs(match.batting_first.balls)}\n"
    summary_text += f"Extras: {match.batting_first.extras}\n\n"
    
    # Second innings batting
    summary_text += f"{match.bowling_first.name} Batting\n"
    summary_text += "-" * 40 + "\n"
    for player in match.bowling_first.players:
        if player.balls_faced > 0 or player.is_out:
            status = "out" if player.is_out else "not out"
            sr = player.get_strike_rate()
            summary_text += f"{player.first_name}: {player.runs} ({player.balls_faced}) - {status}"
            if player.boundaries > 0:
                summary_text += f" [{player.boundaries}x4"
                if player.sixes > 0:
                    summary_text += f", {player.sixes}x6"
                summary_text += "]"
            summary_text += f" SR: {sr}\n"
    
    summary_text += f"\nTotal: {match.bowling_first.score}/{match.bowling_first.wickets}\n"
    summary_text += f"Overs: {format_overs(match.bowling_first.balls)}\n"
    summary_text += f"Extras: {match.bowling_first.extras}\n\n"
    
    await context.bot.send_message(
        chat_id=group_id,
        text=summary_text
    )
    
    await asyncio.sleep(1)
    
    # Bowling summary
    bowling_summary = "Bowling Figures\n"
    bowling_summary += "=" * 40 + "\n\n"
    
    # First innings bowling
    bowling_summary += f"{match.bowling_first.name} Bowling\n"
    bowling_summary += "-" * 40 + "\n"
    for player in match.bowling_first.players:
        if player.balls_bowled > 0:
            overs = format_overs(player.balls_bowled)
            economy = player.get_economy()
            bowling_summary += f"{player.first_name}: {overs} overs, {player.wickets}/{player.runs_conceded}"
            bowling_summary += f" Econ: {economy}"
            if player.maiden_overs > 0:
                bowling_summary += f" M: {player.maiden_overs}"
            bowling_summary += "\n"
    
    bowling_summary += "\n"
    
    # Second innings bowling
    bowling_summary += f"{match.batting_first.name} Bowling\n"
    bowling_summary += "-" * 40 + "\n"
    for player in match.batting_first.players:
        if player.balls_bowled > 0:
            overs = format_overs(player.balls_bowled)
            economy = player.get_economy()
            bowling_summary += f"{player.first_name}: {overs} overs, {player.wickets}/{player.runs_conceded}"
            bowling_summary += f" Econ: {economy}"
            if player.maiden_overs > 0:
                bowling_summary += f" M: {player.maiden_overs}"
            bowling_summary += "\n"
    
    await context.bot.send_message(
        chat_id=group_id,
        text=bowling_summary
    )
    
    await asyncio.sleep(1)
    
    # Player of the Match
    potm_text = "Player of the Match\n"
    potm_text += "=" * 40 + "\n\n"
    
    # Calculate POTM based on performance
    all_players = match.batting_first.players + match.bowling_first.players
    best_player = None
    best_score = 0
    
    for player in all_players:
        # Score calculation: runs + (wickets * 20) + (boundaries * 2)
        performance_score = player.runs + (player.wickets * 20) + (player.boundaries * 2)
        if performance_score > best_score:
            best_score = performance_score
            best_player = player
    
    if best_player:
        potm_text += f"{best_player.first_name}\n\n"
        if best_player.balls_faced > 0:
            potm_text += f"Batting: {best_player.runs} ({best_player.balls_faced}) SR: {best_player.get_strike_rate()}\n"
        if best_player.balls_bowled > 0:
            potm_text += f"Bowling: {best_player.wickets}/{best_player.runs_conceded} Econ: {best_player.get_economy()}\n"
    
    await context.bot.send_message(
        chat_id=group_id,
        text=potm_text
    )

async def update_player_stats_after_match(match: Match, winner: Team, loser: Team):
    """Update global player statistics after match - FIXED"""
    all_players = match.batting_first.players + match.bowling_first.players
    
    for player in all_players:
        user_id = player.user_id
        
        # Initialize if needed
        if user_id not in player_stats:
            init_player_stats(user_id)
        
        stats = player_stats[user_id]
        
        # Update match count
        stats["matches_played"] += 1
        
        # Check if winner (handle tied match)
        if winner:
            is_winner = (player in winner.players)
            if is_winner:
                stats["matches_won"] += 1
        
        # Update batting stats
        if player.balls_faced > 0:
            stats["total_runs"] += player.runs
            stats["total_balls_faced"] += player.balls_faced
            stats["dot_balls_faced"] += player.dot_balls_faced
            stats["boundaries"] += getattr(player, 'boundaries', 0)
            stats["sixes"] += getattr(player, 'sixes', 0)
            
            # Check for century/half-century
            if player.runs >= 100:
                stats["centuries"] += 1
            elif player.runs >= 50:
                stats["half_centuries"] += 1
            
            # Update highest score
            if player.runs > stats["highest_score"]:
                stats["highest_score"] = player.runs
            
            # Check for duck
            if player.runs == 0 and player.is_out:
                stats["ducks"] += 1
            
            # Update last 5 scores
            stats["last_5_scores"].append(player.runs)
            if len(stats["last_5_scores"]) > 5:
                stats["last_5_scores"].pop(0)
        
        # Update bowling stats
        if player.balls_bowled > 0:
            stats["total_wickets"] += player.wickets
            stats["total_balls_bowled"] += player.balls_bowled
            stats["total_runs_conceded"] += player.runs_conceded
            stats["dot_balls_bowled"] += player.dot_balls_bowled
            stats["total_no_balls"] += player.no_balls
            stats["total_wides"] += player.wides
            
            # Update best bowling
            if player.wickets > stats["best_bowling"]["wickets"]:
                stats["best_bowling"]["wickets"] = player.wickets
                stats["best_bowling"]["runs"] = player.runs_conceded
            elif player.wickets == stats["best_bowling"]["wickets"] and player.runs_conceded < stats["best_bowling"]["runs"]:
                stats["best_bowling"]["runs"] = player.runs_conceded
            
            # Update last 5 wickets
            stats["last_5_wickets"].append(player.wickets)
            if len(stats["last_5_wickets"]) > 5:
                stats["last_5_wickets"].pop(0)
        
        # Update timeouts
        stats["total_timeouts"] += player.batting_timeouts + player.bowling_timeouts
    
    # Save to disk
    save_data()

async def send_potm_message(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Send Player of the Match with detailed stats"""
    
    # Calculate POTM
    all_players = match.batting_first.players + match.bowling_first.players
    
    # Performance scoring: runs + (wickets * 25) + (boundaries * 3) + (sixes * 5)
    best_player = None
    best_score = 0
    
    for player in all_players:
        performance = player.runs + (player.wickets * 25) + (player.boundaries * 3) + (player.sixes * 5)
        if performance > best_score:
            best_score = performance
            best_player = player
    
    if not best_player:
        return
    
    potm_gif = "https://media.giphy.com/media/26u4cqiYI30juCOGY/giphy.gif"
    
    msg = f"⭐ <b>PLAYER OF THE MATCH</b> ⭐\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    player_tag = f"<a href='tg://user?id={best_player.user_id}'>{best_player.first_name}</a>"
    msg += f"🏅 <b>{player_tag}</b>\n\n"
    
    # Batting Performance
    if best_player.balls_faced > 0:
        msg += f"🏏 <b>BATTING</b>\n"
        msg += f"   Runs: <b>{best_player.runs}</b> ({best_player.balls_faced} balls)\n"
        msg += f"   Strike Rate: <b>{best_player.get_strike_rate()}</b>\n"
        if best_player.boundaries > 0:
            msg += f"   Boundaries: {best_player.boundaries} 4s"
            if best_player.sixes > 0:
                msg += f", {best_player.sixes} 6s"
            msg += "\n"
        msg += "\n"
    
    # Bowling Performance
    if best_player.balls_bowled > 0:
        msg += f"⚾ <b>BOWLING</b>\n"
        msg += f"   Wickets: <b>{best_player.wickets}/{best_player.runs_conceded}</b>\n"
        msg += f"   Overs: {format_overs(best_player.balls_bowled)}\n"
        msg += f"   Economy: <b>{best_player.get_economy()}</b>\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "<i>Outstanding performance! 👏</i>"
    
    try:
        await context.bot.send_animation(
            group_id,
            animation=potm_gif,
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except:
        await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)

async def send_victory_message(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match, winner: Team, loser: Team, margin: str):
    """Send beautiful victory message with GIF"""
    
    victory_gif = get_random_gif(MatchEvent.VICTORY)
    
    msg = f"🏆 <b>MATCH RESULT</b> 🏆\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += f"🎉 <b>WINNER: {winner.name.upper()}</b> 🎉\n"
    msg += f"🔥 <b>Won by:</b> {margin}\n\n"
    
    msg += f"📊 <b>FINAL SCORES</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🔹 <b>{match.batting_first.name}</b>\n"
    msg += f"   Score: <b>{match.batting_first.score}/{match.batting_first.wickets}</b>\n"
    msg += f"   Overs: {format_overs(match.batting_first.balls)}\n\n"
    
    msg += f"🔸 <b>{match.bowling_first.name}</b>\n"
    msg += f"   Score: <b>{match.bowling_first.score}/{match.bowling_first.wickets}</b>\n"
    msg += f"   Overs: {format_overs(match.bowling_first.balls)}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━"
    
    try:
        await context.bot.send_animation(
            group_id,
            animation=victory_gif,
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except:
        await context.bot.send_message(group_id, msg, parse_mode=ParseMode.HTML)

def check_achievements(player: Player):
    """Check and award achievements to player"""
    user_id = player.user_id
    stats = player_stats.get(user_id)
    
    if not stats:
        return
    
    if user_id not in achievements:
        achievements[user_id] = []
    
    user_achievements = achievements[user_id]
    
    # Century Maker
    if stats["centuries"] >= 1 and "Century Maker" not in user_achievements:
        user_achievements.append("Century Maker")
    
    # Hat-trick Hero (3 wickets in match)
    if player.wickets >= 3 and "Hat-trick Hero" not in user_achievements:
        user_achievements.append("Hat-trick Hero")
    
    # Diamond Hands (50+ matches)
    if stats["matches_played"] >= 50 and "Diamond Hands" not in user_achievements:
        user_achievements.append("Diamond Hands")
    
    # Speed Demon (Strike Rate > 200 in a match with 10+ runs)
    if player.runs >= 10 and player.get_strike_rate() > 200 and "Speed Demon" not in user_achievements:
        user_achievements.append("Speed Demon")
    
    # Economical (Economy < 5 in a match with 12+ balls bowled)
    if player.balls_bowled >= 12 and player.get_economy() < 5 and "Economical" not in user_achievements:
        user_achievements.append("Economical")

def save_match_to_history(match: Match, winner_name: str, loser_name: str):
    """Save match details to history"""
    match_record = {
        "match_id": match.match_id,
        "group_id": match.group_id,
        "group_name": match.group_name,
        "date": match.created_at.isoformat(),
        "overs": match.total_overs,
        "winner": winner_name,
        "loser": loser_name,
        "team_x_score": match.team_x.score,
        "team_x_wickets": match.team_x.wickets,
        "team_y_score": match.team_y.score,
        "team_y_wickets": match.team_y.wickets,
        "total_balls": len(match.ball_by_ball_log)
    }
    
    match_history.append(match_record)
    
    # Update group stats
    if match.group_id in registered_groups:
        registered_groups[match.group_id]["total_matches"] += 1
    
    save_data()

# Stats commands
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Beautiful stats display - IMPROVED"""
    user = update.effective_user
    
    if user.id not in player_stats:
        await update.message.reply_text(
            "❌ <b>No Career Data Found</b>\n\n"
            "You haven't played any matches yet.\n"
            "Join a game with /game to start! 🎮",
            parse_mode=ParseMode.HTML
        )
        return
    
    stats = player_stats[user.id]
    
    matches_played = stats["matches_played"]
    matches_won = stats["matches_won"]
    win_rate = (matches_won / matches_played * 100) if matches_played > 0 else 0
    
    total_runs = stats["total_runs"]
    total_balls = stats["total_balls_faced"]
    avg_runs = (total_runs / matches_played) if matches_played > 0 else 0
    strike_rate = (total_runs / total_balls * 100) if total_balls > 0 else 0
    
    total_wickets = stats["total_wickets"]
    total_balls_bowled = stats["total_balls_bowled"]
    total_conceded = stats["total_runs_conceded"]
    bowling_avg = (total_conceded / total_wickets) if total_wickets > 0 else 0
    economy = (total_conceded / (total_balls_bowled / 6)) if total_balls_bowled > 0 else 0
    
    user_tag = get_user_tag(user)
    
    msg = f"📊 <b>CRICOVERSE STATISTICS</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👤 {user_tag}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += f"🏆 <b>CAREER OVERVIEW</b>\n"
    msg += f"• Matches Played: <b>{matches_played}</b>\n"
    msg += f"• Matches Won: <b>{matches_won}</b>\n"
    msg += f"• Win Rate: <b>{win_rate:.1f}%</b>\n\n"
    
    msg += f"🏏 <b>BATTING</b>\n"
    msg += f"<code>Runs   : {total_runs:<6} Avg: {avg_runs:.2f}</code>\n"
    msg += f"<code>Balls  : {total_balls:<6} SR : {strike_rate:.1f}</code>\n"
    msg += f"<code>HS     : {stats['highest_score']:<6} Ducks: {stats['ducks']}</code>\n"
    msg += f"<code>100s   : {stats['centuries']:<6} 50s: {stats['half_centuries']}</code>\n"
    msg += f"💥 Boundaries: {stats['boundaries']} 4s | {stats['sixes']} 6s\n\n"
    
    msg += f"⚾ <b>BOWLING</b>\n"
    msg += f"<code>Wkts   : {total_wickets:<6} Avg: {bowling_avg:.2f}</code>\n"
    msg += f"<code>Balls  : {total_balls_bowled:<6} Eco: {economy:.2f}</code>\n"
    msg += f"<code>Best   : {stats['best_bowling']['wickets']}/{stats['best_bowling']['runs']}</code>\n"
    msg += f"🎯 Dot Balls: {stats['dot_balls_bowled']}\n\n"
    
    # Recent form
    last_5 = stats.get("last_5_scores", [])
    if last_5:
        form = "  ".join(f"<b>{x}</b>" for x in reversed(last_5))
        msg += f"📉 <b>RECENT FORM</b>\n{form}\n\n"
    
    msg += "━━━━━━━━━━━━━━━━━━━━━━━"
    
    try:
        await update.message.reply_photo(
            photo=MEDIA_ASSETS.get("stats"),
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays a clean, professional career statistics card for the user.
    Focus: readability, hierarchy, premium look.
    """
    user = update.effective_user

    # 1. Check if user exists
    if user.id not in player_stats:
        await update.message.reply_text(
            "❌ <b>No Career Data Found</b>\n\n"
            "You haven’t played any matches yet.\n"
            "Join a game and start building your legacy 🏏",
            parse_mode=ParseMode.HTML
        )
        return

    s = player_stats[user.id]
    ach_list = achievements.get(user.id, [])

    # ---------------- DERIVED METRICS ----------------

    matches = s.get('matches_played', 0)
    wins = s.get('matches_won', 0)
    win_rate = (wins / matches * 100) if matches else 0.0

    runs = s.get('total_runs', 0)
    balls = s.get('total_balls_faced', 0)
    bat_avg = (runs / matches) if matches else 0.0
    bat_sr = (runs / balls * 100) if balls else 0.0

    fours = s.get('boundaries', 0)
    sixes = s.get('sixes', 0)
    dots_faced = s.get('dot_balls_faced', 0)

    wickets = s.get('total_wickets', 0)
    balls_bowled = s.get('total_balls_bowled', 0)
    runs_conceded = s.get('total_runs_conceded', 0)
    overs_bowled = balls_bowled / 6 if balls_bowled else 0

    bowl_avg = (runs_conceded / wickets) if wickets else 0.0
    bowl_econ = (runs_conceded / overs_bowled) if overs_bowled else 0.0
    bowl_sr = (balls_bowled / wickets) if wickets else 0.0
    best_fig = f"{s['best_bowling']['wickets']}/{s['best_bowling']['runs']}"

    # ---------------- PLAYER RANK ----------------

    rank_title = "🆕 Rookie"
    if matches >= 10: rank_title = "⭐ Amateur"
    if matches >= 25: rank_title = "🔥 Pro"
    if matches >= 50: rank_title = "👑 Veteran"
    if matches >= 100: rank_title = "🦁 Legend"
    if matches >= 500: rank_title = "🐐 GOAT"

    # ---------------- MESSAGE ----------------

    joined_date = datetime.fromisoformat(
        user_data[user.id].get("started_at", datetime.now().isoformat())
    ).strftime("%d %b %Y")

    msg = (
        "📊 <b>CRICOVERSE PLAYER PROFILE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 {get_user_tag(user)}\n"
        f"🏅 <b>Rank:</b> {rank_title}\n"
        f"📅 <b>Joined:</b> {joined_date}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    # -------- CAREER OVERVIEW --------
    msg += (
        "🏆 <b>CAREER OVERVIEW</b>\n"
        f"• Matches Played : <b>{matches}</b>\n"
        f"• Matches Won    : <b>{wins}</b>\n"
        f"• Win Rate       : <b>{win_rate:.1f}%</b>\n"
    )

    if s.get("total_timeouts", 0) > 0:
        msg += f"• Timeouts       : <b>{s['total_timeouts']}</b>\n"

    msg += "\n"

    # -------- BATTING --------
    msg += (
        "🏏 <b>BATTING</b>\n"
        f"<code>Runs   : {runs:<6} Avg : {bat_avg:.2f}</code>\n"
        f"<code>Balls  : {balls:<6} SR  : {bat_sr:.1f}</code>\n"
        f"<code>HS     : {s['highest_score']:<6} Ducks: {s['ducks']}</code>\n"
        f"<code>100s   : {s['centuries']:<6} 50s  : {s['half_centuries']}</code>\n"
        f"💥 Boundaries : {fours} x4  |  {sixes} x6\n"
        f"🛡 Dot Balls  : {dots_faced} ({(dots_faced/balls*100) if balls else 0:.0f}%)\n\n"
    )

    # -------- BOWLING --------
    msg += (
        "⚾ <b>BOWLING</b>\n"
        f"<code>Wkts   : {wickets:<6} Avg : {bowl_avg:.2f}</code>\n"
        f"<code>Overs  : {overs_bowled:<6.1f} Eco : {bowl_econ:.2f}</code>\n"
        f"<code>Best   : {best_fig:<6} SR  : {bowl_sr:.1f}</code>\n"
        f"🎯 Dot Balls : {s.get('dot_balls_bowled', 0)}\n"
        f"🚫 Extras   : {s.get('total_wides', 0) + s.get('total_no_balls', 0)}\n\n"
    )

    # -------- RECENT FORM --------
    last_5 = s.get("last_5_scores", [])
    if last_5:
        form = "  ".join(f"<b>{x}</b>" for x in reversed(last_5))
        msg += (
            f"📉 <b>RECENT FORM</b> (Last {len(last_5)})\n"
            f"{form}\n\n"
        )

    # -------- ACHIEVEMENTS --------
    if ach_list:
        msg += f"🎖 <b>ACHIEVEMENTS</b>\n"
        for ach in ach_list[:3]:
            msg += f"• {ach}\n"
        if len(ach_list) > 3:
            msg += f"<i>…and {len(ach_list) - 3} more</i>\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━"

    # -------- SEND --------
    try:
        await update.message.reply_photo(
            photo=MEDIA_ASSETS.get("stats"),
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except Exception:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def h2h_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Head-to-Head Comparison UI"""
    
    # 1. Agar arguments nahi hain to "Usage Guide" dikhao
    if not context.args or len(context.args) < 2:
        msg = "⚔️ <b>HEAD-TO-HEAD BATTLES</b> ⚔️\n"
        msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += "Compare stats between two players!\n\n"
        msg += "👇 <b>How to Use:</b>\n"
        msg += "<code>/h2h @player1 @player2</code>\n\n"
        msg += "<i>See who is the real champion!</i> 🏆"
        
        try:
            await update.message.reply_photo(
                photo=MEDIA_ASSETS["h2h"],
                caption=msg,
                parse_mode=ParseMode.HTML
            )
        except:
            await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
        return

    # 2. Mock / Placeholder UI (Jab user arguments de)
    user1_name = context.args[0]
    user2_name = context.args[1]
    
    # Fancy Versus Card
    msg = f"⚔️ <b>RIVALRY CLASH</b> ⚔️\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👤 <b>{user1_name}</b>  🆚  👤 <b>{user2_name}</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "🏆 <b>HEAD TO HEAD</b>\n"
    msg += f"├ Matches: <b>0</b>\n"
    msg += f"├ Won by {user1_name}: <b>0</b>\n"
    msg += f"└ Won by {user2_name}: <b>0</b>\n\n"
    
    msg += "🏏 <b>BATTING COMPARISON</b>\n"
    msg += f"├ Runs: <code>0</code> 🆚 <code>0</code>\n"
    msg += f"├ SR: <code>0.0</code> 🆚 <code>0.0</code>\n"
    msg += f"└ 6s: <code>0</code> 🆚 <code>0</code>\n\n"
    
    msg += "⚾ <b>BOWLING COMPARISON</b>\n"
    msg += f"├ Wickets: <code>0</code> 🆚 <code>0</code>\n"
    msg += f"└ Econ: <code>0.0</code> 🆚 <code>0.0</code>\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += "<i>Real-time comparison feature coming soon!</i>"

    try:
        await update.message.reply_photo(
            photo=MEDIA_ASSETS["h2h"],
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# Owner/Admin commands
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast to ALL Groups AND Private DMs with HTML"""
    user = update.effective_user
    if user.id != OWNER_ID: return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ <b>Usage:</b> Reply to a message to broadcast.", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text("📢 <b>Starting Broadcast...</b>\n<i>Sending to Groups & DMs...</i>", parse_mode=ParseMode.HTML)
    
    success_groups = 0
    success_users = 0
    
    # 1. Broadcast to Groups
    for chat_id in list(registered_groups.keys()):
        try:
            await context.bot.copy_message(chat_id=chat_id, from_chat_id=update.message.chat_id, message_id=update.message.reply_to_message.message_id)
            success_groups += 1
            await asyncio.sleep(0.05)
        except: pass

    # 2. Broadcast to Users (DM)
    for user_id in list(user_data.keys()):
        try:
            await context.bot.copy_message(chat_id=user_id, from_chat_id=update.message.chat_id, message_id=update.message.reply_to_message.message_id)
            success_users += 1
            await asyncio.sleep(0.05)
        except: pass

    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        text=f"✅ <b>Broadcast Complete!</b>\n\n👥 <b>Groups:</b> {success_groups}\n👤 <b>DMs:</b> {success_users}",
        parse_mode=ParseMode.HTML
    )


async def botstats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot Statistics Dashboard"""
    user = update.effective_user
    
    # Check Admin
    if user.id != OWNER_ID:
        await update.message.reply_text("🔒 <b>Access Denied:</b> Owner only command.", parse_mode=ParseMode.HTML)
        return
    
    # Calculate Uptime
    uptime_seconds = int(time.time() - bot_start_time)
    uptime_days = uptime_seconds // 86400
    uptime_hours = (uptime_seconds % 86400) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    
    # Calculate Balls
    total_balls = sum(match.get("total_balls", 0) for match in match_history)
    
    # Find Active Group
    most_active = "N/A"
    if match_history:
        group_counts = {}
        for m in match_history:
            gid = m.get("group_id")
            group_counts[gid] = group_counts.get(gid, 0) + 1
        if group_counts:
            top_gid = max(group_counts, key=group_counts.get)
            most_active = registered_groups.get(top_gid, {}).get("group_name", "Unknown")

    # Dashboard Message
    msg = "🤖 <b>SYSTEM DASHBOARD</b> 🤖\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"⏱ <b>Uptime:</b> <code>{uptime_days}d {uptime_hours}h {uptime_minutes}m</code>\n"
    msg += f"📡 <b>Status:</b> 🟢 Online\n"
    msg += f"💾 <b>Database:</b> {os.path.getsize(USERS_FILE) // 1024} KB (Healthy)\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    msg += "📈 <b>TRAFFIC STATS</b>\n"
    msg += f"👥 <b>Total Users:</b> <code>{len(user_data)}</code>\n"
    msg += f"🛡 <b>Total Groups:</b> <code>{len(registered_groups)}</code>\n"
    msg += f"🎮 <b>Live Matches:</b> <code>{len(active_matches)}</code>\n\n"
    
    msg += "🏏 <b>GAMEPLAY STATS</b>\n"
    msg += f"🏆 <b>Matches Finished:</b> <code>{len(match_history)}</code>\n"
    msg += f"⚾ <b>Balls Bowled:</b> <code>{total_balls}</code>\n"
    msg += f"🔥 <b>Top Group:</b> {most_active}\n"
    msg += "━━━━━━━━━━━━━━━━━━━━━━"
    
    try:
        await update.message.reply_photo(
            photo=MEDIA_ASSETS["botstats"],
            caption=msg,
            parse_mode=ParseMode.HTML
        )
    except:
        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

# 1. Manual Backup Command
async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manually send FULL data backup to Owner"""
    user = update.effective_user
    if user.id != OWNER_ID: return

    try:
        # Create consolidated data dictionary
        full_backup = {
            "users": user_data,
            "matches": match_history,
            "stats": player_stats,
            "achievements": achievements,
            "groups": registered_groups,
            "backup_time": datetime.now().isoformat()
        }
        
        # Save to a temporary file in BACKUP_DIR
        filename = f"full_backup_{int(time.time())}.json"
        file_path = os.path.join(BACKUP_DIR, filename)
        
        with open(file_path, 'w') as f:
            json.dump(full_backup, f, indent=2)

        # Send the file
        await update.message.reply_document(
            document=open(file_path, 'rb'),
            caption=f"📦 <b>Full System Backup</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.HTML
        )
        
        # Optional: Remove file after sending to save space
        # os.remove(file_path)
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        await update.message.reply_text(f"❌ Backup Failed: {e}")

# 2. Automated Backup Job (Background Task)
async def auto_backup_job(context: ContextTypes.DEFAULT_TYPE):
    """Automatically send FULL backup to Owner's DM"""
    try:
        # Create consolidated data dictionary
        full_backup = {
            "users": user_data,
            "matches": match_history,
            "stats": player_stats,
            "achievements": achievements,
            "groups": registered_groups,
            "backup_time": datetime.now().isoformat()
        }
        
        filename = f"auto_backup_{int(time.time())}.json"
        file_path = os.path.join(BACKUP_DIR, filename)
        
        with open(file_path, 'w') as f:
            json.dump(full_backup, f, indent=2)

        await context.bot.send_document(
            chat_id=OWNER_ID,
            document=open(file_path, 'rb'),
            caption=f"🤖 <b>Auto-Backup System</b>\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Auto-backup failed: {e}")

async def restore_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /restore command - Owner only"""
    user = update.effective_user
    
    # Security Check
    if user.id != OWNER_ID:
        await update.message.reply_text("🔒 Access Denied: Owner only.")
        return
    
    # File Check
    if not update.message.reply_to_message or not update.message.reply_to_message.document:
        await update.message.reply_text("⚠️ Please reply to a valid Backup JSON file with /restore")
        return
    
    # Active Match Check
    if active_matches:
        await update.message.reply_text("⚠️ Cannot restore while matches are running! Please wait for them to finish.")
        return
    
    try:
        status_msg = await update.message.reply_text("⏳ <b>Restoring Data...</b>", parse_mode=ParseMode.HTML)
        
        # Download file
        file = await update.message.reply_to_message.document.get_file()
        restore_path = os.path.join(BACKUP_DIR, "restore_temp.json")
        await file.download_to_drive(restore_path)
        
        # Load and Validate
        with open(restore_path, 'r') as f:
            backup_data = json.load(f)
            
        # Basic Validation: Check if it's a full backup
        if "users" not in backup_data and "stats" not in backup_data:
            await status_msg.edit_text("❌ <b>Invalid Backup File!</b>\nThis looks like an old or empty file. Restore cancelled.")
            os.remove(restore_path)
            return
        
        # Restore Globals
        global user_data, match_history, player_stats, achievements, registered_groups
        
        # Use .get() to handle missing keys safely
        if "users" in backup_data:
            user_data = {int(k): v for k, v in backup_data["users"].items()}
            
        if "matches" in backup_data:
            match_history = backup_data["matches"]
            
        if "stats" in backup_data:
            player_stats = {int(k): v for k, v in backup_data["stats"].items()}
            
        if "achievements" in backup_data:
            achievements = {int(k): v for k, v in backup_data["achievements"].items()}
            
        if "groups" in backup_data:
            registered_groups = {int(k): v for k, v in backup_data["groups"].items()}
        
        # Save to disk immediately
        save_data()
        
        # Cleanup
        os.remove(restore_path)
        
        backup_time = backup_data.get("backup_time", "Unknown")
        
        success_text = f"✅ <b>System Restored Successfully!</b>\n"
        success_text += f"📅 <b>Backup Date:</b> {backup_time}\n"
        success_text += f"👥 <b>Users:</b> {len(user_data)}\n"
        success_text += f"📊 <b>Stats Loaded:</b> {len(player_stats)}\n"
        success_text += f"🏆 <b>Matches:</b> {len(match_history)}"
        
        await status_msg.edit_text(success_text, parse_mode=ParseMode.HTML)
        logger.info("Data restored successfully via command.")
        
    except Exception as e:
        logger.error(f"Error restoring backup: {e}")
        await update.message.reply_text(f"❌ <b>Restore Failed:</b> {str(e)}", parse_mode=ParseMode.HTML)

async def endmatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force end match (Owner + Group Admins)"""
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.id not in active_matches:
        await update.message.reply_text("No active match to end.")
        return

    # Check Admin Rights
    member = await chat.get_member(user.id)
    is_admin = member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    
    if user.id != OWNER_ID and not is_admin:
        await update.message.reply_text("❌ Only Group Admins can end the match!")
        return
        
    match = active_matches[chat.id]
    
    # Cleanup
    try:
        if match.main_message_id:
            await context.bot.unpin_chat_message(chat_id=chat.id, message_id=match.main_message_id)
    except: pass
    
    del active_matches[chat.id]
    await update.message.reply_text("✅ Match ended forcefully by Admin.")

async def resetmatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /resetmatch command - Owner only"""
    user = update.effective_user
    
    # Check if owner
    if user.id != OWNER_ID:
        await update.message.reply_text(
            "This command is restricted to the bot owner."
        )
        return
    
    chat = update.effective_chat
    
    if chat.id not in active_matches:
        await update.message.reply_text("No active match in this group.")
        return
    
    match = active_matches[chat.id]
    
    # Cancel all tasks
    if match.join_phase_task:
        match.join_phase_task.cancel()
    if match.ball_timeout_task:
        match.ball_timeout_task.cancel()
    if match.batsman_selection_task:
        match.batsman_selection_task.cancel()
    if match.bowler_selection_task:
        match.bowler_selection_task.cancel()
    
    # Reset match to team joining phase
    del active_matches[chat.id]
    
    await update.message.reply_text(
        "Match has been reset by bot owner.\n"
        "Use /game to start a new match."
    )
    
    logger.info(f"Match in group {chat.id} reset by owner")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    # Notify owner about error
    try:
        error_text = f"An error occurred:\n\n{str(context.error)}"
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=error_text
        )
    except Exception as e:
        logger.error(f"Failed to notify owner about error: {e}")

async def create_prediction_poll(context: ContextTypes.DEFAULT_TYPE, group_id: int, match: Match):
    """Create and pin prediction poll"""
    try:
        poll_message = await context.bot.send_poll(
            chat_id=group_id,
            question="🎯 Who will win this match?",
            options=[
                f"🔵 {match.team_x.name}",
                f"🔴 {match.team_y.name}"
            ],
            is_anonymous=False,
            allows_multiple_answers=False
        )
        
        # Pin the poll
        try:
            await context.bot.pin_chat_message(
                chat_id=group_id,
                message_id=poll_message.message_id,
                disable_notification=True
            )
        except:
            pass  # If bot can't pin, continue anyway
            
    except Exception as e:
        logger.error(f"Error creating poll: {e}")

async def handle_group_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Batsman Input in Group (Deletes number to hide it)"""
    
    # Ignore Private chats, only Group
    if update.effective_chat.type == "private": return
    if not update.message or not update.message.text: return
    
    text = update.message.text.strip()
    if not text.isdigit(): return
    
    number = int(text)
    if number < 0 or number > 6: return # Ignore invalid numbers
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    
    if chat_id not in active_matches: return
    match = active_matches[chat_id]
    match.last_activity = time.time()
    
    if match.phase != GamePhase.MATCH_IN_PROGRESS: return

    # Identify Players
    batting_team = match.current_batting_team
    bowling_team = match.current_bowling_team
    
    # Check Indices (Safety Check)
    if batting_team.current_batsman_idx is None or bowling_team.current_bowler_idx is None:
        return

    striker = batting_team.players[batting_team.current_batsman_idx]
    bowler = bowling_team.players[bowling_team.current_bowler_idx]
    
    processed = False
    
    # 1. Check if Bowler sent number in Group (Backup, ideally should be DM)
    if user_id == bowler.user_id:
        if match.current_ball_data.get("bowler_number") is None:
            match.current_ball_data["bowler_number"] = number
            await context.bot.send_message(chat_id, f"⚾ <b>{bowler.first_name}</b> has bowled!", parse_mode=ParseMode.HTML)
            
            # Cancel timeout & Request Batsman
            if match.ball_timeout_task: match.ball_timeout_task.cancel()
            await request_batsman_number(context, chat_id, match)
            processed = True

    # 2. Check if Striker sent number
    elif user_id == striker.user_id:
        # Batsman can only play if bowler has bowled
        if match.current_ball_data.get("bowler_number") is not None:
            if match.current_ball_data.get("batsman_number") is None:
                match.current_ball_data["batsman_number"] = number
                await context.bot.send_message(chat_id, f"🏏 <b>{striker.first_name}</b> played a shot!", parse_mode=ParseMode.HTML)
                
                if match.ball_timeout_task: match.ball_timeout_task.cancel()
                await process_ball_result(context, chat_id, match)
                processed = True
    
    # Delete the number message (Requires Admin)
    if processed:
        try:
            await update.message.delete()
        except: 
            pass # Fail silently if no permissions

async def handle_dm_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle DM messages from players during match"""
    user = update.effective_user
    message = update.message
    
    if not message.text: return
    text = message.text.strip()
    
    # Check if it's a number
    if not text.isdigit(): return
    number = int(text)
    
    if number < 0 or number > 6:
        await message.reply_text("Please send a number between 0 and 6.")
        return
    
    # Find active match where this user is playing
    user_match = None
    user_group_id = None
    
    for group_id, match in active_matches.items():
        if match.phase == GamePhase.MATCH_IN_PROGRESS:
            batsman_idx = match.current_batting_team.current_batsman_idx
            bowler_idx = match.current_bowling_team.current_bowler_idx
            
            if batsman_idx is not None and bowler_idx is not None:
                batsman = match.current_batting_team.players[batsman_idx]
                bowler = match.current_bowling_team.players[bowler_idx]
                
                if user.id == batsman.user_id or user.id == bowler.user_id:
                    user_match = match
                    user_group_id = group_id
                    break
    
    if not user_match: return
    
    # Process the number
    await process_player_number(update, context, user_group_id, user_match, number)


# Main function
def main():
    """Start the bot"""
    # Load data on startup
    load_data()
    
    # Create application
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .read_timeout(60)  # Increased to 60s
        .write_timeout(60) # Increased to 60s
        .connect_timeout(60)
        .build()
    )
    
    # --- JOBS (Scheduled Tasks) ---
    if application.job_queue:
        # 1. Cleanup inactive matches every 60 seconds (Checks for 15 min inactivity)
        application.job_queue.run_repeating(cleanup_inactive_matches, interval=60, first=60)
        
        # 2. Auto Backup every 1 hour (3600 seconds)
        application.job_queue.run_repeating(auto_backup_job, interval=3600, first=10)
    
    # --- COMMAND HANDLERS ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("game", game_command))
    application.add_handler(CommandHandler("extend", extend_command))
    application.add_handler(CommandHandler("add", add_player_command))
    application.add_handler(CommandHandler("remove", remove_player_command))
    application.add_handler(CommandHandler("batting", batting_command))
    application.add_handler(CommandHandler("bowling", bowling_command))
    application.add_handler(CommandHandler("drs", drs_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("h2h", h2h_command))
    application.add_handler(CommandHandler("players", players_command)) # Players list
    application.add_handler(CommandHandler("timeout", timeout_command))
    application.add_handler(CommandHandler("huddle", huddle_command))
    application.add_handler(CommandHandler("taunt", taunt_command))
    application.add_handler(CommandHandler("celebrate", celebrate_command))
    application.add_handler(CommandHandler("cheer", cheer_command))
    application.add_handler(CommandHandler("scorecard", scorecard_command))
    application.add_handler(CommandHandler("endmatch", endmatch_command))

    
    # Owner/Admin commands
    application.add_handler(CommandHandler("broadcast", broadcast_command))
    application.add_handler(CommandHandler("botstats", botstats_command))
    application.add_handler(CommandHandler("backup", backup_command))
    application.add_handler(CommandHandler("restore", restore_command))
    application.add_handler(CommandHandler("resetmatch", resetmatch_command))

    
    # --- CALLBACK HANDLERS ---
    application.add_handler(CallbackQueryHandler(mode_selection_callback, pattern="^mode_"))
    application.add_handler(CallbackQueryHandler(team_join_callback, pattern="^(join_team_|leave_team)"))
    application.add_handler(CallbackQueryHandler(host_selection_callback, pattern="^become_host$"))
    application.add_handler(CallbackQueryHandler(captain_selection_callback, pattern="^captain_team_"))
    application.add_handler(CallbackQueryHandler(team_edit_done_callback, pattern="^team_edit_done$"))
    application.add_handler(CallbackQueryHandler(over_selection_callback, pattern="^overs_"))
    application.add_handler(CallbackQueryHandler(toss_callback, pattern="^toss_(heads|tails)$"))
    application.add_handler(CallbackQueryHandler(toss_decision_callback, pattern="^toss_decision_"))

    application.add_handler(CallbackQueryHandler(set_edit_team_callback, pattern="^(edit_team_|edit_back)"))

    # --- MESSAGE HANDLERS ---
    # NOTE: Yeh 'handle_group_input' use karega (Group mein number bhejne ke liye)
    # Agar purana DM wala chahiye toh isse hata kar 'handle_dm_message' laga lena
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, handle_dm_message))
    
    # 2. Group Chat Handler (Agar koi galti se group mein number likh de)
    application.add_handler(MessageHandler(filters.TEXT & filters.ChatType.GROUPS, handle_group_input))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start bot
    logger.info("Cricoverse bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()