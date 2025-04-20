import re
import functools
from pathlib import Path
from collections.abc import Sequence

import openpyxl
from readconfig import config

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from subtitle import ASSReader

PATTERNS = config['patterns']

class TextProcessor:
    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        self.text = TextProcessor.process(self.raw_text)

    @staticmethod
    def process(text) -> str:
        with open(PATTERNS, 'r', encoding = 'utf-8-sig') as entries:
            for entry in entries:
                flag, p, rep = entry.split(',')[:3]
                if int(flag):
                    text = re.sub(p, rep, text, flags = re.MULTILINE)
        return text

    def write(self, path: Path):
        with open(path, 'w', encoding = 'utf-8') as fp:
            fp.write(self.text)


class BilingualText(Sequence):
    def __init__(self) -> None:
        self.contents: list[list[str, str]] = []
        
    def __len__(self) -> int:
        return len(self.contents)
    
    def __getitem__(self, idx):
        return self.contents[idx]
    
    def _readTxt(self, text: str) -> None:
        # Reverse to get jp ahead
        self.contents = [list(reversed(line.split('\n', maxsplit = 1)))
                         for line in text.strip().split('\n\n')]
    
    def load_from_ass(self, source: 'ASSReader'):
        if not source.bilingual:
            raise TypeError('Only bilingual ASS can be loaded.')
        jpDict = {}
        cnDict = {}
        for style in source.styles:
            timeDict = {line.key(): line.text for line in getattr(source, style)}
            if 'jp' in style.lower():
                jpDict.update(timeDict)
            elif 'cn' in style.lower():
                cnDict.update(timeDict)
        keys = set(jpDict.keys()) | set(cnDict.keys())
        for key in sorted(keys, key = lambda x: x[0]):
            jp = jpDict.get(key, '')
            jp = re.sub(r'\{.+?\}', r'', jp)
            cn = cnDict.get(key, '')
            cn = re.sub(r'\{.+?\}', r'', cn)
            self.contents.append([jp, cn])

    def load_from_file(self, path: Path):
        match path.suffix:
            case '.txt':
                with open(path, 'r', encoding = 'utf-8') as fp:
                    self._readTxt(fp.read())
            case '.xlsx':
                self._readExcel(path)
            case _:
                raise ValueError('Unsupported format.')
        
    def write(self, path: Path) -> None:
        self.outputPath = path
        match path.suffix:
            case '.txt': self._writeTXT()
            case '.xlsx': self._writeExcel()
            case _: raise ValueError('Unsupported format.')
    
    def _readExcel(self, path):
        excel = openpyxl.load_workbook(path)
        sheet = excel.active
        for line in sheet:
            content = [cell.value for cell in line ]
            match content:
                case jp, None, None:
                    c = [jp ,'#']
                case jp, None, comment:
                    c = [jp, f'#\\{comment}']
                case jp, cn, None:
                    c = [jp, cn]
                case jp, cn, comment:
                    c = [jp, f'{cn}\\{comment}']
                case jp, None:
                    c = [jp ,'#']
                case jp, cn:
                    c = [jp, cn]
            self.contents.append(c)

    def _writeTXT(self):
        with open(self.outputPath, 'w', encoding = 'utf-8') as fp:
            for jp, cn in self:
                fp.write(f'{cn}\n{jp}\n\n')
    
    def _writeExcel(self):
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        for jp, cn in self:
            try:
                cn, comment = cn.split('\\')
            except ValueError:
                comment = None
            if cn == '#':
                cn = None
            sheet.append([jp, cn, comment])
            workbook.save(self.outputPath)
            

if __name__ == '__main__':
    # path = Path(r'E:\Renaissance\翻译相关\KitaujiSub_TextProcessor\pysubGUI\test_files\[KitaujiSub] Kusuriya no Hitorigoto - 37.chs_jp.ass')
    # sub = Subtitle(path)
    # sub.pick('Text - CN', 'Text - JP')
    path = Path(r'E:\Renaissance\翻译相关\KitaujiSub_TextProcessor\pysubGUI\test_files\Example_TXT.txt')
    biling = BilingualText()
    biling.load_from_file(path)
    for line in biling.contents:
        print(line)
    # out = Path(r'E:\Renaissance\翻译相关\KitaujiSub_TextProcessor\pysubGUI\test_files\Example_TXT.xlsx')
    # biling.write(out)