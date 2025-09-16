import os
from datetime import datetime


def log_print(text):
	os.makedirs(f"src\\logs\\", exist_ok=True)
	now = datetime.now()
	with open("log.txt", "a") as file:
		file.write(now.strftime("%H:%M %d.%m.%Y")+f"\t\t{text}\n")