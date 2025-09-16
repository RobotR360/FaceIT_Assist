import json, requests

import config
from webparser import WebParser
from loggingLocal import log_print
"""Этот класс работает с неофициальным FaceIT API, может видоизмениться в дальнейшем"""
class FaceITAPI:
	#Инициализация класса требуется готовая сессия с куками FaceIT
	def __init__(self, session):
		self.session = session
#Функция возвращает последний матч и краткую информацию о игроках, без статистики матча
	def LastMatchLobby(self, nickname):
		id_user = self.get_id_user(nickname)
		id_last_match = self.get_last_matches(id_user, 1)[0]
		data_lobby, data_statistics = self.get_match(id_last_match)
		return self.get_info_lobby(data_lobby, data_statistics)
#Функция возвращает статистику на конец последнего матча
	def LastMatchStatistic(self, nickname):
		id_user = self.get_id_user(nickname)
		id_last_match = self.get_last_matches(id_user, 1)[0]
		data_lobby, data_statistics = self.get_match(id_last_match)
		return self.get_statistic_user(data_statistics, id_user)
#Функция возращает информацию о игроках, без статистики, за определенный матч
	def MatchLobby(self, id_match):
		data_lobby, data_statistics = self.get_match(id_match)
		return self.get_info_lobby(data_lobby, data_statistics)
#Функция возвращает статистику на конец определенного матча
	def MatchStatistics(self, id_match, id_user):
		data_lobby, data_statistics = self.get_match(id_match)
		return self.get_statistic_user(data_statistics, id_user)
#запрос информации об игроке по его нику
	def get_id_user(self, nickname):
		url_data_user = f"https://www.faceit.com/api/users/v1/nicknames/{nickname}"
		response = self.session.RequestGet(url_data_user)
		data = json.loads(response.text)
		return data["payload"]["id"]
#Запрос информации о последнем матче игрока по его айди
	def get_last_matches(self, user_id, quant):
		url_for_last_match = f"https://www.faceit.com/api/stats/v1/stats/time/users/{user_id}/games/cs2?size={quant}&game_mode=5v5"	   
		response = self.session.RequestGet(url_for_last_match)
		data = json.loads(response.text)
		id_matches = []
		for match in data:
			id_matches.append(match["matchId"])
		return id_matches
#Запрос полной информации о матче
	def get_match(self, match_id):
		url_data_match_details = f"https://www.faceit.com/api/stats/v3/matches/{match_id}"
		url_data_lobby = f"https://www.faceit.com/api/match/v2/match/{match_id}"	   
		response = self.session.RequestGet(url_data_lobby)
		data_lobby = json.loads(response.text)
		response = self.session.RequestGet(url_data_match_details)
		data_statistics = json.loads(response.text)
		return data_lobby, data_statistics
#Фильтрация полученных данных, о игроках в лобби, в словари
	def get_info_match_users(self, data_lobby_users):
		data_users_in_lobby = {}
		i=0
		for team in data_lobby_users:
			teams_data = {}
			team_data = data_lobby_users[team]["roster"]
			party_id = 0
			all_party_ids = []
			for user in team_data:
				user_data = {}
				if user["partyId"] not in all_party_ids:
					all_party_ids.append(user["partyId"])
					party_id_user = party_id
					party_id+=1
				else:
					party_id_user = all_party_ids.index(user["partyId"])
				user_data.update({"Nickname":user["nickname"]})
				user_data.update({"GameName":user["gameName"]}) 
				gameID=user["gameId"]
				user_data.update({"Url-Steam":f"steamcommunity.com/profiles/{gameID}"})
				nickname = user["nickname"]
				user_data.update({"Url-Faceit":f"https://www.faceit.com/ru/players/{nickname}"})
				user_data.update({"Elo":user["elo"]})
				user_data.update({"Level":user["gameSkillLevel"]})
				user_data.update({"ID-Faceit":user["id"]})
				user_data.update({"Faceit-Party":party_id_user})
				teams_data.update({"User"+str(i):user_data})
				i+=1
			teams_data.update({"AVG-Elo":data_lobby_users[team]["stats"]["rating"]})
			data_users_in_lobby.update({"Team"+team[-1]:teams_data})
		return data_users_in_lobby
#Фильтрация данных, о сервере в использованном в матче, в словарь
	def get_info_lobby(self, data_lobby, data_statistics):
		data_lobby_short ={}
		data_lobby_short.update({"startTime":data_lobby["payload"]["startedAt"]})
		data_lobby_short.update({"finishTime":data_lobby["payload"]["finishedAt"]})
		data_lobby_short.update({"location":data_lobby["payload"]["voting"]["location"]["pick"][0]})
		data_lobby_short.update({"map":data_lobby["payload"]["voting"]["map"]["pick"][0]})
		#Получение итогового счета матча, конструкция актуальна на 16.09.25 в связи с тестированием нового формата на стороне фейсит
		try:
			data_lobby_short.update({"Score": str(data_statistics[0]["teams"][0]["score"])+":"+str(data_statistics[0]["teams"][1]["score"])})
		except:
			data_lobby_short.update({"Score": data_statistics[0]["i18"]})
		data_lobby_short.update({"url_demo":data_lobby["payload"]["demoURLs"][0]})
		data_lobby_short.update({"url_match":"https://www.faceit.com/ru/cs2/room/"+data_lobby["payload"]["id"]})
		teams = self.get_info_match_users(data_lobby["payload"]["teams"])
		data_lobby_short.update({"teams":teams})
		return data_lobby_short
#Добавление вложенного словаря
	def get_statistic_user(self, data_statistics, user_id):
		data_statistic_user ={}
		statistic = self.get_info_match_statistics( data_statistics[0], user_id)
		data_statistic_user.update({"Statistics":statistic})
		return data_statistic_user
#Проверка полученной информации, относится она к старому или тестовому формату
	def get_info_match_statistics(self, data, user_id):
		statistic = {}
		if "duels" in data:
			statistic.update({"Mem-Info":self.get_mem_info(data, user_id)})
			statistic.update({"Info":self.get_info(data, user_id)})
		else:
			statistic.update({"Mem-Info-Old":"This old game don`t have info for mem moments"})
			statistic.update({"Info-Old":self.get_info_old(data, user_id)})
		return statistic
#Фильтрация старого формата в словарь
	def get_info_old(self, data, user_id):
		return_data = {}
		stats_user = self.parse_user(data, user_id)
		return_data.update({"Elo":self.elo_for_old_constructe(user_id, data["matchId"])})
		return_data.update({"Kills":stats_user["i6"]})
		return_data.update({"Death":stats_user["i8"]})
		return_data.update({"Assists":stats_user["i7"]})
		return_data.update({"ADR":stats_user["c10"]})
		return_data.update({"MVPs":stats_user["i9"]})
		return_data.update({"HsKills":stats_user["i13"]})
		return_data.update({"HsRate":stats_user["c4"]})
		return return_data
#Получение статистики определенного игрока
	def parse_user(self, data, user_id):
		for team in data["teams"]:
			for player in team["players"]:
				if user_id in player["playerId"]:
					return player
#Получение информации по матчу путем поиска этого матча у определенного игрока
	def info_match_old_constructe(self, user_id, match_id):
		default_url_last_30_match = f"https://www.faceit.com/api/stats/v1/stats/time/users/{user_id}/games/cs2?size=30"
		url_match = default_url_last_30_match
		while True:
			response = self.session.RequestGet(url_match)
			data = json.loads(response.text)
			for match in data:
				if match_id in match["matchId"]:
					return match
				else:
					url_match = default_url_last_30_match + "&to="+str(match["data"])
#Получение значения поля эло для определенного игрока из матча
	def elo_for_old_constructe(self, user_id, match_id):
		return self.info_match_old_constructe(user_id, match_id)['elo']
#Получение принадлежности игрока к команде
	def teamate_id(self, data, user_id):
		team1 = []
		for players in data["teams"][0]["players"]:
			team1.append(players["playerId"])
		team2 = []
		for players in data["teams"][1]["players"]:
			team2.append(players["playerId"])
		if user_id in team1:
			return team1
		else:
			return team2
#Сбор "Мем" информации 
	def get_mem_info(self, data, user_id):
		mem_info = {}
		team_ids = self.teamate_id(data,user_id)
		flashed_self = 0
		if user_id in data["duels"][user_id]:
			data_duel = data["duels"][user_id][user_id]
			if "flashed" in data_duel:
				flashed_self +=data_duel["flashed"]
		max_flashed = 0
		id_max_flashed_team = "nothing"
		max_damage = 0
		id_max_damage_team = "nothing"
		max_flashedBy = 0
		id_max_flashedBy_team = "nothing"
		max_damageBy = 0
		id_max_damageBy_team = "nothing"
		quant_flashed = 0
		quant_damage = 0
		quant_flashedBy = 0
		quant_damageBy = 0
		for teamate in team_ids:
			if teamate in data["duels"][user_id]:
				data_duel = data["duels"][user_id][teamate]
				if "flashed" in data_duel:
					quant_flashed += data_duel["flashed"]
					if max_flashed < data_duel["flashed"]:
						max_flashed = data_duel["flashed"]
						id_max_flashed_team = teamate
				elif "damage" in data_duel:
					quant_damage += data_duel["damage"]
					if max_damage < data_duel["damage"]:
						max_damage = data_duel["damage"]
						id_max_damage_team = teamate
				elif "flashedBy" in data_duel:
					quant_flashedBy += data_duel["flashedBy"]
					if max_flashedBy < data_duel["flashedBy"]:
						max_flashedBy = data_duel["flashedBy"]
						id_max_flashedBy_team = teamate
				elif "damageBy" in data_duel:
					quant_damageBy += data_duel["damageBy"]
					if max_damageBy < data_duel["damageBy"]:
						max_damageBy = data_duel["damageBy"]
						id_max_damageBy_team = teamate
		stats_user = self.parse_user(data, user_id)
		hits_user = stats_user["hits"]
		shot_user = stats_user["shots"]
		kill_user = stats_user["kills"]
		damage_self = 0
		damage_self += stats_user["heDamageReceivedFromSelf"]
		damage_self += stats_user["burnerDmgReceivedFromSelf"]
		mem_info.update({"FlashedSelf":flashed_self})
		mem_info.update({"DamageSelf":damage_self})
		mem_info.update({"FlashedTeam":quant_flashed})
		mem_info.update({"MaxFlashedTeamate":id_max_flashed_team})
		mem_info.update({"MaxFlash":max_flashed})
		mem_info.update({"FlashedByTeam":quant_flashedBy})
		mem_info.update({"MaxFlashedByTeamate":id_max_flashedBy_team})
		mem_info.update({"MaxFlashBy":max_flashedBy})
		mem_info.update({"DamageTeam":quant_damage})
		mem_info.update({"MaxDamageTeamate":id_max_damage_team})
		mem_info.update({"MaxDamage":max_damage})
		mem_info.update({"DamageByTeam":quant_damageBy})
		mem_info.update({"MaxDamageByTeamate":id_max_damageBy_team})
		mem_info.update({"MaxDamageBy":max_damageBy})
		mem_info.update({"Hits":hits_user})
		mem_info.update({"Shots":shot_user})
		mem_info.update({"Kills":kill_user})
		return mem_info
#Сбор статистики каждого игрока
	def get_info(self, data,user_id):
		info = {}
		stats_user = self.parse_user(data, user_id)
		info.update({"Elo":stats_user["elo"]})
		info.update({"1v1LW":str(stats_user["1v1Losses"])+"/"+str(stats_user["1v1Wins"])})
		info.update({"1v2LW":str(stats_user["1v2Losses"])+"/"+str(stats_user["1v2Wins"])})
		info.update({"1v3LW":str(stats_user["1v3Losses"])+"/"+str(stats_user["1v3Wins"])})
		info.update({"1v4LW":str(stats_user["1v4Losses"])+"/"+str(stats_user["1v4Wins"])})
		info.update({"1v5LW":str(stats_user["1v5Losses"])+"/"+str(stats_user["1v5Wins"])})
		info.update({"Accuracy":stats_user["accuracy"]})
		info.update({"AssistedFlash":stats_user["assistedFlash"]})
		info.update({"Kills":stats_user["kills"]})
		info.update({"Death":stats_user["deaths"]})
		info.update({"Assists":stats_user["assists"]})
		info.update({"ClutchRoundLW":str(stats_user["clutchRoundsLost"])+"/"+str(stats_user["clutchRoundsWon"])})
		info.update({"Damage":stats_user["damage"]})
		info.update({"HsKills":stats_user["hsKills"]})
		info.update({"HsRate":stats_user["hsRate"]})
		info.update({"ADR":stats_user["adr"]})
		info.update({"KillForBlind":stats_user["blindKills"]})
		info.update({"MVPs":stats_user["mvps"]})
		if "ct" in stats_user:
			for half in ["ct","t"]:
				stats_user_half = stats_user[half]
				info_half = {}
				info_half.update({"1v1LW":str(stats_user_half["1v1Losses"])+"/"+str(stats_user_half["1v1Wins"])})
				info_half.update({"1v2LW":str(stats_user_half["1v2Losses"])+"/"+str(stats_user_half["1v2Wins"])})
				info_half.update({"1v3LW":str(stats_user_half["1v3Losses"])+"/"+str(stats_user_half["1v3Wins"])})
				info_half.update({"1v4LW":str(stats_user_half["1v4Losses"])+"/"+str(stats_user_half["1v4Wins"])})
				info_half.update({"1v5LW":str(stats_user_half["1v5Losses"])+"/"+str(stats_user_half["1v5Wins"])})
				info_half.update({"Accuracy":stats_user_half["accuracy"]})
				info_half.update({"AssistedFlash":stats_user_half["assistedFlash"]})
				info_half.update({"Kills":stats_user_half["kills"]})
				info_half.update({"Death":stats_user_half["deaths"]})
				info_half.update({"Assists":stats_user_half["assists"]})
				info_half.update({"ClutchRoundLW":str(stats_user_half["clutchRoundsLost"])+"/"+str(stats_user_half["clutchRoundsWon"])})
				info_half.update({"Damage":stats_user_half["damage"]})
				info_half.update({"HsKills":stats_user_half["hsKills"]})
				info_half.update({"HsRate":stats_user_half["hsRate"]})
				info_half.update({"ADR":stats_user_half["adr"]})
				info_half.update({"KillForBlind":stats_user_half["blindKills"]})
				info_half.update({"MVPs":stats_user_half["mvps"]})
				info.update({half:info_half})
		return info
