# -*- coding: utf-8 -*-
"""
我的记账本 —— 桌面版
双击运行（或运行 启动记账本.bat）即可使用。
数据保存在同目录下的 账单数据.json 文件里。
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox
import json
import os
import datetime

# ---------- 数据文件位置（和本程序放在同一个文件夹） ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "账单数据.json")

# ---------- 分类配置 ----------
EXPENSE_CATS = [
    ("餐饮", "#f59e0b"), ("交通", "#3b82f6"), ("购物", "#ec4899"),
    ("居住", "#8b5cf6"), ("医疗", "#ef4444"), ("学习", "#06b6d4"),
    ("娱乐", "#f97316"), ("通讯", "#10b981"), ("人情", "#e11d48"),
    ("其他", "#64748b"),
]
INCOME_CATS = [
    ("工资", "#16a34a"), ("奖金", "#22c55e"), ("理财", "#0ea5e9"),("生活费", "#2be90e"),
    ("红包", "#f43f5e"), ("其他", "#64748b"),
]
CAT_COLORS = {}          # 分类名 -> 颜色
for name, color in EXPENSE_CATS + INCOME_CATS:
    CAT_COLORS.setdefault(name, color)

INCOME_COLOR = "#16a34a"   # 收入 - 绿色
EXPENSE_COLOR = "#ef4444"  # 支出 - 红色
BG = "#f5f6f8"             # 窗口背景
CARD_BG = "#ffffff"        # 卡片背景
PRIMARY = "#6366f1"        # 主按钮颜色
PRIMARY_HOVER = "#4f46e5"


def fmt(n):
    """把数字格式化成金额，例如 ¥1,234.56"""
    return "¥{:,.2f}".format(n)


class RoundedButton(tk.Canvas):
    """圆角按钮：用 Canvas 画出圆角矩形，支持悬停变色、点击回调。"""
    def __init__(self, parent, text, command, bg="#6366f1", fg="#ffffff",
                 hover=None, outline="", font=("Microsoft YaHei", 10),
                 padx=16, pady=6, radius=13):
        self._f = tkfont.Font(family=font[0], size=font[1],
                              weight=(font[2] if len(font) > 2 else "normal"))
        w = self._f.measure(text) + padx * 2
        h = self._f.metrics("linespace") + pady * 2
        super().__init__(parent, width=w, height=h, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0)
        self._text = text
        self._command = command
        self._bg = bg
        self._fg = fg
        self._hover = hover or bg
        self._outline = outline
        self._bw, self._bh, self._r = w, h, radius
        self._enabled = True
        self._current = bg
        self._draw(bg)
        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Enter>", lambda e: self._enabled and self._draw(self._hover))
        self.bind("<Leave>", lambda e: self._enabled and self._draw(self._bg))
        self.bind("<Configure>", self._resize)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
               x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
               x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.create_polygon(pts, smooth=True, **kw)

    def _draw(self, color):
        self._current = color
        self.delete("all")
        kw = {"fill": color}
        if self._outline:
            kw["outline"] = self._outline
            kw["width"] = 1
        self._round_rect(1, 1, self._bw - 1, self._bh - 1, self._r, **kw)
        self.create_text(self._bw / 2, self._bh / 2, text=self._text,
                         fill=self._fg, font=self._f)

    def _resize(self, e):
        self._bw, self._bh = e.width, e.height
        self._draw(self._current)

    def _press(self, e):
        if self._enabled:
            self._draw(self._hover)

    def _release(self, e):
        if self._enabled:
            self._draw(self._bg)
            if self._command:
                self._command()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("记账本")
        self.root.configure(bg=BG)
        self.fit_to_screen()

        self.records = self.load_data()
        self.current_month = datetime.date.today().strftime("%Y-%m")  # 例如 "2026-10"

        self.build_ui()
        self.refresh()

    def fit_to_screen(self):
        """按屏幕大小调整窗口，保证不超出屏幕，并居中显示。"""
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        w = min(1040, sw - 60)
        h = min(820, sh - 120)
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 3)
        self.root.minsize(760, 560)
        self.root.geometry("{}x{}+{}+{}".format(w, h, x, y))

    def _on_content_config(self, e):
        bbox = self.canvas.bbox("all")
        if bbox:
            self.canvas.configure(scrollregion=bbox)

    def _on_canvas_config(self, e):
        self.canvas.itemconfigure(self.content_id, width=e.width)

    def _on_wheel(self, e):
        self.canvas.yview_scroll(int(-e.delta / 120), "units")

    def _tree_wheel(self, e):
        self.tree.yview_scroll(int(-e.delta / 120), "units")
        return "break"

    # ---------- 数据存取 ----------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("保存失败", "数据没能保存到文件：\n" + str(e))

    # ---------- 界面搭建 ----------
    def build_ui(self):
        # 滚动容器：内容可以上下滚动，窗口再小也不会被截断
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        vbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.content = tk.Frame(self.canvas, bg=BG)
        self.content_id = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_config)
        self.canvas.bind("<Configure>", self._on_canvas_config)
        self.canvas.bind_all("<MouseWheel>", self._on_wheel)

        # 顶部：标题 + 月份切换
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill="x", padx=16, pady=(16, 10))

        tk.Label(top, text="📒 我的记账本", bg=BG, fg="#1f2937",
                 font=("Microsoft YaHei", 18, "bold")).pack(side="left")

        nav = tk.Frame(top, bg=BG)
        nav.pack(side="right")
        self.month_label = tk.Label(nav, text="", bg=BG, fg="#1f2937",
                                    font=("Microsoft YaHei", 13, "bold"), width=12)
        self.month_label.pack(side="left", padx=6)

        def nav_btn(text, cmd):
            return RoundedButton(nav, text, cmd, bg="#ffffff", fg="#374151",
                                 hover="#eef0f4", outline="#e5e7eb", padx=14, pady=5)
        nav_btn("‹ 上月", self.prev_month).pack(side="left", padx=3)
        nav_btn("下月 ›", self.next_month).pack(side="left", padx=3)
        nav_btn("回到本月", self.goto_today).pack(side="left", padx=3)

        # 记账 + 明细（放在顶部）
        top_main = tk.Frame(self.content, bg=BG)
        top_main.pack(fill="x", padx=16, pady=6)

        form_card = tk.Frame(top_main, bg=CARD_BG, highlightbackground="#e5e7eb",
                             highlightthickness=1)
        form_card.pack(side="left", fill="y", padx=(0, 7))
        self.build_form(form_card)

        rec_card = tk.Frame(top_main, bg=CARD_BG, highlightbackground="#e5e7eb",
                            highlightthickness=1)
        rec_card.pack(side="left", fill="both", expand=True, padx=(7, 0))
        self.build_records(rec_card)

        # 汇总卡片
        summary = tk.Frame(self.content, bg=BG)
        summary.pack(fill="x", padx=16, pady=6)
        self.sum_income = self.make_card(summary, "本月收入", INCOME_COLOR)
        self.sum_expense = self.make_card(summary, "本月支出", EXPENSE_COLOR)
        self.sum_balance = self.make_card(summary, "本月结余", INCOME_COLOR)

        # 图表区（左：饼图，右：柱状图）
        charts = tk.Frame(self.content, bg=BG)
        charts.pack(fill="x", padx=16, pady=(6, 16))

        pie_card = tk.Frame(charts, bg=CARD_BG, highlightbackground="#e5e7eb",
                            highlightthickness=1)
        pie_card.pack(side="left", fill="both", expand=True, padx=(0, 7))
        tk.Label(pie_card, text="🍩 支出分类", bg=CARD_BG, fg="#374151",
                 font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        pie_body = tk.Frame(pie_card, bg=CARD_BG)
        pie_body.pack(fill="both", expand=True, padx=8, pady=4)
        self.pie_canvas = tk.Canvas(pie_body, width=240, height=240, bg=CARD_BG,
                                    highlightthickness=0)
        self.pie_canvas.pack(side="left")
        self.legend_frame = tk.Frame(pie_body, bg=CARD_BG)
        self.legend_frame.pack(side="left", fill="both", expand=True, padx=6)

        bar_card = tk.Frame(charts, bg=CARD_BG, highlightbackground="#e5e7eb",
                            highlightthickness=1)
        bar_card.pack(side="left", fill="both", expand=True, padx=(7, 0))
        tk.Label(bar_card, text="📊 每日收支", bg=CARD_BG, fg="#374151",
                 font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))
        self.bar_canvas = tk.Canvas(bar_card, height=250, bg=CARD_BG, highlightthickness=0)
        self.bar_canvas.pack(fill="both", expand=True, padx=8, pady=4)

    def make_card(self, parent, title, color):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground="#e5e7eb",
                        highlightthickness=1)
        card.pack(side="left", fill="x", expand=True, padx=6)
        tk.Label(card, text=title, bg=CARD_BG, fg="#6b7280",
                 font=("Microsoft YaHei", 11)).pack(anchor="w", padx=14, pady=(12, 2))
        val = tk.Label(card, text="¥0.00", bg=CARD_BG, fg=color,
                       font=("Microsoft YaHei", 17, "bold"))
        val.pack(anchor="w", padx=14, pady=(0, 12))
        return val

    def build_form(self, parent):
        tk.Label(parent, text="✏️ 记一笔", bg=CARD_BG, fg="#374151",
                 font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 6))

        self.type_var = tk.StringVar(value="expense")
        type_row = tk.Frame(parent, bg=CARD_BG)
        type_row.pack(fill="x", padx=14, pady=2)
        ttk.Radiobutton(type_row, text="支出", variable=self.type_var, value="expense",
                        command=self.update_cats).pack(side="left")
        ttk.Radiobutton(type_row, text="收入", variable=self.type_var, value="income",
                        command=self.update_cats).pack(side="left", padx=(16, 0))

        def add_field(label, widget):
            tk.Label(parent, text=label, bg=CARD_BG, fg="#6b7280",
                     font=("Microsoft YaHei", 10)).pack(anchor="w", padx=14, pady=(8, 2))
            widget.pack(fill="x", padx=14)

        self.amount_var = tk.StringVar()
        add_field("金额（元）", ttk.Entry(parent, textvariable=self.amount_var, width=18))

        self.cat_var = tk.StringVar()
        self.cat_box = ttk.Combobox(parent, textvariable=self.cat_var, state="readonly", width=18)
        add_field("分类", self.cat_box)

        self.date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        add_field("日期（年-月-日）", ttk.Entry(parent, textvariable=self.date_var, width=18))

        self.note_var = tk.StringVar()
        note_entry = ttk.Entry(parent, textvariable=self.note_var, width=18)
        add_field("备注（可不填）", note_entry)
        note_entry.bind("<Return>", lambda e: self.add_record())

        RoundedButton(parent, "保存", self.add_record, bg=PRIMARY, fg="white",
                      hover=PRIMARY_HOVER, font=("Microsoft YaHei", 12, "bold"),
                      pady=9).pack(fill="x", padx=14, pady=14)

        self.update_cats()

    def build_records(self, parent):
        head = tk.Frame(parent, bg=CARD_BG)
        head.pack(fill="x", padx=14, pady=(12, 4))
        tk.Label(head, text="📋 账单明细", bg=CARD_BG, fg="#374151",
                 font=("Microsoft YaHei", 12, "bold")).pack(side="left")
        RoundedButton(head, "导出 CSV", self.export_csv, bg="#ffffff", fg="#374151",
                      hover="#eef0f4", outline="#e5e7eb", padx=12, pady=4).pack(side="right")
        RoundedButton(head, "删除选中", self.delete_selected, bg="#ffffff", fg="#374151",
                      hover="#eef0f4", outline="#e5e7eb", padx=12, pady=4).pack(side="right", padx=(0, 8))

        self.tree = ttk.Treeview(parent, columns=("date", "cat", "note", "amount"),
                                 show="headings", height=12)
        self.tree.heading("date", text="日期")
        self.tree.heading("cat", text="分类")
        self.tree.heading("note", text="备注")
        self.tree.heading("amount", text="金额")
        self.tree.column("date", width=90, anchor="center")
        self.tree.column("cat", width=80, anchor="center")
        self.tree.column("note", width=170, anchor="w")
        self.tree.column("amount", width=100, anchor="e")
        self.tree.tag_configure("income", foreground=INCOME_COLOR)
        self.tree.tag_configure("expense", foreground=EXPENSE_COLOR)

        scroll = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=(0, 14))
        scroll.pack(side="left", fill="y", pady=(0, 14))
        self.tree.bind("<MouseWheel>", self._tree_wheel)

    # ---------- 分类下拉框 ----------
    def update_cats(self):
        cats = EXPENSE_CATS if self.type_var.get() == "expense" else INCOME_CATS
        names = [c[0] for c in cats]
        self.cat_box["values"] = names
        if self.cat_var.get() not in names:
            self.cat_var.set(names[0])

    # ---------- 月份切换 ----------
    def prev_month(self):
        self.shift_month(-1)

    def next_month(self):
        self.shift_month(1)

    def goto_today(self):
        self.current_month = datetime.date.today().strftime("%Y-%m")
        self.refresh()

    def shift_month(self, delta):
        y, m = self.current_month.split("-")
        y, m = int(y), int(m) + delta
        if m == 0:
            y, m = y - 1, 12
        elif m == 13:
            y, m = y + 1, 1
        self.current_month = "{:04d}-{:02d}".format(y, m)
        self.refresh()

    # ---------- 记账 ----------
    def add_record(self):
        rtype = self.type_var.get()
        try:
            amount = float(self.amount_var.get().strip())
        except ValueError:
            messagebox.showwarning("提示", "请输入正确的金额（数字，大于 0）")
            return
        if amount <= 0:
            messagebox.showwarning("提示", "金额要大于 0 哦")
            return

        date = self.date_var.get().strip() or datetime.date.today().strftime("%Y-%m-%d")
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            messagebox.showwarning("提示", "日期格式不对，请写成 年-月-日，例如 2026-10-06")
            return

        self.records.append({
            "id": int(datetime.datetime.now().timestamp() * 1000),
            "type": rtype,
            "amount": round(amount, 2),
            "category": self.cat_var.get(),
            "date": date,
            "note": self.note_var.get().strip(),
        })
        self.save_data()
        self.amount_var.set("")
        self.note_var.set("")
        self.current_month = date[:7]  # 跳到记录所在的月份
        self.refresh()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在账单列表里，点一下要删除的那一条")
            return
        if messagebox.askyesno("确认", "确定删除选中的 {} 条记录吗？".format(len(sel))):
            ids = {int(i) for i in sel}
            self.records = [r for r in self.records if r["id"] not in ids]
            self.save_data()
            self.refresh()

    def export_csv(self):
        if not self.records:
            messagebox.showinfo("提示", "还没有任何账单，无法导出")
            return
        lines = ["类型,金额,分类,日期,备注"]
        for r in self.records:
            tn = "收入" if r["type"] == "income" else "支出"
            note = r["note"].replace('"', '""')
            lines.append('{},{},{},{},,"{}"'.format(tn, r["amount"], r["category"], r["date"], note))
        path = os.path.join(BASE_DIR, "账单_" + self.current_month + ".csv")
        try:
            with open(path, "w", encoding="utf-8-sig") as f:
                f.write("\n".join(lines))
            messagebox.showinfo("导出成功", "已保存到：\n" + path)
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    # ---------- 刷新显示 ----------
    def month_records(self):
        return [r for r in self.records if r["date"][:7] == self.current_month]

    def refresh(self):
        y, m = self.current_month.split("-")
        self.month_label.config(text="{} 年 {} 月".format(int(y), int(m)))
        self.render_summary()
        self.render_pie()
        self.render_bars()
        self.render_records()

    def render_summary(self):
        income = sum(r["amount"] for r in self.month_records() if r["type"] == "income")
        expense = sum(r["amount"] for r in self.month_records() if r["type"] == "expense")
        self.sum_income.config(text=fmt(income))
        self.sum_expense.config(text=fmt(expense))
        bal = income - expense
        self.sum_balance.config(text=fmt(bal), fg=INCOME_COLOR if bal >= 0 else EXPENSE_COLOR)

    def render_pie(self):
        self.pie_canvas.delete("all")
        for w in self.legend_frame.winfo_children():
            w.destroy()

        data = {}
        for r in self.month_records():
            if r["type"] == "expense":
                data[r["category"]] = data.get(r["category"], 0) + r["amount"]
        total = sum(data.values())

        if total <= 0:
            self.pie_canvas.create_text(120, 120, text="这个月还没有支出记录",
                                        fill="#6b7280", font=("Microsoft YaHei", 11))
            return

        # 画环形图
        cx, cy, radius, hole = 120, 120, 90, 48
        start = 90  # 从正上方开始
        items = sorted(data.items(), key=lambda kv: -kv[1])
        for name, amount in items:
            extent = -360 * amount / total
            color = CAT_COLORS.get(name, "#64748b")
            self.pie_canvas.create_arc(cx - radius, cy - radius, cx + radius, cy + radius,
                                       start=start, extent=extent, fill=color, outline=CARD_BG)
            start += extent
        self.pie_canvas.create_oval(cx - hole, cy - hole, cx + hole, cy + hole,
                                    fill=CARD_BG, outline=CARD_BG)
        self.pie_canvas.create_text(cx, cy - 12, text="总支出", fill="#6b7280",
                                    font=("Microsoft YaHei", 10))
        self.pie_canvas.create_text(cx, cy + 10, text=fmt(total), fill="#1f2937",
                                    font=("Microsoft YaHei", 12, "bold"))

        # 图例
        for name, amount in items:
            row = tk.Frame(self.legend_frame, bg=CARD_BG)
            row.pack(anchor="w", pady=2)
            color = CAT_COLORS.get(name, "#64748b")
            tk.Label(row, text="●", fg=color, bg=CARD_BG,
                     font=("Microsoft YaHei", 12)).pack(side="left")
            pct = amount / total * 100
            tk.Label(row, text="  {}  {} ({:.1f}%)".format(name, fmt(amount), pct),
                     bg=CARD_BG, fg="#374151",
                     font=("Microsoft YaHei", 9)).pack(side="left")

    def render_bars(self):
        self.bar_canvas.delete("all")
        days = self.days_in_month()
        per_day = {d: {"income": 0, "expense": 0} for d in range(1, days + 1)}
        for r in self.month_records():
            d = int(r["date"][8:10])
            if 1 <= d <= days:
                per_day[d][r["type"]] += r["amount"]

        W = 470
        H = 230
        base = H - 26
        top = 16
        chart_h = base - top
        max_val = 1
        for d in per_day:
            max_val = max(max_val, per_day[d]["income"], per_day[d]["expense"])

        has_data = any(per_day[d]["income"] + per_day[d]["expense"] > 0 for d in per_day)
        if not has_data:
            self.bar_canvas.create_text(W // 2, H // 2, text="这个月还没有收支记录",
                                        fill="#6b7280", font=("Microsoft YaHei", 11))
            return

        slot = (W - 20) / days
        for d in range(1, days + 1):
            x = 10 + (d - 1) * slot + slot / 2
            h_in = per_day[d]["income"] / max_val * chart_h
            h_out = per_day[d]["expense"] / max_val * chart_h
            bar_w = 4
            self.bar_canvas.create_rectangle(x - bar_w - 1, base - h_in, x - 1, base,
                                             fill=INCOME_COLOR, outline="")
            self.bar_canvas.create_rectangle(x + 1, base - h_out, x + bar_w + 1, base,
                                             fill=EXPENSE_COLOR, outline="")
            if d == 1 or d % 5 == 0 or d == days:
                self.bar_canvas.create_text(x, base + 9, text=str(d), fill="#6b7280",
                                            font=("Microsoft YaHei", 8))

        # 图例
        self.bar_canvas.create_rectangle(W - 110, 6, W - 98, 14, fill=INCOME_COLOR, outline="")
        self.bar_canvas.create_text(W - 92, 10, text="收入", anchor="w",
                                    fill="#6b7280", font=("Microsoft YaHei", 9))
        self.bar_canvas.create_rectangle(W - 50, 6, W - 38, 14, fill=EXPENSE_COLOR, outline="")
        self.bar_canvas.create_text(W - 32, 10, text="支出", anchor="w",
                                    fill="#6b7280", font=("Microsoft YaHei", 9))

    def render_records(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        recs = sorted(self.month_records(),
                      key=lambda r: (r["date"], r["id"]), reverse=True)
        for r in recs:
            sign = "+" if r["type"] == "income" else "-"
            self.tree.insert("", "end", iid=str(r["id"]),
                             values=(r["date"], r["category"], r["note"], sign + fmt(r["amount"])),
                             tags=(r["type"],))

    def days_in_month(self):
        y, m = map(int, self.current_month.split("-"))
        return (datetime.date(y + (m // 12), m % 12 + 1, 1) - datetime.timedelta(days=1)).day


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
