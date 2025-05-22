import subprocess
import json
from pathlib import Path
from config import read_config


class MkvSubExtractor:
    def __init__(self, path: Path):
        self.config = read_config()
        self.merge = f'{self.config["mkvtoolnix"]}\\mkvmerge'
        self.extract = f'{self.config["mkvtoolnix"]}\\mkvextract'
        
        self.path = Path(path)
        self.read_sub_tracks()

    def read_sub_tracks(self):
        result = subprocess.run(
            [self.merge, self.path, '-i', '-F', 'json'],
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
        subprocess.run([self.extract, self.path, 'tracks', f"{track_id}:{str(outputPath)}"])

