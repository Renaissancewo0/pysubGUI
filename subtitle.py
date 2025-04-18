from collections.abc import MutableSequence
from abc import abstractmethod
from typing import Iterator

import re
import itertools
import functools
import operator
from pathlib import Path
from collections import Counter

from timeline import Timeline


class Subtitle(MutableSequence):
    def __new__(cls, path: Path):
        '''Distribute the object into following subclasses'''
        match path.suffix:
            case '.ass': return super().__new__(ASSReader)
            case '.srt': return super().__new__(SRTReader)
            case '.vtt': return super().__new__(VTTReader)
            case _: raise ValueError('Unsupported format.')

    def __init__(self, path: Path):
        self.path = path
        self.contents: list[Timeline] = []
        self.bilingual = False
        
        with open(path, 'r', encoding = 'utf-8') as fp:
            self.raw_contents = fp.read()
        self.parse()

    # These five are the abstract methods in MutableSequence
    def __getitem__(self, key: int) -> Timeline:
        return self.contents[key]

    def __setitem__(self, key: int, value: Timeline) -> None:
        self.contents[key] = value

    def __delitem__(self, key: Timeline) -> None:
        del self.contents[key]

    def __iter__(self) -> Iterator[Timeline]:
        return iter(self.contents)

    def __len__(self) -> int:
        return len(self.contents)

    def insert(self, index: int, value: Timeline) -> None:
        return self.contents.insert(index, value)

    def sort(self, key = lambda x: x.start):
        self.contents.sort(key = key)

    @abstractmethod
    def parse(self):
        '''Parse the file to the form of Contents'''

    def extractText(self) -> str:
        self.sort()
        if self.bilingual:
            raise TypeError('Only for monolingual subtitle')
        return '\n'.join(line.text for line in self)


class ASSReader(Subtitle):
    timestamp = re.compile(r'.+?: \d,(\d:\d{2}:\d{2}[.]\d{2}),(\d:\d{2}:\d{2}[.]\d{2}),(.+?),,\d+,\d+,\d+,,(.+?)$')
    def __init__(self, path) -> None:
        super().__init__(path)

    def parse(self) -> None:
        # For ASS files, get all the existing styles. Waiting for a pick() method to dump them into self.contents.
        self.styles = re.findall(r'Style: (.+?),', self.raw_contents)

    def pick(self, styles: str) -> None:
        print(styles)
        self.styles = styles
        cn = 0
        jp = 0
        # Construct a dictionary for each picked style
        for style in self.styles:
            self.__dict__[style] = []
            if 'jp' in style.lower():
                jp += 1
            elif 'cn' in style.lower():
                cn += 1
        self.bilingual = bool(cn * jp)
        
        lines = self.raw_contents.split('\n\n')[-1].split('\n')[2:]
        for line in lines:
            # if results := re.search(self.timestamp, line):
            #     start, end, style, text = results.groups()
            try:
                _, start, end, style, *_, text = line.split(',')
                # Write the text, along with the timeline, into the dictionary specified by style
                if (stylelist := self.__dict__.get(style)) is not None:
                    line = Timeline(start, end, text)
                    stylelist.append(line)
            except ValueError:
                pass

        if not self.bilingual:
            for style in self.styles:
                self.extend(getattr(self, style))

class SRTReader(Subtitle):
    timestamp = re.compile(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.+?)\n\n', flags = re.DOTALL)
    def __init__(self, path) -> None:
        super().__init__(path)
        self.remove_repetitive_lines()
        
    def parse(self) -> None:
        for line in re.findall(self.timestamp, self.raw_contents):
            start, end, text = line
            text = SRTReader.tackleMultilines(text)
            self.append(Timeline(start, end, text))

    def remove_repetitive_lines(self) -> None:
        repetition = Counter(line.text for line in self)
        self.sort(key = lambda line: (repetition[line.text], line.text, line.start))

        mergedLines = []
        while (count := repetition[self.contents[-1].text]) > 1:
            self.contents, toBeMerged = self.contents[:-count], self.contents[-count:]
            mergedLines += SRTReader.merge_lines(toBeMerged)
        self.contents += mergedLines
        self.sort()

    @staticmethod
    def merge_lines(lines: list[Timeline]) -> list[Timeline]:
        isContinuous = lambda x, y: x.end == y.start
        flags = [isContinuous(*pair) for pair in itertools.pairwise(lines)]
        idx = 0
        for flag, counts in itertools.groupby(flags):
            count = len(list(counts))
            if flag:
                lines[idx:idx+count+1] = [lines[idx].merge(lines[idx+count])]
            idx += count
        return lines

    @staticmethod
    def tackleMultilines(text: str) -> str:
        lines = text.split('\n')
        # Single line
        if len(lines) == 1:
            return text
        # Eliminate distractions
        striped = []
        patterns = ['\u200E', '&lrm;', '&nbsp;', r'<.*?>', r'\{.*?\}']
        for line in lines:
            for pattern in patterns:
                line = re.sub(pattern, '', line)
            striped.append(line)
        # Case for multiple speakers
        if striped[0][0] in ('(', '（') and functools.reduce(operator.eq, (line[0] for line in striped)):
            return '　-'.join(lines)
        return '　'.join(lines)


class VTTReader(SRTReader):
    timestamp = re.compile(r'(\d{2}:\d{2}:\d{2}[.]\d{3}) --> (\d{2}:\d{2}:\d{2}[.]\d{3}) .+?\n(.*?)\n\n', re.DOTALL)
    def __init__(self, path) -> None:
        super().__init__(path)


if __name__ == '__main__':
    path = Path(r'E:\Renaissance\翻译相关\KitaujiSub_TextProcessor\pysubGUI\test_files\[KitaujiSub] Kusuriya no Hitorigoto - 37.chs_jp.ass')
    x = Subtitle(path)
    x.pick(['Text - CN', 'Text - JP'])
    c = x.cast2BilingualText()
    print(c.jp)
