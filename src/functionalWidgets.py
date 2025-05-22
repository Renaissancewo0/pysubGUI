import io
from contextlib import redirect_stdout

from config import Status
from mkvextractor import MkvSubExtractor
from subtitle import Subtitle
from textprocessor import TextProcessor, BilingualText

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QSizePolicy, QHeaderView,
    QDialog, QDialogButtonBox, QMessageBox, QTextEdit, QLineEdit,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout
)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from mainWindow import MainWindow


class MkvListWidget(QListWidget):
    def __init__(self, mainWindow: 'MainWindow'):
        super().__init__()
        self.mainWindow = mainWindow
        # Called when track row is selected
        self.currentRowChanged.connect(self.select_row)
        
        self.mkv = MkvSubExtractor(self.mainWindow.path)
        self.show_sub_tracks()
        
    def show_sub_tracks(self):
        # Get a list of subtitle tracks and display
        for track in self.mkv.subTracks:
            trackName = f'{self.mainWindow.path.stem}[{track["properties"]["language"]}][{track["properties"]["language_ietf"]}]'
            listItem = QListWidgetItem(trackName)
            listItem.setData(Qt.UserRole, (track['id'], track['codec']))
            self.addItem(listItem)
    
    def select_row(self, row):
        item = self.item(row)
        # Track name as the filename
        self.mainWindow.outputFilename.setText(item.text())
        # Initialize the format combo box
        self.mainWindow.outputFortmat.clear()
        match item.data(Qt.UserRole)[1]:
            case 'SubRip/SRT':
                self.mainWindow.outputFortmat.addItems(['.srt', '.txt'])
            case 'SubStationAlpha':
                self.mainWindow.outputFortmat.addItems(['.ass', '.txt'])
    
    def extract(self):
        path = self.mainWindow.constructOutputPath()
        original_path = path.with_suffix(self.mainWindow.outputFortmat.itemText(0))
        trackID = self.currentItem().data(Qt.UserRole)[0]
        self.mkv.extract_subtitle(trackID, original_path)
        
        # When extracted as *.txt, read the subtitle file and process its text 
        if path.suffix == '.txt':
            # itemText(0) for ass or srt, i.e., the format of subtitle file itselff
            self.mainWindow.path = original_path
            # Waiting for subtitle being fully extracted
            self.wait_for_file()
            # Call the function which handles subtitle
            self.mainWindow.read_subtitle()
            self.mainWindow.extract()
            
        
    def wait_for_file(self):
        timer = QTimer()
        timer.setInterval(200)
        def check():
            if self.mainWindow.path.exists():
                timer.stop()
        timer.timeout.connect(check)
        timer.start()    


class SubtitleDisplay(QWidget):
    def __init__(self, mainWindow: 'MainWindow'):
        super().__init__()
        self.mainWindow = mainWindow
        self.drawLayout()
        self.read_sub()

    def drawLayout(self):
        # Two text displaying area
        layout = QHBoxLayout()
        self.leftDisplay = QTextEdit()
        self.leftDisplay.setReadOnly(True)
        self.rightDisplay = QTextEdit()
        self.rightDisplay.setReadOnly(True)
        layout.addWidget(self.leftDisplay)
        layout.addWidget(self.rightDisplay)
        self.setLayout(layout)
        
    def read_sub(self):
        self.subtitle = Subtitle(self.mainWindow.path)
        if self.subtitle.path.suffix == '.ass':
            self.pick_styles()

        # For monolingual subtitle, text are waiting to be preprocessed
        if self.mainWindow.status == Status.MONOLINGUAL:
            self.mainWindow.extractButton.setText('提取字幕')
            # Show raw text and processed text
            self.leftDisplay.setPlainText(self.subtitle.raw_contents)
            self.textprocessor = TextProcessor(self.subtitle.extractText())
            self.rightDisplay.setPlainText(self.textprocessor.text)
            
            # Can only be extracted into .txt file
            self.mainWindow.outputFortmat.clear()
            self.mainWindow.outputFortmat.addItem('.txt')
        
    def extract(self):
        path = self.mainWindow.constructOutputPath()
        self.textprocessor.write(path)
        QMessageBox.information(self.mainWindow, '提示', '完成')
        
    def pick_styles(self):
        self.pickDialog = ChooseStyleDialog(self.mainWindow, self)
        self.pickDialog.exec()
        if self.subtitle.bilingual:
            self.mainWindow.status = Status.BILINGUAL


class BilingualTable(QTableWidget):
    def __init__(self, mainWindow: 'MainWindow'):
        super().__init__()
        self.mainWindow = mainWindow
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.load_text()
        self.show_text()
    
    def load_text(self):
        self.bilingualText = BilingualText()
        self.mainWindow.outputFortmat.clear()
        match self.mainWindow.path.suffix:
            case '.ass':
                self.bilingualText.load_from_ass(self.mainWindow.subtitleDisplay.subtitle)
                outputFomrmats = ['.xlsx', '.txt']
            case '.txt':
                self.bilingualText.load_from_file(self.mainWindow.path)
                outputFomrmats = ['.xlsx']
            case '.xlsx':
                self.bilingualText.load_from_file(self.mainWindow.path)
                outputFomrmats = ['.txt']
        self.mainWindow.outputFortmat.addItems(outputFomrmats)
        
    def show_text(self):
        rows = len(self.bilingualText)
        columns = 2
        self.setRowCount(rows)
        self.setColumnCount(columns)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        for row in range(rows):
            for column in range(columns):
                item = QTableWidgetItem(self.bilingualText[row][column])
                self.setItem(row, column, item)
    
    def extract(self):
        path = self.mainWindow.constructOutputPath()
        self.bilingualText.write(path)
        QMessageBox.information(self.mainWindow, '提示', '完成')


class InputFileLineEdit(QLineEdit):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        file_path = urls[0].toLocalFile()
        self.setText(file_path)
        event.acceptProposedAction()


class ChooseStyleDialog(QDialog):
    def __init__(self, parent: 'MainWindow', subReader: 'SubtitleDisplay'):
        super().__init__(parent)
        self.mainWindow = parent
        self.subReader = subReader
        
        self.setWindowTitle('选择需要读取的字幕样式')
        layout = QVBoxLayout()
        self.styleList = QListWidget()
        self.styleList.setSelectionMode(QListWidget.MultiSelection)
        self.styleList.addItems(self.subReader.subtitle.styles)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        
        layout.addWidget(self.styleList)
        layout.addWidget(self.buttons)
        self.setLayout(layout)
    
    def accept(self):
        pickedStyles = [item.text() for item in self.styleList.selectedItems()]
        self.subReader.subtitle.pick(pickedStyles)
        super().accept()

