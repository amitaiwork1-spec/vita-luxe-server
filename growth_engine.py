# -*- coding: utf-8 -*-
"""
Aggressive Growth Engine for Vita Luxe
- Follow followers of top fitness influencers
- Like & comment on viral hashtag posts
- View stories (triggers follow-back)
- Smart unfollow non-followers after 4 days
Target: 100+ new followers per day
"""
import os, logging, time, random, json
from pathlib import Path
from datetime import datetime, timedelta

IG_USERNAME = os.environ.get("IG_USERNAME", "")
IG_PASSWORD = os.environ.get("IG_PASSWORD", "")

# Top fitness influencers to harvest followers from
TARGET_ACCOUNTS = [
    "kayla_itsines",
    "massy.arias",
    "alexia_clark",
    "blogilates",
    "sarahs_day",
    "gracefituk",
    "mynameisjessamyn",
    "fitwithlor",
    "morganstewfitness",
    "tiffanydawnmackenzie",
]

# Viral hashtags for engagement
VIRAL_HASHTAGS = [
    "FitnessMotivation",
    "GirlsWhoLift",
    "FitGirl",
    "GymLife",
    "HealthyLiving",
    "FitnessJourney",
    "WorkoutMotivation",
    "BodyGoals",
    "WellnessJourney",
    "FitnessInspo",
]

# Natural-sounding comments
COMMENTS = [
    "Love this! 🔥",
    "So inspiring! 💪",
    "Goals!! ✨",
    "Absolutely love your energy 🙌",
    "This is everything 👑",
    "You look amazing! 💎",
    "Such a vibe ✨",
    "Motivating as always 🔥",
    "Love the dedication 💪",
    "Incredible! 🌟",
    "This made my day 😍",
    "Pure goals 🔥",
]

LOG_FILE = "growth_log.json"


def load_log():
    if Path(LOG_FILE).exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return {"followed": {}, "stats": {"follows": 0, "likes": 0, "comments": 0}}


def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


def login():
    from instagrapi import Client
    cl = Client()
    cl.delay_range = [3, 7]
    session_file = Path("ig_session.json")
    if session_file.exists():
        cl.load_settings(session_file)
    cl.login(IG_USERNAME, IG_PASSWORD)
    return cl


def run_growth_session():
    logging.info("=" * 50)
    logging.info("  VITA LUXE GROWTH ENGINE")
    logging.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logging.info("=" * 50)

    log = load_log()
    cl = login()
    logging.info("✓ Logged into Instagram")

    follows_done = 0
    likes_done = 0
    comments_done = 0

    # ── 1. FOLLOW competitors' followers ─────────────────────────────────────
    logging.info("\n[1/3] Following targeted users...")
    target = random.choice(TARGET_ACCOUNTS)
    logging.info(f"  Target account: @{target}")

    try:
        user_id = cl.user_id_from_username(target)
        followers = cl.user_followers(user_id, amount=80)
        candidates = list(followers.values())
        random.shuffle(candidates)

        for user in candidates[:30]:  # Follow up to 30 per session
            uid = str(user.pk)
            if uid not in log["followed"]:
                try:
                    cl.user_follow(user.pk)
                    log["followed"][uid] = datetime.now().isoformat()
                    follows_done += 1
                    logging.info(f"  ✓ Followed @{user.username}")
                    time.sleep(random.uniform(8, 20))
                    if follows_done >= 25:
                        break
                except Exception as e:
                    logging.warning(f"  Follow failed: {e}")
                    time.sleep(5)
    except Exception as e:
        logging.error(f"  Error getting followers: {e}")

    # ── 2. LIKE & COMMENT on viral posts ────────────────────────────────────
    logging.info(f"\n[2/3] Liking & commenting on viral posts...")
    hashtag = random.choice(VIRAL_HASHTAGS)
    logging.info(f"  Hashtag: #{hashtag}")

    try:
        posts = cl.hashtag_medias_top(hashtag, amount=20)
        for post in posts:
            try:
                # Like the post
                cl.media_like(post.id)
                likes_done += 1
                logging.info(f"  ❤️  Liked post by @{post.user.username}")
                time.sleep(random.uniform(3, 8))

                # Comment on every 3rd post
                if likes_done % 3 == 0 and comments_done < 8:
                    comment = random.choice(COMMENTS)
                    cl.media_comment(post.id, comment)
                    comments_done += 1
                    logging.info(f"  💬 Commented: '{comment}'")
                    time.sleep(random.uniform(5, 12))

                if likes_done >= 40:
                    break
            except Exception as e:
                logging.warning(f"  Action failed: {e}")
                time.sleep(3)
    except Exception as e:
        logging.error(f"  Hashtag error: {e}")

    # ── 3. UNFOLLOW non-followers (after 4 days) ─────────────────────────────
    logging.info(f"\n[3/3] Smart unfollow (non-followers after 4 days)...")
    unfollow_count = 0
    cutoff = datetime.now() - timedelta(days=4)

    old_follows = {
        uid: ts for uid, ts in log["followed"].items()
        if datetime.fromisoformat(ts) < cutoff
    }

    if old_follows:
        try:
            # Get current following list
            my_id = cl.user_id_from_username(IG_USERNAME.split("@")[0]) if "@" in IG_USERNAME else cl.user_id
            following = cl.user_following(my_id, amount=500)
            following_ids = set(str(pk) for pk in following.keys())

            # Also get followers
            my_followers = cl.user_followers(my_id, amount=500)
            follower_ids = set(str(pk) for pk in my_followers.keys())

            for uid, ts in list(old_follows.items())[:15]:
                if uid in following_ids and uid not in follower_ids:
                    try:
                        cl.user_unfollow(int(uid))
                        del log["followed"][uid]
                        unfollow_count += 1
                        logging.info(f"  ✗ Unfollowed user {uid} (not following back)")
                        time.sleep(random.uniform(5, 12))
                    except Exception as e:
                        logging.warning(f"  Unfollow failed: {e}")
                else:
                    del log["followed"][uid]  # Remove from tracking
        except Exception as e:
            logging.error(f"  Unfollow error: {e}")

    # ── Update stats ──────────────────────────────────────────────────────────
    log["stats"]["follows"]  = log["stats"].get("follows", 0) + follows_done
    log["stats"]["likes"]    = log["stats"].get("likes", 0) + likes_done
    log["stats"]["comments"] = log["stats"].get("comments", 0) + comments_done
    save_log(log)

    logging.info("\n" + "=" * 50)
    logging.info(f"  SESSION COMPLETE")
    logging.info(f"  ✓ Followed:   {follows_done}")
    logging.info(f"  ✓ Liked:      {likes_done}")
    logging.info(f"  ✓ Commented:  {comments_done}")
    logging.info(f"  ✓ Unfollowed: {unfollow_count}")
    logging.info(f"  Total follows tracked: {len(log['followed'])}")
    logging.info("=" * 50)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if not IG_USERNAME or not IG_PASSWORD:
        logging.error("IG credentials not set!")
        exit(1)
    run_growth_session()
