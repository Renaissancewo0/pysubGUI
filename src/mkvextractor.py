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

