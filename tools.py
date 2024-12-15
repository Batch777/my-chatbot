import json
import glob
import os
import psutil
import random
import subprocess
import fnmatch
from colorama import Fore, Style, init
import random

init(autoreset=True)

def print_first_ten_elements(input_list):
    # 取前十个元素
    first_ten = input_list[:10]
    # 配置颜色
    colors = [Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTBLUE_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTMAGENTA_EX]

    color_temp = None
    # 打印结果
    for element in first_ten:
        #不和前一个颜色重复
        color_temp = random.choice([color for color in colors if color is not color_temp])
        print(color_temp + str(element) + Style.RESET_ALL)  # 随机选择颜色

def find_and_kill_process_by_name(process_name):
    for proc in psutil.process_iter(['name']):
        if process_name.lower() in proc.info['name'].lower():
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

def music_player(music_name: str, toggle_button: str):
    # 定义音乐目录
    music_dir = os.path.expanduser("~/Music/")

    # 获取音乐文件列表
    all_music_files = [f for f in os.listdir(music_dir) if fnmatch.fnmatch(f, '*.mp3')]
    random.shuffle(all_music_files)

    if music_name:
        # 模糊搜索匹配的歌曲
        matches = [f for f in all_music_files if music_name.lower() in f.lower()]
        if matches:
            # 如果找到匹配的歌曲，将其放到列表的顶部
            music_files = matches + [f for f in all_music_files if f not in matches]
        else:
            return "没有找到符合条件的音乐。"
    else:
        # 随机播放
        music_files = all_music_files

    # 根据指令播放或停止音乐
    if toggle_button == 'play':
        find_and_kill_process_by_name("mpg123")
        run_code = ["mpg123", "-list", "-q"] + [os.path.join(music_dir, _) for _ in music_files]
        subprocess.Popen(run_code)
        print_first_ten_elements(music_files)
        return "成功播放音乐"
            # 在这里可以调用实际的播放音乐代码，例如使用pygame或其他音频库
            # 例如将它作为 subprocess 运行：
            # os.system(f"start {os.path.join(music_dir, song)}")  # Windows
            # os.system(f"open {os.path.join(music_dir, song)}")  # macOS
            # os.system(f"xdg-open {os.path.join(music_dir, song)}")  # Linux
            # p = subprocess.Popen(["mpg123", os.path.join(music_dir, song)])
    elif toggle_button == 'stop':
        try:
            find_and_kill_process_by_name("mpg123")
            return "已停止播放"
        except:
            return "无要停止播放的音乐"
    else:
        return "无效的指令，请使用 'play' 或 'stop'。"


