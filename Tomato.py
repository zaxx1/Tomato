from colorama import *
from datetime import datetime
from fake_useragent import FakeUserAgent
from faker import Faker
from time import sleep
import gc
import json
import os
import pytz
import random
import requests
import sys


class Tomarket:
    def __init__(self, query_file=None, accounts_file=None, tokens_file=None) -> None:
        self.session = requests.Session()
        self.faker = Faker()
        self.query_file = query_file
        self.accounts_file = accounts_file
        self.tokens_file = tokens_file
        self.tokens_saved = False
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'api-web.tomarket.ai',
            'Origin': 'https://mini-app.tomarket.ai',
            'Pragma': 'no-cache',
            'Referer': 'https://mini-app.tomarket.ai/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        now = datetime.now(pytz.timezone('Asia/Jakarta'))
        timestamp = now.strftime(f'%x %X %Z')
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {timestamp} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    def split_queries(self, queries_file, lines_per_file=10):
        with open(queries_file, 'r') as f:
            queries = [line.strip() for line in f.readlines() if line.strip()]

        total_lines = len(queries)
        files_created = []

        for i in range(0, total_lines, lines_per_file):
            chunk = queries[i:i + lines_per_file]
            file_index = (i // lines_per_file) + 1
            query_file = f"queries-{file_index}.txt"

            with open(query_file, 'w') as f_out:
                f_out.write("\n".join(chunk))

            files_created.append(query_file)
        return files_created

    def user_login(self):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/login'
        try:
            if not os.path.exists(self.query_file):
                raise FileNotFoundError(f"File '{self.query_file}' Not Found. Please Ensure It Exists")

            with open(self.query_file, 'r') as f:
                queries = [line.strip() for line in f.readlines()]

            if not queries:
                raise ValueError(f"File '{self.query_file}' Is Empty. Please Fill It With Queries")

            accounts = []
            for query in queries:
                if not query:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Empty Query Found, Skipping... ]{Style.RESET_ALL}")
                    continue

                data = json.dumps({'init_data':query,'invite_code':'0000cYQe','from':'','is_bot':False})
                self.headers.update({
                    'Content-Length': str(len(data)),
                    'Content-Type': 'application/json'
                })
                response = self.session.post(url=url, headers=self.headers, data=data)
                response.raise_for_status()
                data = response.json()
                access_token = data['data']['access_token']
                first_name = data['data']['fn']
                if not first_name:
                    first_name = self.faker.first_name()
                accounts.append({
                    'first_name': first_name,
                    'token': access_token
                })

            with open(self.accounts_file, 'w') as outfile:
                json.dump({'accounts': accounts}, outfile, indent=4)

            self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Generated Tokens In '{self.accounts_file}' ]{Style.RESET_ALL}")

            if not self.tokens_saved:
                with open(self.tokens_file, 'w') as tokens_file:
                    for account in accounts:
                        tokens_file.write(f"{account['token']}\n")
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Successfully Backed Up Tokens To '{self.tokens_file}' ]{Style.RESET_ALL}")
                self.tokens_saved = True

            return accounts
        except (FileNotFoundError, ValueError, requests.RequestException, json.JSONDecodeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
            return []

    def claim_daily(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/daily/claim'
        data = json.dumps({'game_id':'fa873d13-d831-4d6f-8aee-9cff7a1d0db1'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_daily = response.json()
            if claim_daily is not None:
                if 'status' in claim_daily:
                    if claim_daily['status'] == 0:
                        self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Daily Claimed ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Points {claim_daily['data']['today_points']} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Day {claim_daily['data']['today_game']} ]{Style.RESET_ALL}"
                        )
                    elif claim_daily['status'] == 400 and claim_daily['message'] == 'already_check':
                        self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Already Check Daily Claim ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_daily['message']}' Status '{claim_daily['status']}' In Daily Claim ]{Style.RESET_ALL}")
                elif 'code' in claim_daily:
                    if claim_daily['code'] == 400 and claim_daily['message'] == 'claim throttle':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Daily Claim Throttle ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_daily['message']}' Code '{claim_daily['status']}' In Daily Claim ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Daily Claim ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data In Daily Claim Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Daily Claim: {str(e)} ]{Style.RESET_ALL}")

    def balance_user(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/user/balance'
        self.headers.update({
            'Authorization': token,
            'Content-Length': '0'
        })
        response = self.session.post(url=url, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def start_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/start'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            start_farm = response.json()
            if start_farm is not None:
                if 'status' in start_farm:
                    if start_farm['status'] in [0, 200]:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Farming Started ]{Style.RESET_ALL}")
                        now = datetime.now(pytz.timezone('Asia/Jakarta'))
                        farm_end_at = datetime.fromtimestamp(start_farm['data']['end_at'], pytz.timezone('Asia/Jakarta'))
                        if now >= farm_end_at:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming Farming ]{Style.RESET_ALL}")
                            self.claim_farm(token=token)
                        else:
                            timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farming Can Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
                    elif start_farm['status'] == 500 and start_farm['message'] == 'game already started':
                        now = datetime.now(pytz.timezone('Asia/Jakarta'))
                        farm_end_at = datetime.fromtimestamp(start_farm['data']['end_at'], pytz.timezone('Asia/Jakarta'))
                        if now >= farm_end_at:
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming Farming ]{Style.RESET_ALL}")
                            self.claim_farm(token=token)
                        else:
                            self.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Farming Already Started ]{Style.RESET_ALL}")
                            timestamp_farm_end_at = farm_end_at.strftime('%X %Z')
                            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Farming Can Claim At {timestamp_farm_end_at} ]{Style.RESET_ALL}")
                    elif start_farm['status'] == 500 and start_farm['message'] == 'game end need claim':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming Farming ]{Style.RESET_ALL}")
                        self.claim_farm(token=token)
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{start_farm['message']}' Status '{start_farm['status']}' In Farm Start ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In Start Farming ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data In Start Farming Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Farming: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Start Farming: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Farming: {str(e)} ]{Style.RESET_ALL}")

    def claim_farm(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/farm/claim'
        data = json.dumps({'game_id':'53b22103-c7ff-413d-bc63-20f6fb806a07'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_farm = response.json()
            if claim_farm is not None:
                if 'status' in claim_farm:
                    if claim_farm['status'] == 0:
                        self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Farming Claimed {claim_farm['data']['points']} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Start Farming ]{Style.RESET_ALL}"
                        )
                        self.start_farm(token=token)
                    elif claim_farm['status'] == 500 and claim_farm['message'] == 'farm not started or claimed':
                        self.print_timestamp(
                            f"{Fore.RED + Style.BRIGHT}[ Farming Not Started ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Start Farming ]{Style.RESET_ALL}"
                        )
                        self.start_farm(token=token)
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_farm['message']}' Status '{claim_farm['status']}' In Claim Farming Data ]{Style.RESET_ALL}")
                elif 'code' in claim_farm:
                    if claim_farm['code'] == 400 and claim_farm['message'] == 'claim throttle':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Farming Throttle ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_farm['message']}' Code '{claim_farm['status']}' In Farm Claim ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Claim Farming ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Claim Farming Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Farming: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Farming: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Farming: {str(e)} ]{Style.RESET_ALL}")

    def play_game(self, token: str, first_name: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/play'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            play_game = response.json()
            if play_game is not None:
                if 'status' in play_game:
                    if play_game['status'] == 0:
                        self.print_timestamp(
                            f"{Fore.GREEN + Style.BRIGHT}[ Game Started ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.BLUE + Style.BRIGHT}[ Please Wait 30 Seconds ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        )
                        sleep(33)
                        self.claim_game(token=token, points=random.randint(700, 800))
                    elif play_game['status'] == 500 and play_game['message'] == 'no chance':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No Chance To Start Game ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{play_game['message']}' Status '{play_game['status']}' In Game Play ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In Play Game ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Play Game Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")

    def claim_game(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d','points':points})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_game = response.json()
            if claim_game is not None:
                if 'status' in claim_game:
                    if claim_game['status'] == 0:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {claim_game['data']['points']} ]{Style.RESET_ALL}")
                    elif claim_game['status'] == 500 and claim_game['message'] == 'game not start':
                        self.print_timestamp(
                            f"{Fore.RED + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Starting Game ]{Style.RESET_ALL}"
                        )
                        self.play_game(token=token)
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Status '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
                elif 'code' in claim_game:
                    if claim_game['code'] == 400 and claim_game['message'] == 'claim throttle':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Game Throttle ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Code '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Claim Game ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Claim Game Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")

    def claim_game(self, token: str, points: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/game/claim'
        data = json.dumps({'game_id':'59bcd12e-04e2-404c-a172-311a0084587d','points':points})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_game = response.json()
            if claim_game is not None:
                if 'status' in claim_game:
                    if claim_game['status'] == 0:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Game Claimed {claim_game['data']['points']} ]{Style.RESET_ALL}")
                    elif claim_game['status'] == 500 and claim_game['message'] == 'game not start':
                        self.print_timestamp(
                            f"{Fore.RED + Style.BRIGHT}[ Game Not Start ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Starting Game ]{Style.RESET_ALL}"
                        )
                        self.play_game(token=token)
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Status '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
                elif 'code' in claim_game:
                    if claim_game['code'] == 400 and claim_game['message'] == 'claim throttle':
                        self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claim Game Throttle ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_game['message']}' Code '{claim_game['status']}' In Claim Game ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' Or 'code' In Claim Game ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Claim Game Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Game: {str(e)} ]{Style.RESET_ALL}")

    def list_tasks(self, token: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/list'
        data = json.dumps({'language_code':'en'})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        response = self.session.post(url=url, headers=self.headers, data=data)
        response.raise_for_status()
        list_tasks = response.json()
        current_time = datetime.now()
        for category in list_tasks['data']:
            for task in list_tasks['data'][category]:
                end_time = datetime.strptime(task.get('endTime'), '%Y-%m-%d %H:%M:%S') if task.get('endTime') else None
                if (
                    (end_time and end_time < current_time) or
                    ('walletAddress' in task['handleFunc'] or 'boost' in task['handleFunc'] or 'checkInvite' in task['handleFunc']) or
                    ('bitget' in task['title'].lower()) or
                    ('classmate' in task['type'].lower())
                ):
                    continue
                wait_second = task.get('waitSecond', 0)
                if task['status'] == 0 and task['type'] == "mysterious":
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                    self.claim_tasks(token=token, task_id=task['taskId'], task_title=task['title'])
                elif task['status'] == 0:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Starting {task['title']} ]{Style.RESET_ALL}")
                    self.start_tasks(token=token, task_id=task['taskId'], task_title=task['title'], task_waitsecond=wait_second)
                elif task['status'] == 1:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ You Haven't Finish Or Start {task['title']} ]{Style.RESET_ALL}")
                    self.check_tasks(token=token, task_id=task['taskId'], task_title=task['title'])
                elif task['status'] == 2:
                    self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task['title']} ]{Style.RESET_ALL}")
                    self.claim_tasks(token=token, task_id=task['taskId'], task_title=task['title'])

    def start_tasks(self, token: str, task_id: int, task_title: str, task_waitsecond: int):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/start'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            start_tasks = response.json()
            if start_tasks is not None:
                if 'status' in start_tasks:
                    if start_tasks['status'] == 0:
                        if 'status' in start_tasks['data']:
                            if start_tasks['data']['status'] == 1:
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Checking {task_title} ]{Style.RESET_ALL}")
                                sleep(task_waitsecond + 3)
                                self.check_tasks(token=token, task_id=task_id, task_title=task_title)
                            elif start_tasks['data']['status'] == 2:
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task_title} ]{Style.RESET_ALL}")
                                self.claim_tasks(token=token, task_id=task_id, task_title=task_title)
                        else:
                            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In 'data' Start Tasks ]{Style.RESET_ALL}")
                    elif start_tasks['status'] == 500 and start_tasks['message'] == 'Handle user\'s task error':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Finish {task_title} By Itself ]{Style.RESET_ALL}")
                    elif start_tasks['status'] == 500 and start_tasks['message'] == 'Task handle is not exist':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Exist ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{start_tasks['message']}' Status '{start_tasks['status']}' In Start Tasks ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In Start Tasks ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Start Tasks Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")

    def check_tasks(self, token: str, task_id: int, task_title: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/check'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            check_tasks = response.json()
            if check_tasks is not None:
                if 'status' in check_tasks:
                    if check_tasks['status'] == 0:
                        if 'status' in check_tasks['data']:
                            if check_tasks['data']['status'] == 1:
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ {task_title} Still Have Not Finished ]{Style.RESET_ALL}")
                            elif check_tasks['data']['status'] == 2:
                                self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ Claiming {task_title} ]{Style.RESET_ALL}")
                                self.claim_tasks(token=token, task_id=task_id, task_title=task_title)
                        else:
                            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In 'data' Check Tasks ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{check_tasks['message']}' Status '{check_tasks['status']}' In Check Tasks ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In Check Tasks ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Check Tasks Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Check Tasks: {str(e)} ]{Style.RESET_ALL}")

    def claim_tasks(self, token: str, task_id: int, task_title: str):
        url = 'https://api-web.tomarket.ai/tomarket-game/v1/tasks/claim'
        data = json.dumps({'task_id':task_id})
        self.headers.update({
            'Authorization': token,
            'Content-Length': str(len(data)),
            'Content-Type': 'application/json'
        })
        try:
            response = self.session.post(url=url, headers=self.headers, data=data)
            response.raise_for_status()
            claim_tasks = response.json()
            if claim_tasks is not None:
                if 'status' in claim_tasks:
                    if claim_tasks['status'] == 0:
                        self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ {task_title} Claimed ]{Style.RESET_ALL}")
                    elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t start this task':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Have Not Start {task_title} ]{Style.RESET_ALL}")
                    elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'You haven\'t finished this task':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ You Have Not Finished {task_title} ]{Style.RESET_ALL}")
                    elif claim_tasks['status'] == 500 and claim_tasks['message'] == 'Task is not within the valid time':
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_title} Is Not Within The Valid Time ]{Style.RESET_ALL}")
                    else:
                        self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Error '{claim_tasks['message']}' Status '{claim_tasks['status']}' In Claim Tasks ]{Style.RESET_ALL}")
                else:
                    self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ There Is No 'status' In Claim Tasks ]{Style.RESET_ALL}")
            else:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Data Claim Tasks Is None ]{Style.RESET_ALL}")
        except requests.HTTPError as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except requests.RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ A Request Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")
        except Exception as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    def main(self):
        while True:
            try:
                accounts = self.user_login()
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ ————— Information ————— ]{Style.RESET_ALL}")
                for account in accounts:
                    self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}")
                    self.claim_daily(token=account['token'])
                    balance = self.balance_user(token=account['token'])
                    self.print_timestamp(
                        f"{Fore.YELLOW + Style.BRIGHT}[ Balance {balance['data']['available_balance']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Play Passes {balance['data']['play_passes']} ]{Style.RESET_ALL}"
                    )
                    self.start_farm(token=account['token'])
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ ————— Tasks ————— ]{Style.RESET_ALL}")
                for account in accounts:
                    self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}")
                    self.list_tasks(token=account['token'])
                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ ————— Play Passes ————— ]{Style.RESET_ALL}")
                for account in accounts:
                    balance = self.balance_user(token=account['token'])
                    if balance['data']['play_passes'] != 0:
                        while balance['data']['play_passes'] > 0:
                            self.play_game(token=account['token'], first_name=account['first_name'])
                            balance['data']['play_passes'] -= 1
                    else:
                        self.print_timestamp(
                            f"{Fore.RED + Style.BRIGHT}[ Not Enough Play Passes ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}[ {account['first_name']} ]{Style.RESET_ALL}"
                        )
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting Soon ]{Style.RESET_ALL}")
                sleep(3 * 3600)
                self.clear_terminal()
                gc.collect()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue


if __name__ == '__main__':
    try:
        init(autoreset=True)

        if not os.path.exists('queries.txt'):
            print(f"{Fore.RED + Style.BRIGHT}[ 'queries.txt' Not Found In The Directory ]{Style.RESET_ALL}", flush=True)
            sys.exit(1)

        tomarket = Tomarket(None, None, None)
        created_files = tomarket.split_queries('queries.txt')

        tomarket.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Select The Queries File To Use ]{Style.RESET_ALL}")
        for i, query_file in enumerate(created_files, start=1):
            tomarket.print_timestamp(
                f"{Fore.MAGENTA + Style.BRIGHT}[ {i} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.CYAN + Style.BRIGHT}[ {query_file} ]{Style.RESET_ALL}"
            )

        choice = int(input(
            f"{Fore.CYAN + Style.BRIGHT}[ Enter The Number Corresponding To The File You Want To Use ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        )) - 1

        if choice < 0 or choice >= len(created_files):
            raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

        selected_query = created_files[choice]
        base_name = selected_query.split('-')[1].split('.')[0]
        accounts_file = f"accounts-{base_name}.json"
        tokens_file = f"tokens-{base_name}.txt"

        tomarket = Tomarket(selected_query, accounts_file, tokens_file)
        tomarket.main()
    except (ValueError, IndexError):
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ Invalid Selection. Please Run The Script Again And Choose A Valid Option ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        tomarket.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ See You ]{Style.RESET_ALL}")
        sys.exit(0)
