import streamlit as st
import uuid
import json
import sqlite3
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Qdrant set up
q_client = QdrantClient(
    url="placeholder", 
    api_key="placeholder"
)

# Load a lightweight embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Qdrant Functions
def stringify_profile(profile: dict) -> str:
    parts = [
        f"My name is {profile.get('name')}, I'm {profile.get('age')} years old from {profile.get('location')}.",
        f"I'm a {profile.get('social_energy')} and enjoy {profile.get('hobbies')}.",
        f"I prefer {'group activities' if 'group' in profile.get('conversation_preference', '').lower() else 'deep 1-on-1 conversations'}.",
        f"My love languages in friendship are: {', '.join(profile.get('love_languages', []))}.",
        f"When someone cancels plans last minute, I feel: {profile.get('cancellation_reaction')}.",
        f"To recharge, I usually: {profile.get('recharge_style')}.",
        f"A personal habit I'm proud of is: {profile.get('trait')}.",
    ]
    return " ".join(parts)


# SQLite setup
conn = sqlite3.connect("profiles.db")
cursor = conn.cursor()

# Create table with new fields
cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    age TEXT,
    location TEXT,
    social_energy TEXT,
    hobbies TEXT,
    conversation_preference TEXT,
    communication_frequency TEXT,
    friendship_love_language TEXT,
    personality_season TEXT,
    proud_trait TEXT,
    recharge_style TEXT,
    reaction_to_cancellation TEXT
)
""")
conn.commit()

# Streamlit setup
st.set_page_config(page_title="Friend Group Matcher")

if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

questions = [
    "What's your name?",
    "How old are you?",
    "Where are you located?",
    "Which best describes your social energy? (introvert, ambivert, extrovert)",
    "List a few hobbies you enjoy.",
    "Do you prefer deep one-on-one conversations or group activities?",
    "How often do you like to text or check in with friends?",
    "What’s your love language when it comes to friendships?",
    "If your personality were a season, which one would it be and why?",
    "What’s a personal habit or trait you’re proud of?",
    "How do you usually recharge — alone or with others?",
    "When someone cancels plans last minute, how do you feel?"
]

if "profile" not in st.session_state:
    st.session_state.profile = {}
if "step" not in st.session_state:
    st.session_state.step = 0

# UI
st.title("🧑‍🤝‍🧑 Friend Matcher Bot")
st.write(f"**Your User ID**: {st.session_state.user_id}")

if st.session_state.step < len(questions):
    question = questions[st.session_state.step]
    st.write(f"**Bot:** {question}")

    with st.form(key=f"form_{st.session_state.step}"):
        # Customized input types
        if "social energy" in question:
            answer = st.selectbox("Choose one:", ["introvert", "ambivert", "extrovert"])
        elif "deep one-on-one conversations" in question:
            answer = st.selectbox("Choose one:", ["deep one-on-one conversations", "group activities"])
        elif "love language" in question:
            love_languages = [
                "Words of Affirmation",
                "Acts of Service",
                "Receiving Gifts",
                "Quality Time",
                "Physical Touch"
            ]
            selected = []
            for lang in love_languages:
                if st.checkbox(lang, key=lang):
                    selected.append(lang)
            answer = ", ".join(selected)
        else:
            answer = st.text_input("Your answer")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.profile[question] = answer
            st.session_state.step += 1
            st.rerun()
else:
    st.success("Thanks! Here's your profile:")

    profile_with_id = {"user_id": st.session_state.user_id, **st.session_state.profile}
    with open(f"profile_{st.session_state.user_id}.json", "w") as f:
        json.dump(profile_with_id, f, indent=2)

    # Save to SQLite
    cursor.execute("SELECT 1 FROM profiles WHERE user_id = ?", (st.session_state.user_id,))
    if cursor.fetchone() is None:
        # Insert new profile if it doesn't exist
        cursor.execute("""
            INSERT INTO profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            st.session_state.user_id,
            st.session_state.profile.get("What's your name?"),
            st.session_state.profile.get("How old are you?"),
            st.session_state.profile.get("Where are you located?"),
            st.session_state.profile.get("Which best describes your social energy? (introvert, ambivert, extrovert)"),
            st.session_state.profile.get("List a few hobbies you enjoy."),
            st.session_state.profile.get("Do you prefer deep one-on-one conversations or group activities?"),
            st.session_state.profile.get("How often do you like to text or check in with friends?"),
            st.session_state.profile.get("What’s your love language when it comes to friendships?"),
            st.session_state.profile.get("If your personality were a season, which one would it be and why?"),
            st.session_state.profile.get("What’s a personal habit or trait you’re proud of?"),
            st.session_state.profile.get("How do you usually recharge — alone or with others?"),
            st.session_state.profile.get("When someone cancels plans last minute, how do you feel?")
        ))
        conn.commit()
        st.info("Your profile has been saved to the local database.")
    else:
        # Show warning if the profile already exists
        st.warning("This user profile already exists in the database.")

    # Step 1: Turn profile into string
    profile_dict = {
        "name": profile_with_id.get("What's your name?"),
        "age": profile_with_id.get("How old are you?"),
        "location": profile_with_id.get("Where are you located?"),
        "social_energy": profile_with_id.get("Which best describes your social energy? (introvert, ambivert, extrovert)"),
        "hobbies": profile_with_id.get("List a few hobbies you enjoy."),
        "conversation_preference": profile_with_id.get("Do you prefer deep one-on-one conversations or group activities?"),
        "communication_frequency": profile_with_id.get("How often do you like to text or check in with friends?"),
        "love_languages": [s.strip() for s in profile_with_id.get("What’s your love language when it comes to friendships?", "").split(",")],
        "personality_season": profile_with_id.get("If your personality were a season, which one would it be and why?"),
        "trait": profile_with_id.get("What’s a personal habit or trait you’re proud of?"),
        "recharge_style": profile_with_id.get("How do you usually recharge — alone or with others?"),
        "cancellation_reaction": profile_with_id.get("When someone cancels plans last minute, how do you feel?")
    }

    text_profile = stringify_profile(profile_dict)

    # Step 2: Generate vector
    vector = model.encode(text_profile).tolist()

    # Step 3: Upload to Qdrant
    q_client.upsert(
        collection_name="friend_profiles",
        points=[{
            "id": st.session_state.user_id,
            "vector": vector,
            "payload": profile_dict
        }]
    )

    # Step 4: Search for similar friends (exclude self)
    hits = q_client.search(
        collection_name="friend_profiles",
        query_vector=vector,
        limit=3,
        with_payload=True,
        score_threshold=0.7
    )

    st.subheader("Top Friend Matches:")
    for hit in hits:
        if hit.id != st.session_state.user_id:
            match = hit.payload
            st.write(f"👤 {match['name']} — {match['social_energy']}, enjoys {match['hobbies']}")
            st.write(f"📬 Similarity Score: {round(hit.score, 2)}")
            st.write("---")

    st.json(profile_with_id)
    conn.close()  # Closing the database connection
