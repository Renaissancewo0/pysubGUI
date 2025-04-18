import json
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from enum import Enum

class Status(Enum):
    SUSPEND = 0
    MKV = 1
    MONOLINGUAL = 2
    BILINGUAL = 3
    
def check_config_json():
    config = {}
    flag_configChanged = 0
    try:
        with open('config.json', 'r', encoding = 'utf-8') as fp:
            config.update(json.load(fp))
    except FileNotFoundError:
        config['mkvtoolnix'] = ask_for_mkvtoolnix()
        config['patterns'] = ask_for_patterns()
        flag_configChanged += 1
    
    if not Path(config['mkvtoolnix']).exists():
        config['mkvtoolnix'] = ask_for_mkvtoolnix()
        flag_configChanged += 1
    if not Path(config['patterns']).exists():
        config['patterns'] = ask_for_patterns()
        flag_configChanged += 1
    
    if flag_configChanged:
        with open('config.json', 'w', encoding = 'utf-8') as fp:
            json.dump(config, fp, indent = 4, ensure_ascii = False)

def ask_for_mkvtoolnix():
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title = '选择mkvtoolnix文件夹')
    return folder
            
def ask_for_patterns():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title = '指定patterns.csv路径',
                                      filetypes = [('CSV UTF-8 (逗号分隔)', '*.csv'), ('所有文件',  '*.*')])
    return path
    
