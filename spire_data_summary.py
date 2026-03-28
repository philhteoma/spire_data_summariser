import os
import json

from pathlib import Path
import datetime

import pandas as pd

SAVES_PATH   = Path("/home/ray/.local/share/SlayTheSpire2/steam/76561197996993222/profile1/saves")
REPLAYS_PATH = Path("/home/ray/.local/share/SlayTheSpire2/steam/76561197996993222/profile1/replays")
HISTORY_PATH = Path("/home/ray/.local/share/SlayTheSpire2/steam/76561197996993222/profile1/saves/history")

all_files = []
for p in os.listdir(HISTORY_PATH):
  with open(HISTORY_PATH.joinpath(p), "r") as file:
    f = json.loads(file.read())
  all_files.append(f)

single_player_files = [x for x in all_files if len(x["players"]) == 1]


card_data = dict()
with open("data/cards/cards.json", "r") as file:
  card_data = json.loads(file.read())

# Get summaries of all invididual runs
def parse_run(run):
  runtime = datetime.datetime.fromtimestamp(run["start_time"]).strftime("%Y-%m-%d")
  
  character = run["players"][0]["character"].split(".")[-1]
  ascension = run["ascension"]
  won = run["win"]

  kben = run["killed_by_encounter"] if run["killed_by_encounter"]!= "NONE.NONE" else None 
  kbev = run["killed_by_event"] if run["killed_by_event"]!= "NONE.NONE" else None 

  killed_by = kbev if not kben else kben
  if killed_by: killed_by = killed_by.split(".")[-1]

  map_history = run["map_point_history"]
  full_map_history = [x for y in map_history for x in y] # unnest
  # print(map_history[0])
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
  bosses += [""] * (3 - len(bosses)) # Padding for runs that do not reach act 2 or 3
  boss_str = ", ".join(["_".join(boss.split("_")[:-1]) for boss in bosses if boss])
  # boss_one, boss_two, boss_three = bosses

  ancients = [act[0]["rooms"][0]["model_id"].split(".")[-1] for act in map_history]
  ancients_str = ", ".join(ancients)

  return {
    "Date" : runtime,
    "Character" : character,
    "Ascension" : ascension,
    "Gold Gained" : gold_gained,
    "Damage Taken" : damage_taken,
    "Damage per floor" : damage_per_floor,
    "Won" : won,
    "Killed By" : killed_by,
    "Died on floor" : died_on_floor,
    "Act 1 Damage" : act_1_damage,
    "Act 2 Damage" : act_2_damage,
    "Act 3 Damage" : act_3_damage,
    "Deadliest Floor" : deadly_room_floor,
    "Deadliest Floor Encounter" : deadly_room_name,
    "Deadliest Floor Damage" : deadly_room_damage,
    "Bosses" : boss_str,
    "Ancients" : ancients_str,
  }

run_history_df = pd.DataFrame([parse_run(x) for x in single_player_files]).sort_values("Date")
run_history_df.to_csv("run_history_standalone.csv")


# Get summaries of card offerings and pick rates
base_dict = {
  "Times offered" : 0,
  "Times picked" : 0,

  "Winning runs picked" : 0,
  "Losing runs picked" : 0,

  "Times offered - card reward" : 0,
  "Times offered - shop" : 0,
  "Times offered - other" : 0,

  "Times picked - card reward" : 0,
  "Times picked - shop" : 0,
  "Times picked - other" : 0,

  "Times offered - Act 1" : 0,
  "Times picked - Act 1" : 0,

  "Times offered - upgraded" : 0,

  "Times transformed into" : 0,

  "Times upgraded" : 0,
  "Times enchanted" : 0,
  }

card_dict = { "CARD." + c["id"] : c for c in card_data }
base_card_dict = { k : base_dict.copy() for k in card_dict.keys() }

def get_card_stats(runs):
  # cards_seen = []
  seen = base_card_dict.copy()
  for run in runs:
    win = run["win"]
    floors = [x for y in run["map_point_history"] for x in y]
    act_one_floors = run["map_point_history"][0]

    for floor in floors:
      try:
        room, ps = floor["rooms"][0], floor["player_stats"][0]
        ps = floor["player_stats"][0]
        # Just do the logic by floor type
        if floor["rooms"][0]["room_type"] == "shop":
          cards_picked = []
          # Shop notation is weird as hell
          # If a card is offered for gold and not bought, it goes into the usual card choices bucket
          # If a card is offered for gold bought, it is *removed* from the card choices bucket and only referenced in "cards bought"
          # If a card is offered in a reward (e.g. orrey), it is added to card choices as usual
          # Notably, you cannot actually distinguish between skipped orrey cards and skipped shop cards
          for card in ps["card_choices"]:
            name, upgrade, pick = card["card"]["id"], card["card"].get("current_upgrade_level", 1), card["was_picked"]   
            sd = seen[name]

            # Need to track picked cards to ensure they aren't counted twice
            if pick: cards_picked.append(name)

            sd["Times offered"] += 1
            if pick: 
                sd["Times picked"] += 1
                if win: sd["Winning runs picked"] += 1
                else  : sd["Losing runs picked"] += 1

            sd["Times offered - shop"] += 1
            if pick: sd["Times picked - shop"] += 1

          for card in ps.get("cards_gained", []):
            name, upgrade, pick = card["id"], card.get("current_upgrade_level", 1), True
            sd = seen[name]

            sd["Times offered"] += 1
            sd["Times picked"] += 1

            if win: sd["Winning runs picked"] += 1
            else  : sd["Losing runs picked"] += 1

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
                if win: sd["Winning runs picked"] += 1
                else  : sd["Losing runs picked"] += 1

              sd["Times offered - card reward"] += 1
              if pick: sd["Times picked - card reward"] += 1

        elif floor["rooms"][0]["room_type"] in ["event", "rest_site", "treasure"]:
          pass

        else:
          raise ValueError(f"Unhandled room type '{floor["rooms"][0]["room_type"]}'")
      except Exception as e:
        print("Floor:::")
        print(floor)
        raise e
      
    # cards_seen.append(seen)
  return seen

# [x for x in get_card_stats(single_player_files[:1]) if x["room"][0]["room_type"] == "shop"]
card_choice_df = pd.DataFrame(get_card_stats(single_player_files)).T

card_choice_df["pick_rate"] = (card_choice_df["Times picked"] / card_choice_df["Times offered"] ).fillna(0).round(2)

card_choice_df["name"] = card_choice_df.index.map(lambda card: card_dict[card]["name"])
card_choice_df["rarity"] = card_choice_df.index.map(lambda card: card_dict[card]["rarity"])
card_choice_df["type"] = card_choice_df.index.map(lambda card: card_dict[card]["type"])
card_choice_df["class"] = card_choice_df.index.map(lambda card: card_dict[card]["color"])

final_column_order = [
 'name',
 'class',
 'rarity',
 'type',
 'Times offered',
 'Times picked',
 'pick_rate',
 'Winning runs picked',
 'Losing runs picked',
 'Times offered - card reward',
 'Times picked - card reward',
 'Times offered - shop',
 'Times picked - shop',
 ]

card_choice_df[final_column_order].to_csv("card_choices_standalone.csv")
