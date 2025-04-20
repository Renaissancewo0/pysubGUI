import subprocess
import json
from pathlib import Path

from readconfig import config
MKV_MERGE = f'{config["mkvtoolnix"]}\\mkvmerge'
MKV_EXTRACT = f'{config["mkvtoolnix"]}\\mkvextract'

class MkvSubExtractor:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.read_sub_tracks()
        # For display cmd lines to other window

    def read_sub_tracks(self):
        result = subprocess.run(
            [MKV_MERGE, self.path, '-i', '-F', 'json'],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True,
            encoding = 'utf-8'
        )
        info = json.loads(result.stdout)
        self.subTracks = [track for track in info['tracks'] if track['type'] == 'subtitles']
        
    def get_track_id(self, track: int):
        return self.subTracks[track]['id']

    def extract_subtitle(self, track_id, outputPath: Path):
        subprocess.run([MKV_EXTRACT, self.path, 'tracks', f"{track_id}:{str(outputPath)}"])


if __name__ == '__main__':
    path = r"E:\Renaissance\翻译相关\KitaujiSub_TextProcessor\pysubGUI\test_files\The.Apothecary.Diaries.S02E14.The.Dancing.Ghost.1080p.NF.WEB-DL.AAC2.0.H.264-VARYG.mkv"
    mkv = MkvSubExtractor(path)
    with open('test_files\\Kusuriya S02E14.json', 'w', encoding = 'utf-8') as fp:
        json.dump(mkv.subTracks, fp, indent = 4, ensure_ascii = False)