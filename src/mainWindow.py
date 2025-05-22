from pathlib import Path
from config import Status
from functionalWidgets import (
    MkvListWidget, SubtitleDisplay, BilingualTable
)
from PySide6.QtWidgets import (
    QApplication, QWidget, QSpacerItem, QSizePolicy,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QListWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QStackedLayout
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setupMainWindow()
        self.path = None
        self.status = Status.SUSPEND

    def setupMainWindow(self):
        # Set window properties
        self.setWindowTitle('KitaujiSub')
        self.setGeometry(100, 100, 720, 480)
        QApplication.instance().setStyleSheet("QLabel{min-width: 80px;}")
        self.overallLayout = QVBoxLayout()
        
        # Create widgets for reading input filename
        toplayout = QHBoxLayout()
        label = QLabel('读取文件路径')
        self.inputFile = QLineEdit()
        inputFileButton = QPushButton('浏览')
        inputFileButton.setFixedSize(80, 24)
        inputFileButton.clicked.connect(self.readInputFile)
        toplayout.addWidget(label)
        toplayout.addWidget(self.inputFile)
        toplayout.addWidget(inputFileButton)
        self.overallLayout.addLayout(toplayout)
        
        # Create a label for display tips
        self.tipLabel = QLabel('    点击【载入文件】以读取文件内容')
        self.tipLabel.setStyleSheet('font-size: 16px;')
        self.overallLayout.addWidget(self.tipLabel)

        # Create a central layout using a stack
        self.mainLayout = QStackedLayout()
        # A list widget that does nothing, but only a placeholder
        self.mainLayout.addWidget(QListWidget())
        self.overallLayout.addLayout(self.mainLayout)
    
        # Create widgets for setting output file
        # For file directory
        fileDirLayout = QHBoxLayout()
        self.outputFileDir = QLineEdit()
        outputFileButton = QPushButton('浏览')
        outputFileButton.setFixedSize(80, 24)
        outputFileButton.clicked.connect(self.readOutputFile)
        # For filename
        filenameLayout = QHBoxLayout()
        self.outputFilename = QLineEdit()
        self.outputFortmat = QComboBox()
        self.outputFortmat.setFixedSize(80, 24)
        # Add them to layouts
        fileDirLayout.addWidget(QLabel('输出文件夹'))
        fileDirLayout.addWidget(self.outputFileDir)
        fileDirLayout.addWidget(outputFileButton)
        filenameLayout.addWidget(QLabel('文件名'))
        filenameLayout.addWidget(self.outputFilename)
        filenameLayout.addWidget(self.outputFortmat)
        self.overallLayout.addLayout(fileDirLayout)
        self.overallLayout.addLayout(filenameLayout)
        
        # Create functional buttons
        bottomLayout = QHBoxLayout()
        self.loadButton = QPushButton('载入文件')
        self.loadButton.clicked.connect(self.load)
        self.loadButton.setFixedSize(80, 24)
        self.extractButton = QPushButton('提取文件')
        self.extractButton.clicked.connect(self.extract)
        self.extractButton.setFixedSize(80, 24)
        bottomLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        bottomLayout.addWidget(self.loadButton)
        bottomLayout.addWidget(self.extractButton)
        self.overallLayout.addLayout(bottomLayout)
        
        self.setLayout(self.overallLayout)

    def readInputFile(self):
        filefilter = ['所有文件 (*)',
                      'Matroska多媒体容器 (*.mkv)',
                      '字幕文件 (*.ass *.srt *.vtt)',
                      '文本文件 (*.txt)',
                      'Excel 工作簿 (*.xlsx)']
        path = QFileDialog.getOpenFileName(self, '选择文件', '', ';;'.join(filefilter))
        if path:
            self.inputFile.setText(path[0])
    
    def readOutputFile(self):
        path = QFileDialog.getExistingDirectory(self, '选择输出目录', '', QFileDialog.ShowDirsOnly)
        if path:
            self.outputFileDir.setText(path[0])
        
    def constructOutputPath(self) -> Path:
        directory = self.outputFileDir.text()
        filename = self.outputFilename.text()
        fmt = self.outputFortmat.currentText()
        return Path(f'{directory}\\{filename}{fmt}')
    
    def load(self):
        # Check if path is available
        if (path :=self.inputFile.text()):
            self.path = Path(path)
        if (self.path is None) or (not self.path.exists()):
            QMessageBox.warning(self, 'Warning', '请选择正确的文件路径')
            return

        self.format = self.path.suffix
        match self.format:
            case '.mkv':
                self.create_mkvLoader()
            case '.ass'|'.srt'|'.vtt':
                self.read_subtitle()
            case '.txt'|'.xlsx':
                self.read_bilingual_text()
            case _:
                QMessageBox.warning(self, 'Warning', '不受支持的格式')
        
        # Set a default output filename
        self.outputFileDir.setText(str(self.path.parent))
        self.outputFilename.setText(self.path.stem)
        
    def extract(self):
        # Check if any file has been loaded
        try:
            getattr(self, 'format')
        except AttributeError:
            QMessageBox.warning(self, 'Warning', '请先加载文件')
            return

        match self.status:
            case Status.MKV:
                self.mkvList.extract()
            case Status.MONOLINGUAL:
                self.subtitleDisplay.extract()
            case Status.BILINGUAL:
                self.bilingualTable.extract()
            case Status.SUSPEND:
                pass
    
    def create_mkvLoader(self):
        self.status = Status.MKV
        self.mkvList = MkvListWidget(self)
        self.extractButton.setText('提取文件')
        self.mainLayout.addWidget(self.mkvList)
        self.mainLayout.setCurrentWidget(self.mkvList)
        self.tipLabel.setText('    提示：输出格式选择.txt时，将自动对字幕进行预处理')
        
    def read_subtitle(self):
        self.extractButton.setText('输出字幕')
        self.tipLabel.setText('')
        self.status = Status.MONOLINGUAL
        
        self.subtitleDisplay = SubtitleDisplay(self)
        if self.status == Status.MONOLINGUAL:
            self.mainLayout.addWidget(self.subtitleDisplay)
            self.mainLayout.setCurrentWidget(self.subtitleDisplay)
        if self.status == Status.BILINGUAL:
            self.read_bilingual_text()
    
    def read_bilingual_text(self):
        self.extractButton.setText('输出字幕')
        self.tipLabel.setText('')
        self.status = Status.BILINGUAL
        self.bilingualTable = BilingualTable(self)
        self.mainLayout.addWidget(self.bilingualTable)
        self.mainLayout.setCurrentWidget(self.bilingualTable)

