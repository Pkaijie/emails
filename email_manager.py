"""
邮箱账号管理程序
================

功能概览：
    1. 手动添加邮箱并记录到本地 JSON 文件 (emails.json)
    2. 在已有邮箱的 @ 之前随机添加后缀，生成不重复的新邮箱
    3. 邮箱有「可用」/「封禁」两种状态，可单条或批量切换
    4. 表格分页展示，固定每页 PAGE_SIZE 条，避免滚动
    5. 表格中的邮箱地址、基础邮箱可点击直接复制到剪贴板
    6. 全部数据自动持久化到脚本同目录的 emails.json

依赖：PyQt5
运行：python email_manager.py
"""

import json
import os
import random
import signal
import string
import sys

# PyQt5 控件类
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QGraphicsDropShadowEffect, QAbstractItemView, QCheckBox
)
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

# ===================== 全局常量 =====================
# 数据文件存放在脚本同目录下，使用 JSON 格式持久化
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emails.json")

# 邮箱状态常量（同时也直接展示在界面上）
STATUS_AVAILABLE = "可用"
STATUS_BANNED = "封禁"

# 表格分页：每页固定显示多少条记录
PAGE_SIZE = 10

# ===================== 界面样式表（QSS） =====================
# QSS 类似 CSS，用于美化 PyQt 界面。下方按控件类型/对象名分块定义。
STYLE_SHEET = """
QWidget#mainWindow {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #667eea, stop:0.5 #764ba2, stop:1 #f093fb);
}

QWidget {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}

QGroupBox {
    background-color: rgba(255, 255, 255, 0.95);
    border: none;
    border-radius: 16px;
    margin-top: 25px;
    padding: 20px;
    padding-top: 35px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 15px;
    top: 5px;
    padding: 5px 15px;
    color: white;
    font-size: 15px;
    font-weight: bold;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    border-radius: 8px;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 10px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #2980b9;
}

QPushButton:pressed {
    background-color: #1c6ea4;
}

QPushButton#generateBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #f093fb, stop:0.5 #f5576c, stop:1 #f093fb);
    font-size: 15px;
    padding: 12px;
}

QPushButton#generateBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #ec77f0, stop:0.5 #e34055, stop:1 #ec77f0);
}

QPushButton#dangerBtn {
    background-color: #e74c3c;
    padding: 6px 14px;
    font-size: 13px;
    border-radius: 8px;
}

QPushButton#dangerBtn:hover {
    background-color: #c0392b;
}

QPushButton#toggleBtn {
    background-color: #f39c12;
    padding: 6px 14px;
    font-size: 13px;
    border-radius: 8px;
}

QPushButton#toggleBtn:hover {
    background-color: #d68910;
}

QPushButton#copyBtn {
    background-color: #8e44ad;
    padding: 4px 10px;
    font-size: 12px;
    border-radius: 6px;
    min-width: 50px;
}

QPushButton#copyBtn:hover {
    background-color: #71368a;
}

/* 可点击复制的文本单元格：默认透明，悬停时浅蓝高亮 */
QLabel#copyableLabel {
    font-size: 13px;
    color: #2c3e50;
    padding: 6px 10px;
    border-radius: 6px;
    background-color: transparent;
}

QLabel#copyableLabel:hover {
    background-color: #eaf0ff;
    color: #4a5fd1;
}

QPushButton#batchBtn {
    background-color: #16a085;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton#batchBtn:hover {
    background-color: #117a65;
}

QPushButton#pagerBtn {
    background-color: #34495e;
    padding: 8px 18px;
    font-size: 13px;
}

QPushButton#pagerBtn:hover {
    background-color: #2c3e50;
}

QPushButton#pagerBtn:disabled {
    background-color: #bdc3c7;
    color: #ecf0f1;
}

QLabel#pageLabel {
    font-size: 14px;
    font-weight: bold;
    color: #2c3e50;
    padding: 0 10px;
}

/* 自定义复选框样式：圆角方框，选中时填充主题紫色 */
QCheckBox::indicator {
    width: 22px;
    height: 22px;
    border: 2px solid #b0b0b0;
    border-radius: 5px;
    background-color: white;
}

QCheckBox::indicator:hover {
    border-color: #667eea;
}

QCheckBox::indicator:checked {
    background-color: #667eea;
    border: 2px solid #667eea;
    image: none;
}

/* 三个统计标签：使用不同背景色 */
QLabel#statTotal, QLabel#statAvailable, QLabel#statBanned {
    font-size: 14px;
    font-weight: bold;
    padding: 6px 16px;
    border-radius: 8px;
    color: white;
}

QLabel#statTotal {
    background-color: #5b6ee1;
}

QLabel#statAvailable {
    background-color: #27ae60;
}

QLabel#statBanned {
    background-color: #c0392b;
}

QLineEdit, QSpinBox {
    border: 2px solid #dcdcdc;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    background-color: white;
}

QLineEdit:focus, QSpinBox:focus {
    border: 2px solid #667eea;
}

QLabel#titleLabel {
    font-size: 26px;
    font-weight: bold;
    color: white;
    padding: 12px;
    background: transparent;
}

QLabel.fieldLabel {
    font-size: 14px;
    color: #2c3e50;
    font-weight: bold;
}

QTableWidget {
    background-color: white;
    border: 1px solid #dcdcdc;
    border-radius: 8px;
    gridline-color: #ecf0f1;
    font-size: 13px;
}

QTableWidget::item {
    padding: 6px;
}

QTableWidget::item:selected {
    background-color: #d6e9ff;
    color: #2c3e50;
}

QHeaderView::section {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #667eea, stop:1 #764ba2);
    color: white;
    padding: 8px;
    border: none;
    font-weight: bold;
    font-size: 13px;
}

QMessageBox {
    background-color: white;
}

QMessageBox QLabel {
    color: #2c3e50;
    font-size: 14px;
}

QMessageBox QPushButton {
    min-width: 80px;
    min-height: 30px;
}
"""


# ===================== 数据持久化辅助函数 =====================

def load_emails() -> list[dict]:
    """从 DATA_FILE 读取邮箱列表。

    返回值：包含若干 dict 的列表，每个 dict 形如
        {"email": "user@example.invalid", "status": "可用", "base": "user@example.invalid"}

    若文件不存在、内容损坏、或某条记录缺少 email 字段，都做兼容处理：
    - 文件不存在 / 解析失败：返回空列表
    - 单条记录非 dict 或缺 email：跳过该条
    """
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # JSON 损坏或读取失败，等同于空数据，避免直接抛异常崩溃
        return []
    return [item for item in data if isinstance(item, dict) and "email" in item]


def save_emails(emails: list[dict]) -> None:
    """将邮箱列表写回 DATA_FILE。

    使用 ensure_ascii=False 让中文等字符保持原样，indent=2 便于人工查看。
    """
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(emails, f, ensure_ascii=False, indent=2)


def split_email(email: str) -> tuple[str, str]:
    """把邮箱按最后一个 @ 拆分为 (local, domain)。

    例如 "user@example.invalid" -> ("user", "example.invalid")。
    若格式非法（缺 @、@ 两边为空）则抛 ValueError，由调用方提示用户。
    """
    if "@" not in email:
        raise ValueError("邮箱必须包含 @ 符号")
    # rpartition 从右往左找最后一个 @，避免本地名里包含 @ 的怪情况影响拆分
    local, _, domain = email.rpartition("@")
    if not local or not domain:
        raise ValueError("邮箱格式无效")
    return local, domain


def generate_random_email(base_email: str, existing: set[str],
                          suffix_length: int, max_attempts: int = 2000) -> str:
    """根据基础邮箱随机生成不重复的新邮箱。

    参数：
        base_email: 基础邮箱，例如 "user@example.invalid"
        existing:   已经存在的全部邮箱地址集合，用于去重
        suffix_length: 在 @ 之前要追加的随机后缀长度
        max_attempts:  最多尝试多少次仍冲突，则放弃并抛错

    生成规则：
        local + 随机后缀 + "@" + domain
        随机后缀字符集为小写字母 + 数字
        例：base="user@example.invalid", suffix_length=2 -> 可能得到 "user@example.invalid"
    """
    local, domain = split_email(base_email)
    chars = string.ascii_lowercase + string.digits
    for _ in range(max_attempts):
        # random.choices 允许重复抽样，正好符合"随机字符串"需求
        suffix = "".join(random.choices(chars, k=suffix_length))
        new_email = f"{local}{suffix}@{domain}"
        if new_email not in existing:
            return new_email
    # 重复次数太多说明可选空间太小，提示用户加大长度
    raise RuntimeError("已尝试多次仍无法生成不重复的邮箱，请增加后缀长度")


# ===================== 自定义控件 =====================

class ClickableLabel(QLabel):
    """支持左键点击事件的标签控件。

    PyQt 自带的 QLabel 默认不发射 clicked 信号，因此这里继承一下并：
    1) 定义一个 clicked 信号
    2) 在 mousePressEvent 中识别左键并发射该信号
    供"邮箱地址"和"基础邮箱"两列实现"点击直接复制"。
    """
    clicked = pyqtSignal()

    def mousePressEvent(self, event):
        # 仅响应鼠标左键，右键/中键不触发复制，避免误操作
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        # 仍然把事件交给父类，保留默认行为（选中/聚焦等）
        super().mousePressEvent(event)


# ===================== 主窗口 =====================

class EmailManagerWindow(QWidget):
    """邮箱管理主窗口。

    重要属性：
        self.emails:        全部邮箱记录的列表（来自 emails.json）
        self.current_page:  当前展示的页码，从 0 开始
        self.row_checkboxes: 当前页 PAGE_SIZE 个 QCheckBox 引用，用于批量操作
                            空行的位置存 None，便于按可视行索引一一对应
    """

    def __init__(self):
        super().__init__()
        # 启动时读入历史数据
        self.emails: list[dict] = load_emails()
        self.current_page = 0
        self.row_checkboxes: list[QCheckBox | None] = []
        # 先构建界面，再触发一次刷新填充表格和统计
        self.init_ui()
        self.refresh_table()

    # ---------- 通用工具 ----------

    def total_pages(self) -> int:
        """根据邮箱总数计算总页数（向上取整），最少返回 1，避免空列表时显示 0/0。"""
        return max(1, (len(self.emails) + PAGE_SIZE - 1) // PAGE_SIZE)

    def add_shadow(self, widget):
        """给指定控件添加柔和阴影，让 GroupBox 浮起来。"""
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))  # 半透明黑色
        widget.setGraphicsEffect(shadow)

    # ---------- 界面构建 ----------

    def init_ui(self):
        """构建整体界面结构。"""
        self.setWindowTitle("邮箱账号管理")
        self.setObjectName("mainWindow")  # 用于 QSS 选择器 #mainWindow
        self.setStyleSheet(STYLE_SHEET)
        self.resize(820, 780)

        # 主布局：标题 + 三个 GroupBox
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(25, 20, 25, 20)

        title = QLabel("📧 邮箱账号管理")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # 三块功能区
        main_layout.addWidget(self._build_add_group())
        main_layout.addWidget(self._build_generate_group())
        main_layout.addWidget(self._build_table_group(), stretch=1)

        self.setLayout(main_layout)

    def _build_add_group(self) -> QGroupBox:
        """「手动添加邮箱」区域：一个输入框 + 添加按钮。"""
        group = QGroupBox("手动添加邮箱")
        self.add_shadow(group)

        layout = QHBoxLayout()
        layout.setSpacing(10)

        label = QLabel("邮箱地址：")
        label.setProperty("class", "fieldLabel")
        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("例如 user@example.invalid")
        # 在输入框中按回车也触发添加，提升录入效率
        self.add_input.returnPressed.connect(self.on_add_email)

        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self.on_add_email)

        layout.addWidget(label)
        layout.addWidget(self.add_input, stretch=1)
        layout.addWidget(add_btn)

        group.setLayout(layout)
        return group

    def _build_generate_group(self) -> QGroupBox:
        """「随机生成邮箱」区域：基础邮箱 + 后缀长度 + 生成按钮。"""
        group = QGroupBox("随机生成邮箱（在 @ 前添加随机后缀）")
        self.add_shadow(group)

        # 外层垂直布局：第一行参数，第二行大按钮
        outer = QVBoxLayout()
        outer.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(10)

        base_label = QLabel("基础邮箱：")
        base_label.setProperty("class", "fieldLabel")
        self.base_input = QLineEdit()
        self.base_input.setPlaceholderText("例如 user@example.invalid")

        len_label = QLabel("后缀长度：")
        len_label.setProperty("class", "fieldLabel")
        # 后缀长度限制在 1~10，避免过短全冲突或过长无意义
        self.length_spin = QSpinBox()
        self.length_spin.setRange(1, 10)
        self.length_spin.setValue(2)
        self.length_spin.setFixedWidth(70)

        row.addWidget(base_label)
        row.addWidget(self.base_input, stretch=1)
        row.addWidget(len_label)
        row.addWidget(self.length_spin)

        gen_btn = QPushButton("🎲 生成并保存为可用")
        gen_btn.setObjectName("generateBtn")
        gen_btn.clicked.connect(self.on_generate_email)

        outer.addLayout(row)
        outer.addWidget(gen_btn)
        group.setLayout(outer)
        return group

    def _build_table_group(self) -> QGroupBox:
        """「已记录邮箱」区域：统计行 + 批量操作行 + 表格 + 分页行。"""
        group = QGroupBox("已记录邮箱")
        self.add_shadow(group)

        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ---- 统计行：总数 / 可用 / 封禁 ----
        stats_row = QHBoxLayout()
        stats_row.setSpacing(10)
        self.total_label = QLabel()
        self.total_label.setObjectName("statTotal")
        self.available_label = QLabel()
        self.available_label.setObjectName("statAvailable")
        self.banned_label = QLabel()
        self.banned_label.setObjectName("statBanned")
        stats_row.addWidget(self.total_label)
        stats_row.addWidget(self.available_label)
        stats_row.addWidget(self.banned_label)
        stats_row.addStretch()  # 把后面的空白推到右侧
        layout.addLayout(stats_row)

        # ---- 批量操作行：全选 / 批量封禁 / 批量恢复 / 批量删除 ----
        batch_row = QHBoxLayout()
        batch_row.setSpacing(8)
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.setObjectName("batchBtn")
        self.select_all_btn.setCursor(Qt.PointingHandCursor)
        self.select_all_btn.clicked.connect(self.on_toggle_select_all)

        batch_ban_btn = QPushButton("批量封禁")
        batch_ban_btn.setObjectName("toggleBtn")
        batch_ban_btn.setCursor(Qt.PointingHandCursor)
        batch_ban_btn.clicked.connect(self.on_batch_ban)

        batch_unban_btn = QPushButton("批量恢复")
        batch_unban_btn.setObjectName("batchBtn")
        batch_unban_btn.setCursor(Qt.PointingHandCursor)
        batch_unban_btn.clicked.connect(self.on_batch_unban)

        batch_del_btn = QPushButton("批量删除")
        batch_del_btn.setObjectName("dangerBtn")
        batch_del_btn.setCursor(Qt.PointingHandCursor)
        batch_del_btn.clicked.connect(self.on_batch_delete)

        batch_row.addWidget(self.select_all_btn)
        batch_row.addWidget(batch_ban_btn)
        batch_row.addWidget(batch_unban_btn)
        batch_row.addWidget(batch_del_btn)
        batch_row.addStretch()
        layout.addLayout(batch_row)

        # ---- 表格 ----
        # 5 列：选择 / 邮箱地址 / 基础邮箱 / 状态 / 操作
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["选择", "邮箱地址", "基础邮箱", "状态", "操作"]
        )
        self.table.verticalHeader().setVisible(False)  # 隐藏行号
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)  # 禁止编辑
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(52)  # 行高
        # 固定表格高度：表头 ≈ 40px + PAGE_SIZE 行 × 52px + 一点边距
        # 这样不论当前页有多少条，表格都不会变高变低，视觉稳定
        self.table.setFixedHeight(40 + PAGE_SIZE * 52 + 4)
        # 列宽策略：邮箱地址 / 基础邮箱 撑满，剩余三列固定宽度
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 220)

        layout.addWidget(self.table)

        # ---- 分页行：上一页 / 页码标签 / 下一页 ----
        pager_row = QHBoxLayout()
        pager_row.setSpacing(8)
        self.prev_btn = QPushButton("◀ 上一页")
        self.prev_btn.setObjectName("pagerBtn")
        self.prev_btn.setCursor(Qt.PointingHandCursor)
        self.prev_btn.clicked.connect(self.on_prev_page)

        self.page_label = QLabel("第 1 / 1 页")
        self.page_label.setObjectName("pageLabel")
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setMinimumWidth(120)

        self.next_btn = QPushButton("下一页 ▶")
        self.next_btn.setObjectName("pagerBtn")
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.clicked.connect(self.on_next_page)

        # 两侧 stretch 让分页控件居中
        pager_row.addStretch()
        pager_row.addWidget(self.prev_btn)
        pager_row.addWidget(self.page_label)
        pager_row.addWidget(self.next_btn)
        pager_row.addStretch()
        layout.addLayout(pager_row)

        group.setLayout(layout)
        return group

    # ---------- 业务逻辑 ----------

    def existing_addresses(self) -> set[str]:
        """返回当前所有已记录邮箱的集合，用于查重。"""
        return {item["email"] for item in self.emails}

    def on_add_email(self):
        """处理「手动添加邮箱」按钮 / 回车。"""
        email = self.add_input.text().strip()
        if not email:
            self._warn("请输入邮箱地址")
            return
        # 校验格式
        try:
            split_email(email)
        except ValueError as e:
            self._warn(str(e))
            return
        # 校验重复
        if email in self.existing_addresses():
            self._warn("该邮箱已存在")
            return

        # 手动添加时，base 字段就等于邮箱本身
        self.emails.append({
            "email": email,
            "status": STATUS_AVAILABLE,
            "base": email,
        })
        save_emails(self.emails)
        self.add_input.clear()
        # 跳到末页让用户立刻看到刚添加的记录
        self.current_page = self.total_pages() - 1
        self.refresh_table()

    def on_generate_email(self):
        """处理「随机生成邮箱」按钮。"""
        base = self.base_input.text().strip()
        if not base:
            self._warn("请输入基础邮箱")
            return
        try:
            split_email(base)
        except ValueError as e:
            self._warn(str(e))
            return

        try:
            new_email = generate_random_email(
                base, self.existing_addresses(), self.length_spin.value()
            )
        except RuntimeError as e:
            self._warn(str(e))
            return

        # base 字段保留输入的基础邮箱，方便表格中显示和后续追溯
        self.emails.append({
            "email": new_email,
            "status": STATUS_AVAILABLE,
            "base": base,
        })
        save_emails(self.emails)
        self.current_page = self.total_pages() - 1
        self.refresh_table()
        QMessageBox.information(self, "生成成功", f"已生成新邮箱：\n{new_email}")

    def on_toggle_status(self, index: int):
        """切换单条邮箱的状态：可用 <-> 封禁。"""
        if not 0 <= index < len(self.emails):
            return
        current = self.emails[index]["status"]
        self.emails[index]["status"] = (
            STATUS_BANNED if current == STATUS_AVAILABLE else STATUS_AVAILABLE
        )
        save_emails(self.emails)
        self.refresh_table()

    def on_delete(self, index: int):
        """删除单条邮箱（带二次确认）。"""
        if not 0 <= index < len(self.emails):
            return
        email = self.emails[index]["email"]
        confirm = QMessageBox.question(
            self, "删除确认", f"确定要删除邮箱 {email} 吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        self.emails.pop(index)
        save_emails(self.emails)
        self.refresh_table()

    # ---------- 表格刷新 ----------

    def refresh_table(self):
        """重新计算统计数据、当前页内容并刷新到界面。

        被多个增删改操作调用，是界面与数据同步的中心点。
        """
        # 总体统计始终基于全部数据，与当前页无关
        total = len(self.emails)
        available_count = sum(
            1 for e in self.emails if e.get("status") == STATUS_AVAILABLE
        )
        banned_count = total - available_count

        # 校正当前页码：删除后可能让最后一页变空，需要回退一页
        last_page = self.total_pages() - 1
        if self.current_page > last_page:
            self.current_page = last_page
        if self.current_page < 0:
            self.current_page = 0

        # 计算本页应显示的数据切片 [start, end)
        start = self.current_page * PAGE_SIZE
        end = min(start + PAGE_SIZE, total)
        page_count = end - start

        # 始终把表格行数固定为 PAGE_SIZE，不足部分用空行占位
        # 这样上一页/下一页时表格高度保持一致，体验更稳定
        self.table.setRowCount(PAGE_SIZE)
        self.row_checkboxes = []

        for visual_row in range(PAGE_SIZE):
            if visual_row < page_count:
                # 当前 visual_row 对应的全局索引 = 起始索引 + 行号
                absolute_index = start + visual_row
                item = self.emails[absolute_index]
                self._render_row(visual_row, absolute_index, item)
            else:
                self._render_empty_row(visual_row)

        # 更新统计标签
        self.total_label.setText(f"📊 总数：{total}")
        self.available_label.setText(f"✅ 可用：{available_count}")
        self.banned_label.setText(f"🚫 封禁：{banned_count}")
        # 更新页码与翻页按钮的可用状态
        self.page_label.setText(f"第 {self.current_page + 1} / {self.total_pages()} 页")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < last_page)
        # 刷新后默认未选中任何行，按钮文字回到「全选」
        self.select_all_btn.setText("全选")

    def _render_row(self, visual_row: int, absolute_index: int, item: dict):
        """绘制一行实际数据。

        参数：
            visual_row:     当前页内的可视行号（0~PAGE_SIZE-1）
            absolute_index: 在 self.emails 中的全局索引（按钮回调用它定位记录）
            item:           {"email": ..., "status": ..., "base": ...}
        """
        # ----- 第 0 列：复选框（居中放置） -----
        cb_container = QWidget()
        cb_layout = QHBoxLayout(cb_container)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        cb_layout.setAlignment(Qt.AlignCenter)
        checkbox = QCheckBox()
        checkbox.setCursor(Qt.PointingHandCursor)
        cb_layout.addWidget(checkbox)
        self.table.setCellWidget(visual_row, 0, cb_container)
        # 把复选框引用按可视行顺序记录下来，供批量操作读取
        self.row_checkboxes.append(checkbox)

        email = item["email"]
        base_email = self._derive_base_email(email)

        # ----- 第 1 列：邮箱地址（点击复制） -----
        self.table.setCellWidget(
            visual_row, 1, self._build_copyable_cell(email)
        )

        # ----- 第 2 列：基础邮箱（点击复制） -----
        self.table.setCellWidget(
            visual_row, 2, self._build_copyable_cell(base_email)
        )

        # ----- 第 3 列：状态（不同颜色文字） -----
        status = item.get("status", STATUS_AVAILABLE)
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignCenter)
        if status == STATUS_AVAILABLE:
            status_item.setForeground(QColor("#27ae60"))  # 绿
        else:
            status_item.setForeground(QColor("#c0392b"))  # 红
        self.table.setItem(visual_row, 3, status_item)

        # ----- 第 4 列：操作按钮（封禁/恢复 + 删除） -----
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(8, 4, 8, 4)
        action_layout.setSpacing(8)

        toggle_btn = QPushButton(
            "封禁" if status == STATUS_AVAILABLE else "恢复"
        )
        toggle_btn.setObjectName("toggleBtn")
        toggle_btn.setMinimumSize(80, 36)
        toggle_btn.setCursor(Qt.PointingHandCursor)
        # 用默认参数 i=absolute_index 把当前索引"冻结"到 lambda 中，
        # 否则循环结束后所有 lambda 都会引用循环结束时的同一个索引。
        toggle_btn.clicked.connect(
            lambda _checked, i=absolute_index: self.on_toggle_status(i)
        )

        del_btn = QPushButton("删除")
        del_btn.setObjectName("dangerBtn")
        del_btn.setMinimumSize(80, 36)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(
            lambda _checked, i=absolute_index: self.on_delete(i)
        )

        action_layout.addWidget(toggle_btn)
        action_layout.addWidget(del_btn)
        self.table.setCellWidget(visual_row, 4, action_widget)

    def _render_empty_row(self, visual_row: int):
        """绘制一行"占位空行"，保持表格高度恒定。"""
        # 用空 QWidget / 空 Item 覆盖任何残留的旧控件
        self.table.setCellWidget(visual_row, 0, QWidget())
        self.table.setCellWidget(visual_row, 1, QWidget())
        self.table.setCellWidget(visual_row, 2, QWidget())
        self.table.setItem(visual_row, 3, QTableWidgetItem(""))
        self.table.setCellWidget(visual_row, 4, QWidget())
        # 空行没有复选框，对应位置存 None，方便 _selected_indices 跳过
        self.row_checkboxes.append(None)

    # ---------- 批量操作 / 翻页 ----------

    def _selected_indices(self) -> list[int]:
        """返回当前页中被勾选的记录在 self.emails 里的全局索引列表。"""
        start = self.current_page * PAGE_SIZE
        return [
            start + i for i, cb in enumerate(self.row_checkboxes)
            if cb is not None and cb.isChecked()
        ]

    def on_toggle_select_all(self):
        """全选/取消全选切换：根据当前页所有非空复选框是否都已勾选来决定。"""
        valid = [cb for cb in self.row_checkboxes if cb is not None]
        if not valid:
            return
        # 当前是否全部勾选？是则下一步取消，否则全选
        target = not all(cb.isChecked() for cb in valid)
        for cb in valid:
            cb.setChecked(target)
        self.select_all_btn.setText("取消全选" if target else "全选")

    def on_prev_page(self):
        """上一页（首页时按钮应已禁用，这里再次校验作保险）。"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_table()

    def on_next_page(self):
        """下一页（末页时按钮应已禁用，这里再次校验作保险）。"""
        if self.current_page < self.total_pages() - 1:
            self.current_page += 1
            self.refresh_table()

    def on_batch_ban(self):
        """批量将勾选项设置为「封禁」。"""
        indices = self._selected_indices()
        if not indices:
            self._warn("请先勾选要操作的邮箱")
            return
        for i in indices:
            self.emails[i]["status"] = STATUS_BANNED
        save_emails(self.emails)
        self.refresh_table()

    def on_batch_unban(self):
        """批量将勾选项设置为「可用」。"""
        indices = self._selected_indices()
        if not indices:
            self._warn("请先勾选要操作的邮箱")
            return
        for i in indices:
            self.emails[i]["status"] = STATUS_AVAILABLE
        save_emails(self.emails)
        self.refresh_table()

    def on_batch_delete(self):
        """批量删除勾选项（带二次确认）。"""
        indices = self._selected_indices()
        if not indices:
            self._warn("请先勾选要删除的邮箱")
            return
        confirm = QMessageBox.question(
            self, "批量删除确认",
            f"确定要删除选中的 {len(indices)} 个邮箱吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        # 倒序删除，避免前面 pop 导致后续索引错位
        for i in sorted(indices, reverse=True):
            self.emails.pop(i)
        save_emails(self.emails)
        self.refresh_table()

    # ---------- 复制 / 提示 ----------

    def _warn(self, message: str):
        """统一封装警告弹窗，便于改样式。"""
        QMessageBox.warning(self, "提示", message)

    def _derive_base_email(self, email: str) -> str:
        """根据邮箱地址查出对应的基础邮箱。

        优先使用记录里保存的 base 字段；
        如果是历史数据没有 base 字段，则回退为邮箱本身（视为自我基础邮箱）。
        """
        for item in self.emails:
            if item.get("email") == email and item.get("base"):
                return item["base"]
        return email

    def _build_copyable_cell(self, text: str) -> QWidget:
        """构建一个直接点击即可复制的文本单元格。

        实现要点：
        - 使用 ClickableLabel 监听左键点击
        - 通过 QSS #copyableLabel:hover 让悬停时高亮，提示可点击
        - 鼠标光标改成手形，进一步表明可点击
        - 外面再包一层 QWidget 是为了给 padding 留余地，并便于以后扩展
        """
        label = ClickableLabel(text)
        label.setObjectName("copyableLabel")
        label.setToolTip(f"点击复制：{text}" if text else "")
        label.setCursor(Qt.PointingHandCursor)
        label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        # 用默认参数 t=text 冻结当前文本，避免 lambda 闭包共享变量问题
        label.clicked.connect(lambda t=text: self._copy_to_clipboard(t))

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        layout.addWidget(label)
        return container

    def _copy_to_clipboard(self, text: str):
        """将 text 写入系统剪贴板，并临时改窗口标题作为反馈。

        没有使用弹窗反馈，避免每次复制都打断用户操作。
        """
        if not text:
            return
        QApplication.clipboard().setText(text)
        original_title = "邮箱账号管理"
        self.setWindowTitle(f"{original_title}  ·  已复制：{text}")
        # 1.5 秒后自动还原标题
        QTimer.singleShot(1500, lambda: self.setWindowTitle(original_title))

    def statusBar_show(self, text: str):
        """工具方法：直接修改窗口标题，作为简易状态栏。"""
        self.setWindowTitle(f"邮箱账号管理  ·  {text}")


# ===================== 程序入口 =====================

def main():
    # 让终端 Ctrl+C 直接终止进程，避免在 Qt 事件循环里被推迟到下一次
    # Python 槽函数才抛出（之前会出现"添加邮箱后才报 KeyboardInterrupt"的现象）
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    window = EmailManagerWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
