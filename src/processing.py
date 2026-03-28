import os
import json
import datetime
from pathlib import Path

import pandas as pd


def parse_run(run):
    runtime = datetime.datetime.fromtimestamp(run["start_time"]).strftime("%Y-%m-%d")

    character = run["players"][0]["character"].split(".")[-1]
    ascension = run["ascension"]
    won = run["win"]

    kben = run["killed_by_encounter"] if run["killed_by_encounter"] != "NONE.NONE" else None
    kbev = run["killed_by_event"] if run["killed_by_event"] != "NONE.NONE" else None

    killed_by = kbev if not kben else kben
    if killed_by:
        killed_by = killed_by.split(".")[-1]

    map_history = run["map_point_history"]
    full_map_history = [x for y in map_history for x in y]

    act_1_damage = sum([x["player_stats"][0]["damage_taken"] for x in map_history[0]])
    act_2_damage = sum([x["player_stats"][0]["damage_taken"] for x in map_history[1]]) if len(map_history) > 1 else 0
    act_3_damage = sum([x["player_stats"][0]["damage_taken"] for x in map_history[2]]) if len(map_history) > 2 else 0

    died_on_floor = len(full_map_history) if killed_by else -1

    damage_taken = sum([x["player_stats"][0]["damage_taken"] for x in full_map_history])
    gold_gained = sum([x["player_stats"][0]["gold_gained"] for x in full_map_history])

    total_floors = len(full_map_history)
    damage_per_floor = round(damage_taken / total_floors, 2)

    deadly_room = sorted(full_map_history, key=lambda room: room["player_stats"][0]["damage_taken"], reverse=True)[0]
    deadly_room_name = deadly_room["rooms"][0]["model_id"].split(".")[-1]
    deadly_room_damage = deadly_room["player_stats"][0]["damage_taken"]
    deadly_room_floor = full_map_history.index(deadly_room) + 1

    bosses = [act[-1]["rooms"][0]["model_id"].split(".")[-1] if act[-1]["map_point_type"] == "boss" else "" for act in map_history]
    bosses += [""] * (3 - len(bosses))
    boss_str = ", ".join(["_".join(boss.split("_")[:-1]) for boss in bosses if boss])

    ancients = [act[0]["rooms"][0]["model_id"].split(".")[-1] for act in map_history]
    ancients_str = ", ".join(ancients)

    return {
        "Date": runtime,
        "Character": character,
        "Ascension": ascension,
        "Gold Gained": gold_gained,
        "Damage Taken": damage_taken,
        "Damage per floor": damage_per_floor,
        "Won": won,
        "Killed By": killed_by,
        "Died on floor": died_on_floor,
        "Act 1 Damage": act_1_damage,
        "Act 2 Damage": act_2_damage,
        "Act 3 Damage": act_3_damage,
        "Deadliest Floor": deadly_room_floor,
        "Deadliest Floor Encounter": deadly_room_name,
        "Deadliest Floor Damage": deadly_room_damage,
        "Bosses": boss_str,
        "Ancients": ancients_str,
    }


def get_card_stats(runs, card_dict):
    base_dict = {
        "Times offered": 0,
        "Times picked": 0,
        "Winning runs picked": 0,
        "Losing runs picked": 0,
        "Times offered - card reward": 0,
        "Times offered - shop": 0,
        "Times offered - other": 0,
        "Times picked - card reward": 0,
        "Times picked - shop": 0,
        "Times picked - other": 0,
        "Times offered - Act 1": 0,
        "Times picked - Act 1": 0,
        "Times offered - upgraded": 0,
        "Times transformed into": 0,
        "Times upgraded": 0,
        "Times enchanted": 0,
    }
    seen = {k: base_dict.copy() for k in card_dict.keys()}

    for run in runs:
        win = run["win"]
        floors = [x for y in run["map_point_history"] for x in y]

        for floor in floors:
            try:
                room, ps = floor["rooms"][0], floor["player_stats"][0]
                ps = floor["player_stats"][0]

                if floor["rooms"][0]["room_type"] == "shop":
                    cards_picked = []
                    for card in ps["card_choices"]:
                        name, upgrade, pick = card["card"]["id"], card["card"].get("current_upgrade_level", 1), card["was_picked"]
                        sd = seen[name]

                        if pick:
                            cards_picked.append(name)

                        sd["Times offered"] += 1
                        if pick:
                            sd["Times picked"] += 1
                            if win:
                                sd["Winning runs picked"] += 1
                            else:
                                sd["Losing runs picked"] += 1

                        sd["Times offered - shop"] += 1
                        if pick:
                            sd["Times picked - shop"] += 1

                    for card in ps.get("cards_gained", []):
                        name, upgrade, pick = card["id"], card.get("current_upgrade_level", 1), True
                        sd = seen[name]

                        sd["Times offered"] += 1
                        sd["Times picked"] += 1

                        if win:
                            sd["Winning runs picked"] += 1
                        else:
                            sd["Losing runs picked"] += 1

                        sd["Times offered - shop"] += 1
                        sd["Times picked - shop"] += 1

                elif floor["rooms"][0]["room_type"] in ["monster", "elite", "boss"]:
                    if "card_choices" in ps.keys():
                        for card in ps["card_choices"]:
                            name, upgrade, pick = card["card"]["id"], card["card"].get("current_upgrade_level", 1), card["was_picked"]
                            sd = seen[name]

                            sd["Times offered"] += 1
                            if pick:
                                sd["Times picked"] += 1
                                if win:
                                    sd["Winning runs picked"] += 1
                                else:
                                    sd["Losing runs picked"] += 1

                            sd["Times offered - card reward"] += 1
                            if pick:
                                sd["Times picked - card reward"] += 1

                elif floor["rooms"][0]["room_type"] in ["event", "rest_site", "treasure"]:
                    pass

                else:
                    raise ValueError(f"Unhandled room type '{floor['rooms'][0]['room_type']}'")
            except Exception as e:
                print("Floor:::")
                print(floor)
                raise e

    return seen


def process_run_history(history_path, cards_json_path, status_callback=None):
    """
    Process Slay the Spire 2 run history and card choice data.

    Returns (run_history_df, card_choice_df).
    """
    def status(msg):
        if status_callback:
            status_callback(msg)

    # Load run files
    status(f"Loading run files from {history_path}...")
    if not history_path.exists():
        raise FileNotFoundError(f"History directory not found: {history_path}")

    all_files = []
    for p in os.listdir(history_path):
        with open(history_path / p, "r") as file:
            all_files.append(json.loads(file.read()))

    single_player_files = [x for x in all_files if len(x["players"]) == 1]
    status(f"Found {len(single_player_files)} single-player runs (of {len(all_files)} total).")

    if not single_player_files:
        raise ValueError("No single-player run files found.")

    # Load card data
    status("Loading card data...")
    with open(cards_json_path, "r") as file:
        card_data = json.loads(file.read())

    card_dict = {"CARD." + c["id"]: c for c in card_data}

    # Process run history
    status("Processing run history...")
    run_history_df = pd.DataFrame([parse_run(x) for x in single_player_files]).sort_values("Date")

    # Process card choices
    status("Processing card choices...")
    card_choice_df = pd.DataFrame(get_card_stats(single_player_files, card_dict)).T

    card_choice_df["pick_rate"] = (card_choice_df["Times picked"] / card_choice_df["Times offered"]).fillna(0).round(2)
    card_choice_df["name"] = card_choice_df.index.map(lambda card: card_dict[card]["name"])
    card_choice_df["rarity"] = card_choice_df.index.map(lambda card: card_dict[card]["rarity"])
    card_choice_df["type"] = card_choice_df.index.map(lambda card: card_dict[card]["type"])
    card_choice_df["class"] = card_choice_df.index.map(lambda card: card_dict[card]["color"])

    final_column_order = [
        'name', 'class', 'rarity', 'type',
        'Times offered', 'Times picked', 'pick_rate',
        'Winning runs picked', 'Losing runs picked',
        'Times offered - card reward', 'Times picked - card reward',
        'Times offered - shop', 'Times picked - shop',
    ]
    card_choice_df = card_choice_df[final_column_order]

    status("Done!")
    return run_history_df, card_choice_df
