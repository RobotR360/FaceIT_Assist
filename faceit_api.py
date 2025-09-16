import requests, json, time, os
from datetime import datetime, timezone, timedelta

import config
from webparser import WebParser
from loggingLocal import log_print
browserSession = WebParser()
browserSession.attach_cookies_to_session(browserSession.load_cookies())
tz_plus_6 = timezone(timedelta(hours=6))

class FaceIT:

	def __init__(self, token):
		self.baseURL = "https://open.faceit.com/data/v4"
		self.headers = {
    		'Authorization': f'Bearer {token}',
    		'Content-Type': 'application/json'
			}
		self.player = self.Player(self)
		self.match = self.Match(self)

	def build_url_match(self, match_id):
		return f"https://www.faceit.com/ru/cs2/room/{match_id}"

	class Player:
		def __init__(self, outer):
			self.outer= outer
			self.url = f"{self.outer.baseURL}/players"

		def build_data_player(self):
			self.data = {
				"ID":self.id,
				"Nickname":self.F_Nickname,
				"URL-FaceIT":self.F_url,
				"URL-Steam":self.S_url,
				"Nickname-Steam":self.S_Nickname,
				"Elo":self.Elo,
				"Level":self.Level,
				"Activated":self.Activated,
				"ID-Last":self.last_match,
				"Quant matches":self.Match,
				"Win rate":self.Win_rate,
				"Stat 5":self.last5 
			}

		def get_data_file(self, nickname):
			with open(f"src\\data\\players\\{nickname}\\data.json", 'r') as f:
				data = json.load(f)
			self.id = data["ID"]
			self.F_Nickname=data["Nickname"]
			self.F_url=data["URL-FaceIT"]
			self.S_url = data["URL-Steam"]
			self.S_Nickname = data['Nickname-Steam']
			self.Elo = data["Elo"]
			self.Level = data["Level"]
			self.last_match = data["ID-Last"]
			self.Activated = data["Activated"]
			self.Match = data["Quant matches"],
			self.Win_rate = data["Win rate"],
			self.last5 = data["Stat 5"]
			self.build_data_player()
			return self

		def get_data_web(self, nickname):
			params = {'nickname':nickname}
			try:
				response = requests.get(
	                    self.url,
	                    headers=self.outer.headers,
	                    params=params)
				response.raise_for_status()
				data = response.json()
				self.id = data["player_id"] 
				self.F_Nickname=data["nickname"]
				self.F_url=data["faceit_url"].replace("{lang}","ru")
				self.S_url = "steamcommunity.com/profiles/"+data["steam_id_64"]
				self.S_Nickname = data['steam_nickname']
				self.Elo = data["games"]["cs2"]["faceit_elo"]
				self.Level = data["games"]["cs2"]["skill_level"]
				self.Activated = data["activated_at"]
				self.last_match = ""
				self.get_stats_cs2()
				self.get_last_match()
				self.build_data_player()
				os.makedirs(f"src\\data\\players\\{nickname}", exist_ok=True)
				with open(f"src\\data\\players\\{nickname}\\data.json", "w") as file:
					json.dump(self.data, file)
				return self
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None

		def get(self, nickname):
			if os.path.isfile(f"src\\data\\players\\{nickname}\\data.json"):
				return self.get_data_file(nickname)
			else:
				return self.get_data_web(nickname)
			
		def get_stats_cs2(self):
			endpoint = f"/{self.id}/stats/cs2"
			try:
				response = requests.get(
	                    self.url+endpoint,
	                    headers=self.outer.headers)
				response.raise_for_status()
				data = response.json()
				self.Match = data["lifetime"]["Matches"]
				self.Win_rate = data["lifetime"]["Win Rate %"]
				self.last5 = data["lifetime"]["Recent Results"]
				return self.Match
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None

		def get_last_match(self):
			params = {'limit': 1,'offset': 0}
			#params = {}
			endpoint = f"/{self.id}/history"
			try:
				response = requests.get(
	                    self.url+endpoint,
	                    headers=self.outer.headers,
	                    params=params)
				response.raise_for_status()
				items = response.json()
				last_match = items['items'][0]['match_id']
			except Exception as e:
				log_print(f"ERROR faceit_api {e} used alt version")
				data = self.get_last_match_alt()
				last_match = data['match_id']
			finally:
				if last_match != self.last_match:
					self.last_match = last_match
				return self.last_match

		def get_last_match_alt(self):
			try:
				url_for_last_match = f"https://www.faceit.com/api/stats/v1/stats/time/users/{self.id}/games/cs2?size={1}&game_mode=5v5"	   
				response = self.session.RequestGet(url_for_last_match)
				data = json.loads(response.text)
				return data[0]
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None

	class Match:

		def __init__(self,outer):
			self.outer = outer
			self.url = f"{self.outer.baseURL}/matches"
			self.session = browserSession

		def get_data_web(self, match_id):
			self.id = match_id
			endpoint = f"/{self.id}"
			try:
				response = requests.get(
	                    self.url+endpoint,
	                    headers=self.outer.headers)
				response.raise_for_status()
				data = response.json()
				self.startTime = datetime.fromtimestamp(int(data["started_at"]), tz_plus_6).strftime("%Y-%m-%d %H:%M")
				self.finishTime = datetime.fromtimestamp(int(data["finished_at"]), tz_plus_6).strftime("%Y-%m-%d %H:%M")
				self.map = data["voting"]["map"]["pick"][0]
				self.location = data["voting"]["location"]["pick"][0]
				self.get_stats()
				self.image = browserSession.get_screenshot(f"https://www.faceit.com/ru/cs2/room/{self.id}", self.id)
				self.build_data_match()
				return self.data
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None

		def get_data_file(self,match_id):
			with open(f"src\\data\\matches\\{match_id}\\data.json", 'r') as f:
				data = json.load(f)
			self.id = data['ID']
			self.startTime = data["Start"]
			self.finishTime = data["End"]
			self.map = data["Map"]
			self.location = data["Location"]
			self.score = data["Score"]
			self.teams = data["Teams"]
			self.image = data["Image"]
			if not os.path.isfile(f"src\\data\\matches\\{self.id}\\img\\{self.id}.png"):
				self.image = browserSession.get_screenshot(f"https://www.faceit.com/ru/cs2/room/{self.id}", self.id)
			self.build_data_match()
			return self.data

		def get(self, match_id):
			if os.path.isfile(f"src\\data\\matches\\{match_id}\\data.json"):
				return self.get_data_file(match_id)
			else:
				return self.get_data_web(match_id)
			
		def get_data_dont_api(self):
			url_data_match_details = f"https://www.faceit.com/api/stats/v3/matches/{self.id}"
			url_data_lobby = f"https://www.faceit.com/api/match/v2/match/{self.id}"	   
			response = self.session.RequestGet(url_data_lobby)
			data_lobby = json.loads(response.text)['payload']['teams']
			response = self.session.RequestGet(url_data_match_details)
			data_statistics = json.loads(response.text)[0]
			return data_lobby, data_statistics

		def calculatedLVL(self, quant):
			match quant:
				case quant if quant >=100 and quant <=500:
					return 1
				case quant if quant >=501 and quant <=750:
					return 2
				case quant if quant >=751 and quant <=900:
					return 3
				case quant if quant >=901 and quant <=1050:
					return 4
				case quant if quant >=1051 and quant <=1200:
					return 5
				case quant if quant >=1201 and quant <=1350:
					return 6
				case quant if quant >=1351 and quant <=1530:
					return 7
				case quant if quant >=1531 and quant <=1750:
					return 8
				case quant if quant >=1751 and quant <=2000:
					return 9
				case quant if quant >=2001 and quant <=9999:
					return 10

		def get_elo_end(self, player_data, match_id):
			try:
				player_elo = {
				"End Elo": player_data['elo'],
				"End lvl": self.calculatedLVL(player_data['elo'])
				}
			except Exception as e:
				log_print(f"ERROR faceit_api {e} used alt version")
				elo = self.elo_for_old_constructe(player_data["playerId"], match_id)
				player_elo = {
				"End Elo": elo,
				"End lvl": self.calculatedLVL(elo)
				}
			finally:
				return player_elo

		def elo_for_old_constructe(self, user_id, match_id):
			try:
				default_url_last_30_match = f"https://www.faceit.com/api/stats/v1/stats/time/users/{user_id}/games/cs2?size=30"
				url_match = default_url_last_30_match
				while True:
					response = self.session.RequestGet(url_match)
					data = json.loads(response.text)
					for match in data:
						if match_id in match["matchId"]:
							return match["elo"]
						else:
							url_match = default_url_last_30_match + "&to="+str(match["data"])
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None

		def rebuild_teamData(self):
			self.teams = {}
			numberTeam = 0
			data_api_v2,data_api_v3 = self.get_data_dont_api()
			for team in self.teams_data:
				players = []
				for player in team["players"]:
					player_data = {}
					playerFaceit = self.outer.Player(self.outer)
					player_info = playerFaceit.get(player['nickname'])
					player_data.update(playerFaceit.data)
					playerFaceit.data.update({
						"Kill":player["player_stats"]["Kills"],
						"Death":player["player_stats"]["Deaths"],
						"Assists":player["player_stats"]["Assists"]
						})
					for team_v2 in data_api_v2:
						for player_v2 in data_api_v2[team_v2]["roster"]:
							if player["player_id"] == player_v2["id"]:
								playerFaceit.data.update({
									"Start Elo": player_v2['elo'],
									"Start lvl": player_v2['gameSkillLevel']
									})
					for team_v3 in data_api_v3["teams"]:
						for player_v3 in team_v3['players']:
							if player["player_id"] == player_v3["playerId"]:
								data = self.get_elo_end(player_v3, self.id)
								playerFaceit.data.update(data)
					players.append(playerFaceit.data)
				numberTeam+=1
				self.teams.update({f"Team{numberTeam}":players})

		def build_data_match(self):
			self.data = {
				"ID":self.id,
				"Start":self.startTime,
				"End":self.finishTime,
				"Map":self.map,
				"Location":self.location,
				"Score":self.score,
				"Image":self.image,	
				"Teams":self.teams
			}
			os.makedirs(f"src\\data\\matches\\{self.id}", exist_ok=True)
			with open(f"src\\data\\matches\\{self.id}\\data.json", "w") as file:
				json.dump(self.data, file)

		def get_stats(self):
			endpoint = f"/{self.id}/stats"
			try:
				response = requests.get(
	                    self.url+endpoint,
	                    headers=self.outer.headers)
				response.raise_for_status()
				data = response.json()
				self.score = data["rounds"][0]["round_stats"]["Score"]		
				self.teams_data = data["rounds"][0]["teams"]
				self.rebuild_teamData()
				return data
			except Exception as e:
				log_print(f"ERROR faceit_api {e}")
				return None
		

