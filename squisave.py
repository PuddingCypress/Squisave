import sys
import os
import zipfile
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence

class SquiSave(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lang = "zh"  # 默认中文
        self.setFixedSize(820, 680)
        self.task_name = "SquiSave_AutoBackup"
        self.source_dir = ""
        self.target_dir = ""
        self.config_file = "squisave_config.ini"
        self.log_file = "squisave_backup.log"

        self.setStyleSheet("""
            QMainWindow { background-color: #FFF7ED; }
            QLabel { font-size: 14px; color: #333; }
            QLineEdit { padding: 9px; border: 1px solid #E2B588; border-radius: 10px; background-color: #fff; }
            QPushButton { padding: 9px 16px; border-radius: 10px; background-color: #FF9F43; color: white; }
            QPushButton:hover { background-color: #FFAB5E; }
            QComboBox { padding: 9px; border-radius: 10px; border: 1px solid #E2B588; background-color: white; }
            QTextEdit { border-radius: 10px; border: 1px solid #E2B588; background-color: #fff; }
            QGroupBox { font-weight: bold; font-size: 16px; color: #FF7A00; }
        """)

        self.load_config()
        self.init_ui()
        self.init_shortcuts()
        self.load_log()

    # ==================== 多语言 ====================
    def tr(self, text):
        en = {
            "SquiSave Backup": "SquiSave Backup",
            "备份路径": "Backup Path",
            "源文件夹：": "Source:",
            "浏览": "Browse",
            "备份到：": "Target:",
            "自动任务": "Auto Task",
            "备份频率：": "Frequency:",
            "每天 12:00": "Daily 12:00",
            "每周一 12:00": "Weekly Mon 12:00",
            "每月1号 12:00": "Monthly 1st",
            "立即备份": "Backup Now",
            "创建任务": "Create Task",
            "查看任务": "View Task",
            "删除任务": "Delete Task",
            "日志": "Log",
            "错误": "Error",
            "请先选择源文件夹和目标文件夹": "Please select source and target folders",
            "成功": "Success",
            "备份完成！": "Backup Completed!",
            "备份失败：": "Backup Failed:",
            "定时任务已创建": "Task Created",
            "任务已删除": "Task Deleted",
            "创建任务失败": "Create Task Failed",
            "查看失败": "View Failed",
            "未找到任务": "No Task Found",
            "中文": "中文",
            "English": "English"
        }
        if self.lang == "en":
            return en.get(text, text)
        return text

    # ==================== 快捷键 ====================
    def init_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+B"), self, self.do_backup)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)

    # ==================== 界面 ====================
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(30,30,30,30)
        main.setSpacing(18)

        # 标题 + 语言切换
        top = QHBoxLayout()
        title = QLabel(self.tr("SquiSave Backup"))
        title.setStyleSheet("font-size:32px; font-weight:bold; color:#FF7A00;")
        self.lang_switch = QComboBox()
        self.lang_switch.addItems([self.tr("中文"), self.tr("English")])
        self.lang_switch.setCurrentText(self.tr("中文") if self.lang=="zh" else self.tr("English"))
        self.lang_switch.currentTextChanged.connect(self.change_lang)
        top.addWidget(title)
        top.addStretch()
        top.addWidget(self.lang_switch)
        main.addLayout(top)

        # 路径
        g1 = QGroupBox(self.tr("备份路径"))
        lay1 = QVBoxLayout(g1)
        self.source_edit = QLineEdit()
        self.target_edit = QLineEdit()
        btn_src = QPushButton(self.tr("浏览"))
        btn_tgt = QPushButton(self.tr("浏览"))
        btn_src.clicked.connect(self.browse_source)
        btn_tgt.clicked.connect(self.browse_target)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel(self.tr("源文件夹：")))
        row1.addWidget(self.source_edit)
        row1.addWidget(btn_src)
        lay1.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel(self.tr("备份到：")))
        row2.addWidget(self.target_edit)
        row2.addWidget(btn_tgt)
        lay1.addLayout(row2)
        main.addWidget(g1)

        # 任务
        g2 = QGroupBox(self.tr("自动任务"))
        lay2 = QGridLayout(g2)
        lay2.addWidget(QLabel(self.tr("备份频率：")), 0,0)
        self.mode_box = QComboBox()
        self.mode_box.addItems([
            self.tr("每天 12:00"),
            self.tr("每周一 12:00"),
            self.tr("每月1号 12:00")
        ])
        lay2.addWidget(self.mode_box, 0,1)

        self.btn_bk = QPushButton(self.tr("立即备份"))
        self.btn_create = QPushButton(self.tr("创建任务"))
        self.btn_view = QPushButton(self.tr("查看任务"))
        self.btn_del = QPushButton(self.tr("删除任务"))
        self.btn_bk.clicked.connect(self.do_backup)
        self.btn_create.clicked.connect(self.create_task)
        self.btn_view.clicked.connect(self.view_task)
        self.btn_del.clicked.connect(self.delete_task)
        lay2.addWidget(self.btn_bk,1,0)
        lay2.addWidget(self.btn_create,1,1)
        lay2.addWidget(self.btn_view,2,0)
        lay2.addWidget(self.btn_del,2,1)
        main.addWidget(g2)

        # 日志
        g3 = QGroupBox(self.tr("日志"))
        lay3 = QVBoxLayout(g3)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        lay3.addWidget(self.log_text)
        main.addWidget(g3)

        self.refresh_ui_text()
        self.setWindowTitle(self.tr("SquiSave Backup"))

    def change_lang(self, text):
        self.lang = "zh" if text == self.tr("中文") else "en"
        self.save_config()
        self.refresh_ui()

    def refresh_ui(self):
        self.close()
        self.__init__()
        self.show()

    def refresh_ui_text(self):
        self.source_edit.setText(self.source_dir)
        self.target_edit.setText(self.target_dir)

    # ==================== 日志 ====================
    def log(self, msg):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{now}] {msg}"
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except:
            pass
        self.log_text.append(line)

    def load_log(self):
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    self.log_text.setPlainText(f.read())
            except:
                pass

    # ==================== 配置 ====================
    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(f"source={self.source_dir}\n")
                f.write(f"target={self.target_dir}\n")
                f.write(f"lang={self.lang}\n")
        except:
            pass

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    for line in f.readlines():
                        if line.startswith("source="):
                            self.source_dir = line.strip().split("=",1)[1]
                        if line.startswith("target="):
                            self.target_dir = line.strip().split("=",1)[1]
                        if line.startswith("lang="):
                            self.lang = line.strip().split("=",1)[1]
            except:
                pass

    def browse_source(self):
        p = QFileDialog.getExistingDirectory()
        if p:
            self.source_dir = p
            self.source_edit.setText(p)
            self.save_config()

    def browse_target(self):
        p = QFileDialog.getExistingDirectory()
        if p:
            self.target_dir = p
            self.target_edit.setText(p)
            self.save_config()

    # ==================== ZIP 备份 ====================
    def do_backup(self):
        if not self.source_dir or not self.target_dir:
            QMessageBox.critical(self, self.tr("错误"), self.tr("请先选择源文件夹和目标文件夹"))
            return

        try:
            dt = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(self.target_dir, f"SquiSave_{dt}.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(self.source_dir):
                    for file in files:
                        full = os.path.join(root, file)
                        rel = os.path.relpath(full, self.source_dir)
                        zf.write(full, rel)

            self.log(self.tr("备份完成！"))
            QMessageBox.information(self, self.tr("成功"), self.tr("备份完成！"))
        except Exception as e:
            self.log(f"{self.tr('备份失败：')}{str(e)}")
            QMessageBox.critical(self, self.tr("错误"), f"{self.tr('备份失败：')}{str(e)}")

    # ==================== 任务 ====================
    def create_task(self):
        try:
            exe = sys.executable
            script = os.path.abspath(__file__)
            cmd = f'"{exe}" "{script}" -quiet'
            mode = self.mode_box.currentText()

            if mode == self.tr("每天 12:00"):
                c = f'schtasks /create /tn "{self.task_name}" /tr "{cmd}" /sc daily /st 12:00 /f'
            elif mode == self.tr("每周一 12:00"):
                c = f'schtasks /create /tn "{self.task_name}" /tr "{cmd}" /sc weekly /d mon /st 12:00 /f'
            else:
                c = f'schtasks /create /tn "{self.task_name}" /tr "{cmd}" /sc monthly /d 1 /st 12:00 /f'

            subprocess.run(c, shell=True, capture_output=True)
            self.log(self.tr("定时任务已创建"))
            QMessageBox.information(self, self.tr("成功"), self.tr("定时任务已创建"))
        except:
            QMessageBox.critical(self, self.tr("错误"), self.tr("创建任务失败"))

    def view_task(self):
        try:
            res = subprocess.run(f'schtasks /query /tn "{self.task_name}" /fo list /v',
                                 shell=True, capture_output=True)
            out = res.stdout.decode("gbk", errors="replace")
            if res.returncode !=0:
                out = self.tr("未找到任务")
            QMessageBox.information(self, "Task Info", out[:800])
        except:
            QMessageBox.critical(self, self.tr("错误"), self.tr("查看失败"))

    def delete_task(self):
        subprocess.run(f'schtasks /delete /tn "{self.task_name}" /f', shell=True)
        self.log(self.tr("任务已删除"))
        QMessageBox.information(self, self.tr("成功"), self.tr("任务已删除"))

# ==================== 静默模式 ====================
def silent_mode():
    app = QApplication(sys.argv)
    w = SquiSave()
    w.do_backup()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "-quiet":
        silent_mode()
    else:
        app = QApplication(sys.argv)
        w = SquiSave()
        w.show()
        sys.exit(app.exec_())