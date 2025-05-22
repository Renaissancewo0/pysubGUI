import json
import subprocess
from enum import Enum
from PySide6.QtWidgets import QFileDialog


class Status(Enum):
    SUSPEND = 0
    MKV = 1
    MONOLINGUAL = 2
    BILINGUAL = 3

def check_config_json():
    config = {}
    flag_configChanged = 0
    with open('config.json', 'r', encoding = 'utf-8') as fp:
        config.update(json.load(fp))
    
    while not check_mkvextractor(config['mkvtoolnix']):
        config['mkvtoolnix'] = ask_for_mkvtoolnix()
        flag_configChanged += 1
    
    if flag_configChanged:
        with open('config.json', 'w', encoding = 'utf-8') as fp:
            json.dump(config, fp, indent = 4, ensure_ascii = False)

def ask_for_mkvtoolnix():
    folder = QFileDialog.getExistingDirectory(caption = '选择mkvtoolnix文件夹路径')
    return folder

def check_mkvextractor(path) -> bool:
    try:
        subprocess.run([f'{path}\\mkvextract', '--version'])
    except FileNotFoundError:
        return False
    return True

def read_config():
    with open('config.json', 'r', encoding = 'utf-8') as fp:
        configuration = json.load(fp)
    return configuration
