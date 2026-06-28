"""
create_db.py
────────────
Run once to initialize quiz_app.db with:
  - users table
  - questions table (with sample questions for every category)
  - results table
  - scores table
  - user_badges table

Usage:
    python create_db.py
"""

import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash

DB = "quiz_app.db"

# ──────────────────────────────────────────────

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL UNIQUE,
    password   TEXT    NOT NULL,
    xp         INTEGER NOT NULL DEFAULT 0,
    is_admin   INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    category   TEXT    NOT NULL,
    difficulty TEXT    NOT NULL,
    question   TEXT    NOT NULL,
    option1    TEXT    NOT NULL,
    option2    TEXT    NOT NULL,
    option3    TEXT    NOT NULL,
    option4    TEXT    NOT NULL,
    answer     TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS results (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category   TEXT    NOT NULL,
    difficulty TEXT    NOT NULL,
    score      INTEGER NOT NULL DEFAULT 0,
    total      INTEGER NOT NULL DEFAULT 10,
    percentage INTEGER NOT NULL DEFAULT 0,
    played_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS scores (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category   TEXT    NOT NULL,
    difficulty TEXT    NOT NULL,
    score      INTEGER NOT NULL DEFAULT 0,
    total      INTEGER NOT NULL DEFAULT 10,
    accuracy   INTEGER NOT NULL DEFAULT 0,
    time_taken INTEGER NOT NULL DEFAULT 0,
    played_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS user_badges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id  TEXT    NOT NULL,
    earned_at TEXT    NOT NULL,
    UNIQUE(user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS idx_questions_cat_diff ON questions(category, difficulty);
CREATE INDEX IF NOT EXISTS idx_results_user       ON results(user_id);
CREATE INDEX IF NOT EXISTS idx_scores_user        ON scores(user_id);
CREATE INDEX IF NOT EXISTS idx_badges_user        ON user_badges(user_id);
"""

# SAMPLE QUESTIONS  (10 easy + 10 hard per category)

QUESTIONS = [
    # ─── GAMING ───
    ("gaming","easy","Which company created the Mario franchise?","Nintendo","Sega","Sony","Capcom","Nintendo"),
    ("gaming","easy","What is the best-selling video game of all time?","Minecraft","Tetris","GTA V","Wii Sports","Minecraft"),
    ("gaming","easy","In which game do you play as Master Chief?","Halo","Doom","Call of Duty","Battlefield","Halo"),
    ("gaming","easy","What color is Pac-Man?","Yellow","Red","Blue","Green","Yellow"),
    ("gaming","easy","Which game features the character Link?","The Legend of Zelda","Metroid","Kirby","F-Zero","The Legend of Zelda"),
    ("gaming","easy","What does 'HP' stand for in RPG games?","Hit Points","Hero Power","High Performance","Healing Potion","Hit Points"),
    ("gaming","easy","Which console introduced the analog stick?","Nintendo 64","PlayStation","Sega Saturn","Atari Jaguar","Nintendo 64"),
    ("gaming","easy","Who is Sonic's main rival?","Shadow","Knuckles","Tails","Eggman","Shadow"),
    ("gaming","easy","In chess-inspired video games, what piece can only move diagonally?","Bishop","Rook","Knight","Pawn","Bishop"),
    ("gaming","easy","What is the name of the island in 'Animal Crossing: New Horizons'?","Player-named island","Nook Island","Dodo Isle","Leaf Island","Player-named island"),
    ("gaming","hard","What is the highest possible score in the original Pac-Man arcade game?","3,333,360","9,999,999","1,000,000","2,500,000","3,333,360"),
    ("gaming","hard","Which game engine powers the Unreal Tournament series?","Unreal Engine","CryEngine","Source Engine","id Tech","Unreal Engine"),
    ("gaming","hard","In Street Fighter II, who is the final boss?","M. Bison","Sagat","Balrog","Vega","M. Bison"),
    ("gaming","hard","What year was the first Pokemon game released in Japan?","1996","1998","1995","2000","1996"),
    ("gaming","hard","Which legendary weapon in Minecraft requires 9 diamonds to craft?","Diamond Sword","Diamond Pickaxe","Diamond Armor","Diamond Axe","Diamond Pickaxe"),
    ("gaming","hard","What does the acronym 'NPC' stand for?","Non-Playable Character","New Player Character","Non-Primary Controller","Neutral Player Component","Non-Playable Character"),
    ("gaming","hard","Which game first introduced the 'Battle Royale' mode concept to mainstream gaming?","PlayerUnknown's Battlegrounds","Fortnite","Apex Legends","H1Z1","PlayerUnknown's Battlegrounds"),
    ("gaming","hard","In the original Doom, what is the name of the shotgun variant with a wider spread?","Super Shotgun","Combat Shotgun","Mega Shotgun","Blast Shotgun","Super Shotgun"),
    ("gaming","hard","Which company developed the Dark Souls series?","FromSoftware","Bandai Namco","Square Enix","Capcom","FromSoftware"),
    ("gaming","hard","In competitive CS:GO, how many rounds must a team win to claim a map?","16","15","20","13","16"),

    # ─── TECH ───
    ("tech","easy","What does CPU stand for?","Central Processing Unit","Computer Personal Unit","Core Processor Unit","Central Peripheral Unit","Central Processing Unit"),
    ("tech","easy","Which company makes the iPhone?","Apple","Samsung","Google","Microsoft","Apple"),
    ("tech","easy","What does HTML stand for?","HyperText Markup Language","High Transfer Markup Language","HyperText Management Language","Home Tool Markup Language","HyperText Markup Language"),
    ("tech","easy","What is the most popular search engine?","Google","Bing","Yahoo","DuckDuckGo","Google"),
    ("tech","easy","What does 'Wi-Fi' stand for?","Wireless Fidelity","Wide Fidelity","Wireless Internet","Wire Free","Wireless Fidelity"),
    ("tech","easy","Which programming language is known as the language of the web (frontend)?","JavaScript","Python","Java","Ruby","JavaScript"),
    ("tech","easy","What is the shortcut to copy text?","Ctrl+C","Ctrl+V","Ctrl+X","Ctrl+Z","Ctrl+C"),
    ("tech","easy","What does USB stand for?","Universal Serial Bus","Ultra Speed Boot","Unified System Base","Universal Storage Bus","Universal Serial Bus"),
    ("tech","easy","Which social media platform uses tweets?","Twitter/X","Instagram","Facebook","Snapchat","Twitter/X"),
    ("tech","easy","What does 'RAM' stand for?","Random Access Memory","Read Accessible Memory","Rapid Action Module","Random Allocation Memory","Random Access Memory"),
    ("tech","hard","What is the time complexity of binary search?","O(log n)","O(n)","O(n²)","O(1)","O(log n)"),
    ("tech","hard","Which protocol is used to securely transfer files over a network?","SFTP","FTP","HTTP","SMTP","SFTP"),
    ("tech","hard","In OSI model, which layer is responsible for routing?","Network Layer","Transport Layer","Data Link Layer","Session Layer","Network Layer"),
    ("tech","hard","What is the output of: 2 ** 10 in Python?","1024","512","2048","256","1024"),
    ("tech","hard","Which data structure uses LIFO (Last In First Out)?","Stack","Queue","Heap","Tree","Stack"),
    ("tech","hard","What is the default port for HTTPS?","443","80","8080","22","443"),
    ("tech","hard","In SQL, which command removes a table and its data permanently?","DROP TABLE","DELETE TABLE","REMOVE TABLE","TRUNCATE TABLE","DROP TABLE"),
    ("tech","hard","What does CORS stand for in web development?","Cross-Origin Resource Sharing","Cross-Object Request Sharing","Client-Origin Resource Service","Core Object Response System","Cross-Origin Resource Sharing"),
    ("tech","hard","Which hashing algorithm is considered the most secure for passwords?","bcrypt","MD5","SHA-1","SHA-256","bcrypt"),
    ("tech","hard","What does a 403 HTTP status code mean?","Forbidden","Not Found","Internal Server Error","Unauthorized","Forbidden"),

    # ─── RECORDS ───
    ("records","easy","Which is the tallest mountain in the world?","Mount Everest","K2","Mont Blanc","Kangchenjunga","Mount Everest"),
    ("records","easy","What is the largest ocean on Earth?","Pacific Ocean","Atlantic Ocean","Indian Ocean","Arctic Ocean","Pacific Ocean"),
    ("records","easy","Which is the longest river in the world?","Nile River","Amazon River","Yangtze River","Mississippi River","Nile River"),
    ("records","easy","What is the fastest land animal?","Cheetah","Lion","Leopard","Pronghorn","Cheetah"),
    ("records","easy","Which country has the most population?","India","China","USA","Indonesia","India"),
    ("records","easy","What is the smallest country in the world?","Vatican City","Monaco","San Marino","Liechtenstein","Vatican City"),
    ("records","easy","Which planet is the largest in our solar system?","Jupiter","Saturn","Neptune","Uranus","Jupiter"),
    ("records","easy","What is the deepest lake in the world?","Lake Baikal","Caspian Sea","Lake Tanganyika","Lake Superior","Lake Baikal"),
    ("records","easy","Which is the world's largest desert?","Sahara Desert","Arabian Desert","Gobi Desert","Antarctic Desert","Antarctic Desert"),
    ("records","easy","What is the hardest natural substance on Earth?","Diamond","Quartz","Topaz","Ruby","Diamond"),
    ("records","hard","What is the world record for the longest time without sleep?","11 days 25 minutes","7 days","14 days","9 days 12 hours","11 days 25 minutes"),
    ("records","hard","What is the deepest point in the ocean?","Mariana Trench","Puerto Rico Trench","Tonga Trench","Java Trench","Mariana Trench"),
    ("records","hard","Which country has won the most FIFA World Cups?","Brazil","Germany","Italy","Argentina","Brazil"),
    ("records","hard","What is the fastest commercial aircraft ever built?","Concorde","Boeing 747","Airbus A380","SR-71 Blackbird","Concorde"),
    ("records","hard","What is the world's most spoken language by native speakers?","Mandarin Chinese","English","Spanish","Hindi","Mandarin Chinese"),
    ("records","hard","What is the highest recorded temperature on Earth?","56.7°C (134°F)","58°C (136°F)","53°C (127°F)","60°C (140°F)","56.7°C (134°F)"),
    ("records","hard","Which building held the title of world's tallest for the longest time?","Empire State Building","Chrysler Building","Sears Tower","World Trade Center","Empire State Building"),
    ("records","hard","What is the largest living organism on Earth by area?","Armillaria ostoyae (honey fungus)","Blue Whale","Giant Sequoia","Whale Shark","Armillaria ostoyae (honey fungus)"),
    ("records","hard","Which country has the most natural lakes?","Canada","Russia","USA","Finland","Canada"),
    ("records","hard","What is the world record for the most push-ups in 24 hours?","46,001","30,000","55,000","38,500","46,001"),

    # ─── RIDDLES ───
    ("riddles","easy","I have hands but cannot clap. What am I?","A clock","A glove","A puppet","A statue","A clock"),
    ("riddles","easy","The more you take, the more you leave behind. What am I?","Footsteps","Water","Time","Breath","Footsteps"),
    ("riddles","easy","What has a neck but no head?","A bottle","A guitar","A shirt","A swan","A bottle"),
    ("riddles","easy","What comes once in a minute, twice in a moment, but never in a thousand years?","The letter M","The letter T","The letter I","The letter E","The letter M"),
    ("riddles","easy","I speak without a mouth and hear without ears. What am I?","An echo","A radio","A telephone","A mirror","An echo"),
    ("riddles","easy","What has keys but no locks, space but no room, and you can enter but can't go inside?","A keyboard","A map","A book","A piano","A keyboard"),
    ("riddles","easy","The more you have of it, the less you see. What is it?","Darkness","Light","Space","Air","Darkness"),
    ("riddles","easy","What gets wetter as it dries?","A towel","A sponge","Sand","Paper","A towel"),
    ("riddles","easy","I have cities, but no houses live there. I have mountains, but no trees grow. What am I?","A map","A painting","A photograph","A globe","A map"),
    ("riddles","easy","What can run but never walks, has a mouth but never talks?","A river","A clock","A snake","A train","A river"),
    ("riddles","hard","Forward I am heavy, but backward I am not. What am I?","Ton","Stone","Rock","Load","Ton"),
    ("riddles","hard","I am always in front of you but cannot be seen. What am I?","The future","A mirror","Your face","Your nose","The future"),
    ("riddles","hard","What has 13 hearts but no other organs?","A deck of cards","A rose bush","A hospital","A tree","A deck of cards"),
    ("riddles","hard","What can be broken without being held?","A promise","Glass","A bone","A record","A promise"),
    ("riddles","hard","I have branches but no fruit, trunk or leaves. What am I?","A bank","A tree stump","A river","A library","A bank"),
    ("riddles","hard","What disappears as soon as you say its name?","Silence","Your shadow","A secret","Wind","Silence"),
    ("riddles","hard","A man walks into a restaurant and orders albatross soup. After one sip, he goes home and kills himself. Why?","He realized he never had albatross soup before","He was poisoned","He found a hair in it","He was allergic","He realized he never had albatross soup before"),
    ("riddles","hard","The person who makes it, sells it. The person who buys it never uses it. The person who uses it doesn't know they're using it. What is it?","A coffin","A dream","A gift","A secret","A coffin"),
    ("riddles","hard","Two fathers and two sons go fishing. They catch three fish and each person gets one fish. How?","There are only 3 people: grandfather, father, son","One is a step-father","One is imaginary","One fish is shared","There are only 3 people: grandfather, father, son"),
    ("riddles","hard","What word in the English language is always spelled incorrectly?","Incorrectly","Wrong","Misspelled","Error","Incorrectly"),

    # ─── CODING ───
    ("coding","easy","What does 'print' do in Python?","Outputs text to console","Saves a file","Creates a variable","Draws on screen","Outputs text to console"),
    ("coding","easy","Which symbol is used for single-line comments in Python?","#","//","/*","--","#"),
    ("coding","easy","What does CSS stand for?","Cascading Style Sheets","Computer Style System","Creative Style Sheets","Cascading System Sheets","Cascading Style Sheets"),
    ("coding","easy","Which data type stores True or False?","Boolean","Integer","String","Float","Boolean"),
    ("coding","easy","What is the index of the first element in most programming languages?","0","1","-1","None","0"),
    ("coding","easy","Which HTML tag creates a hyperlink?","<a>","<link>","<href>","<url>","<a>"),
    ("coding","easy","What does the '==' operator check in most languages?","Equality","Assignment","Identity","Comparison","Equality"),
    ("coding","easy","Which keyword is used to define a function in Python?","def","function","func","define","def"),
    ("coding","easy","What does JSON stand for?","JavaScript Object Notation","Java Standard Object Notation","JavaScript Online Notation","Java Script Object Name","JavaScript Object Notation"),
    ("coding","easy","What is a 'loop' in programming?","Repeated execution of code","A type of variable","A data structure","An error type","Repeated execution of code"),
    ("coding","hard","What is the output of: print(type([])) in Python?","<class 'list'>","<class 'array'>","<type 'list'>","list","<class 'list'>"),
    ("coding","hard","Which sorting algorithm has the best average-case time complexity?","Merge Sort O(n log n)","Bubble Sort O(n²)","Insertion Sort O(n²)","Selection Sort O(n²)","Merge Sort O(n log n)"),
    ("coding","hard","What does the 'async' keyword do in JavaScript?","Makes a function return a Promise","Makes code run faster","Creates a new thread","Pauses execution","Makes a function return a Promise"),
    ("coding","hard","In Python, what is a decorator?","A function that wraps another function","A design pattern","A class method","A type annotation","A function that wraps another function"),
    ("coding","hard","What is a 'closure' in programming?","A function with access to its outer scope","A sealed class","A completed loop","An exception handler","A function with access to its outer scope"),
    ("coding","hard","What does the 'virtual' keyword mean in C++?","Enables polymorphism via method overriding","Makes a variable constant","Allocates memory","Creates a pointer","Enables polymorphism via method overriding"),
    ("coding","hard","What is Big O notation used for?","Describing algorithm time/space complexity","Measuring code size","Counting variables","Defining class hierarchy","Describing algorithm time/space complexity"),
    ("coding","hard","What is the difference between '==' and '===' in JavaScript?","=== also checks type","=== is assignment","== is stricter","There is no difference","=== also checks type"),
    ("coding","hard","What is a race condition in programming?","When two threads access shared data simultaneously","When code runs too fast","When a loop doesn't end","When variables conflict","When two threads access shared data simultaneously"),
    ("coding","hard","What does SOLID stand for in software engineering?","5 OOP design principles","A database type","A security protocol","A testing framework","5 OOP design principles"),

    # ─── SPACE ───
    ("space","easy","How many planets are in our solar system?","8","9","7","10","8"),
    ("space","easy","What is the closest star to Earth?","The Sun","Proxima Centauri","Alpha Centauri A","Sirius","The Sun"),
    ("space","easy","What is the largest planet in our solar system?","Jupiter","Saturn","Neptune","Uranus","Jupiter"),
    ("space","easy","What planet is known as the Red Planet?","Mars","Venus","Jupiter","Saturn","Mars"),
    ("space","easy","How long does it take light to travel from the Sun to Earth?","8 minutes","1 minute","1 hour","24 hours","8 minutes"),
    ("space","easy","What is a group of stars called?","A galaxy","A nebula","A cluster","A constellation","A constellation"),
    ("space","easy","Who was the first human to walk on the moon?","Neil Armstrong","Buzz Aldrin","Yuri Gagarin","Alan Shepard","Neil Armstrong"),
    ("space","easy","What is the name of NASA's most famous space telescope?","Hubble","Kepler","James Webb","Chandra","Hubble"),
    ("space","easy","What force keeps planets orbiting the Sun?","Gravity","Magnetism","Nuclear force","Dark energy","Gravity"),
    ("space","easy","What is a shooting star actually made of?","A meteoroid burning in atmosphere","A comet","A falling satellite","An asteroid","A meteoroid burning in atmosphere"),
    ("space","hard","What is the Schwarzschild radius?","The radius at which an object becomes a black hole","The distance from Earth to the Sun","The radius of the Milky Way","The distance light travels in 1 second","The radius at which an object becomes a black hole"),
    ("space","hard","What is the name of the process by which stars generate energy?","Nuclear fusion","Nuclear fission","Combustion","Gravitational collapse","Nuclear fusion"),
    ("space","hard","How many moons does Saturn have (as of 2024)?","146","82","27","63","146"),
    ("space","hard","What is the Fermi Paradox?","Contradiction between lack of alien evidence and probability of life","A formula for star formation","The theory of parallel universes","A model for galaxy rotation","Contradiction between lack of alien evidence and probability of life"),
    ("space","hard","What is the cosmic microwave background radiation?","Afterglow light from the Big Bang","Radiation from black holes","Light from distant galaxies","Solar wind particles","Afterglow light from the Big Bang"),
    ("space","hard","How far is one light-year in kilometers?","9.461 trillion km","1 billion km","4.24 light-years","150 million km","9.461 trillion km"),
    ("space","hard","What is the Great Attractor?","A gravitational anomaly pulling our galaxy","A massive black hole","The center of the universe","A collapsed star","A gravitational anomaly pulling our galaxy"),
    ("space","hard","What is the Chandrasekhar limit?","Maximum mass of a white dwarf (~1.4 solar masses)","Minimum mass of a neutron star","Speed limit of particles near black holes","Maximum temperature of a star","Maximum mass of a white dwarf (~1.4 solar masses)"),
    ("space","hard","What type of galaxy is the Milky Way?","Barred spiral galaxy","Elliptical galaxy","Irregular galaxy","Lenticular galaxy","Barred spiral galaxy"),
    ("space","hard","What is the Oort Cloud?","A distant spherical cloud of icy objects","A storm on Neptune","A nebula near Earth","The asteroid belt","A distant spherical cloud of icy objects"),

    # ─── SCIENCE ───
    ("science","easy","What is the chemical formula for water?","H2O","HO2","H2O2","OH2","H2O"),
    ("science","easy","What is the powerhouse of the cell?","Mitochondria","Nucleus","Ribosome","Golgi body","Mitochondria"),
    ("science","easy","What planet is known as the morning star?","Venus","Mars","Mercury","Jupiter","Venus"),
    ("science","easy","What gas do plants absorb from the air?","Carbon dioxide","Oxygen","Nitrogen","Hydrogen","Carbon dioxide"),
    ("science","easy","How many bones are in the adult human body?","206","208","196","212","206"),
    ("science","easy","What is the speed of light?","299,792,458 m/s","300,000 km/h","186,000 mph","150,000 km/s","299,792,458 m/s"),
    ("science","easy","What is the most abundant gas in Earth's atmosphere?","Nitrogen","Oxygen","Carbon dioxide","Argon","Nitrogen"),
    ("science","easy","What organ pumps blood through the human body?","Heart","Lungs","Liver","Kidney","Heart"),
    ("science","easy","What is the chemical symbol for gold?","Au","Go","Gd","Ag","Au"),
    ("science","easy","What is the process of plants making food from sunlight called?","Photosynthesis","Respiration","Osmosis","Fermentation","Photosynthesis"),
    ("science","hard","What is the half-life of Carbon-14?","5,730 years","1,000 years","10,000 years","50,000 years","5,730 years"),
    ("science","hard","What is the uncertainty principle in quantum mechanics?","You can't know both position and momentum precisely","Light behaves as both wave and particle","Particles can be in two places at once","Energy is quantized","You can't know both position and momentum precisely"),
    ("science","hard","What is the pH of a neutral solution at 25°C?","7","6","8","5","7"),
    ("science","hard","Which element has the highest electronegativity?","Fluorine","Oxygen","Nitrogen","Chlorine","Fluorine"),
    ("science","hard","What is the Krebs cycle?","A series of reactions for cellular energy production","A type of cell division","A protein synthesis process","A DNA replication cycle","A series of reactions for cellular energy production"),
    ("science","hard","What type of bond holds water molecules together?","Hydrogen bond","Covalent bond","Ionic bond","Metallic bond","Hydrogen bond"),
    ("science","hard","What is the name of the protein that carries oxygen in blood?","Hemoglobin","Albumin","Fibrin","Keratin","Hemoglobin"),
    ("science","hard","What is Avogadro's number?","6.022 × 10²³","6.022 × 10²⁴","3.14 × 10²³","1.38 × 10²³","6.022 × 10²³"),
    ("science","hard","What is the second law of thermodynamics about?","Entropy always increases in a closed system","Energy cannot be created or destroyed","Objects in motion stay in motion","Force equals mass times acceleration","Entropy always increases in a closed system"),
    ("science","hard","What is CRISPR-Cas9?","A gene editing tool","A type of virus","A protein synthesis method","A DNA sequencing technique","A gene editing tool"),
]


def create_database():
    if os.path.exists(DB):
        print(f"[!] {DB} already exists. Deleting and recreating...")
        os.remove(DB)

    conn = sqlite3.connect(DB)
    conn.executescript(SCHEMA)

    # Insert questions
    conn.executemany("""
        INSERT INTO questions
            (category, difficulty, question, option1, option2, option3, option4, answer)
        VALUES (?,?,?,?,?,?,?,?)
    """, QUESTIONS)

    # Insert demo admin user
    conn.execute("""
        INSERT INTO users (username, password, xp, is_admin, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        "admin",
        generate_password_hash("admin123"),
        500,
        1,
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    total = len(QUESTIONS)
    print(f"✅ {DB} created successfully!")
    print(f"   → {total} questions inserted ({total//2} easy, {total//2} hard across 7 categories)")
    print(f"   → Admin user created: username=admin  password=admin123")
    print(f"   → Change the admin password after first login!")


if __name__ == "__main__":
    create_database()