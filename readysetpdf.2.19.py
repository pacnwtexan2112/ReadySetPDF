import os
import sys
import json
import shutil
import csv
import urllib.request
import urllib.parse
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
from tkinterdnd2 import DND_FILES, TkinterDnD
import fitz  # PyMuPDF
from PIL import Image, ImageTk

# Optional QR library
try:
    import qrcode
    import io
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

# ====================== TOOLTIP CLASS ======================
class ToolTip(object):
    def __init__(self, widget, text, app):
        self.widget, self.text, self.app = widget, text, app
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None
    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert") or (0, 0, 0, 0)
        x += self.widget.winfo_rootx() + 25; y += self.widget.winfo_rooty() + 20
        self.tw = tk.Toplevel(self.widget); self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tw, text=self.text, background=self.app.color_pale, foreground=self.app.color_navy, 
                 relief='flat', borderwidth=1, highlightbackground=self.app.color_steel, highlightthickness=1,
                 font=("Arial", "9", "bold"), padx=6, pady=4).pack(ipadx=1)
    def close(self, event=None):
        if self.tw: self.tw.destroy(); self.tw = None

# ====================== APP CLASS ======================
class ReadySetPDFApp:
    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("ReadySetPDF - Professional Prepress")
        
        base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        self.logo_path = os.path.join(base_path, "ReadySetPDF logo.jpg")
        icon_path = os.path.join(base_path, "icon.ico")
        
        if os.path.exists(self.logo_path):
            try:
                self.app_icon = ImageTk.PhotoImage(Image.open(self.logo_path))
                self.root.iconphoto(False, self.app_icon)
            except Exception:
                if os.path.exists(icon_path): self.root.iconbitmap(icon_path)
        elif os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            
        self.root.geometry("1450x920")
        
        self.current_theme_var = tk.StringVar(value="Tech Theme (Default)")
        self.themes = {
            "Tech Theme (Default)": {"WHITE": "#F3EEE8", "NAVY": "#19123D", "LIME": "#B2F332", "STEEL": "#6787AF", "MINT": "#BADDCF", "PALE": "#E8F3DA"},
            "Ink Wash": {"WHITE": "#FFFFE3", "NAVY": "#4A4A4A", "LIME": "#6D8196", "STEEL": "#CBCBCB", "MINT": "#E2E2C7", "PALE": "#F0F0D8"},
            "California Beaches": {"WHITE": "#FAFAFA", "NAVY": "#2C3E50", "LIME": "#FFC067", "STEEL": "#7D99AA", "MINT": "#66F4FF", "PALE": "#E6FAFC"},
            "Cobalt Sky": {"WHITE": "#F4F7FB", "NAVY": "#000080", "LIME": "#0047AB", "STEEL": "#6D8196", "MINT": "#82C8E5", "PALE": "#EBF4FA"}
        }
        self.set_colors()
        self.root.configure(bg=self.color_white)
        self.main_container = tk.Frame(self.root, bg=self.color_white)
        self.main_container.pack(fill="both", expand=True)

        self.files, self.action_queue, self.active_history_index = [], [], -1
        self.preview_doc = None
        self.current_preview_page = 0

        self.rotate_deg_var = tk.StringVar(value="90")
        self.rotate_pages_var = tk.StringVar(value="all")
        self.resize_preset_var = tk.StringVar(value="Letter")
        self.resize_w_var = tk.StringVar(value="8.5")
        self.resize_h_var = tk.StringVar(value="11")
        self.resize_unit_var = tk.StringVar(value="inches")
        self.resize_landscape_var = tk.BooleanVar(value=False)
        self.resize_stretch_var = tk.BooleanVar(value=False)
        self.crop_left_var = tk.StringVar(value="0")
        self.crop_top_var = tk.StringVar(value="0")
        self.crop_right_var = tk.StringVar(value="0")
        self.crop_bottom_var = tk.StringVar(value="0")
        self.crop_unit_var = tk.StringVar(value="inches")
        
        self.monkey_preset_var = tk.StringVar(value="Custom")
        self.monkey_w_var = tk.StringVar(value="9.5")
        self.monkey_h_var = tk.StringVar(value="12")
        self.monkey_unit_var = tk.StringVar(value="inches")
        self.monkey_landscape_var = tk.BooleanVar(value=False)
        self.monkey_order_var = tk.StringVar(value="Sequential")
        self.monkey_double_sided_var = tk.BooleanVar(value=False)
        self.monkey_repeat_var = tk.StringVar(value="1")
        self.monkey_direction_var = tk.StringVar(value="LTR") 
        self.monkey_margin_l_var = tk.StringVar(value="0")
        self.monkey_margin_t_var = tk.StringVar(value="0")
        self.monkey_gutter_h_var = tk.StringVar(value="0")
        self.monkey_gutter_v_var = tk.StringVar(value="0")
        self.monkey_center_var = tk.BooleanVar(value=True)
        self.monkey_draw_marks_var = tk.BooleanVar(value=True)
        self.monkey_mark_dist_var = tk.StringVar(value="0.125")    
        self.monkey_mark_thick_var = tk.StringVar(value="0.007")   
        
        self.grid_preset_var = tk.StringVar(value="12x18")
        self.grid_w_var = tk.StringVar(value="12")
        self.grid_h_var = tk.StringVar(value="18")
        self.grid_unit_var = tk.StringVar(value="inches")
        self.grid_landscape_var = tk.BooleanVar(value=False)
        self.grid_order_var = tk.StringVar(value="Sequential")
        self.grid_double_sided_var = tk.BooleanVar(value=False)
        self.grid_repeat_var = tk.StringVar(value="1")
        self.grid_autoscale_var = tk.BooleanVar(value=False)
        self.grid_aspect_var = tk.BooleanVar(value=True)
        self.grid_cols_var = tk.StringVar(value="2")
        self.grid_rows_var = tk.StringVar(value="2")
        self.grid_margin_l_var = tk.StringVar(value="0")
        self.grid_margin_t_var = tk.StringVar(value="0")
        self.grid_gutter_h_var = tk.StringVar(value="0.25")
        self.grid_gutter_v_var = tk.StringVar(value="0.25")
        self.grid_center_var = tk.BooleanVar(value=True)
        self.grid_draw_marks_var = tk.BooleanVar(value=True)
        self.grid_mark_dist_var = tk.StringVar(value="0.125")    
        self.grid_mark_thick_var = tk.StringVar(value="0.007")
        
        self.blank_pos_var = tk.StringVar(value="End of Document")
        self.blank_page_num_var = tk.StringVar(value="1")
        self.booklet_preset_var = tk.StringVar(value="Custom")
        self.booklet_w_var = tk.StringVar(value="18")
        self.booklet_h_var = tk.StringVar(value="12")
        self.booklet_unit_var = tk.StringVar(value="inches")
        self.booklet_landscape_var = tk.BooleanVar(value=False)
        self.booklet_center_gutter_var = tk.StringVar(value="0")
        self.booklet_margin_l_var = tk.StringVar(value="0")
        self.booklet_margin_t_var = tk.StringVar(value="0")
        self.booklet_creep_var = tk.StringVar(value="0")
        self.booklet_creep_dir_var = tk.StringVar(value="Outward")
        self.booklet_center_var = tk.BooleanVar(value=True)
        self.booklet_rotate_var = tk.BooleanVar(value=False)
        
        self.cutter_size_var = tk.StringVar(value="0.13")
        self.cutter_thick_var = tk.StringVar(value="0.03")
        self.cutter_placement_var = tk.StringVar(value="Inside")
        self.cutter_margin_var = tk.StringVar(value="0")
        self.cutter_pages_var = tk.StringVar(value="all")
        self.cutter_remove_art_var = tk.BooleanVar(value=False)
        self.color_mode_var = tk.StringVar(value="Grayscale")
        self.color_dpi_var = tk.StringVar(value="300")
        self.preview_zoom_var = tk.StringVar(value="1.0x (Standard Fit)")
        self.apply_stamp_var = tk.BooleanVar(value=False)
        self.stamp_text_var = tk.StringVar(value="DIGITAL PROOF")
        self.lock_print_var = tk.BooleanVar(value=False)
        self.lock_edit_var = tk.BooleanVar(value=False)
        self.custom_owner_pw_var = tk.StringVar(value="readysetpdf")  
        
        self.batch_in_var = tk.StringVar()
        self.batch_out_var = tk.StringVar()
        self.batch_recipe_var = tk.StringVar()
        self.is_watching = False
        self.vdp_csv_path_var = tk.StringVar()
        self.vdp_headers = []
        self.vdp_mapped_fields = []
        self.vdp_target_mode = False
        self.vdp_col_var = tk.StringVar()
        self.vdp_type_var = tk.StringVar(value="Text")
        self.vdp_x_var = tk.StringVar(value="0.5")
        self.vdp_y_var = tk.StringVar(value="0.5")
        self.vdp_w_var = tk.StringVar(value="2.0")
        self.vdp_h_var = tk.StringVar(value="0.5")
        self.vdp_font_var = tk.StringVar(value="Helvetica")
        self.vdp_size_var = tk.StringVar(value="12")
        self.vdp_align_var = tk.StringVar(value="Left")
        self.vdp_color_var = tk.StringVar(value="#000000")
        self.unlock_source_var = tk.StringVar()
        self.unlock_pass_var = tk.StringVar()

        self.preview_img_w = 0; self.preview_img_h = 0
        self.preview_pos_x = 0; self.preview_pos_y = 0
        self.preview_final_scale = 1.0

        self.setup_styles()
        self.setup_ui()

    def set_colors(self):
        theme = self.themes.get(self.current_theme_var.get(), self.themes["Tech Theme (Default)"])
        self.color_white = theme["WHITE"]; self.color_navy = theme["NAVY"]
        self.color_lime = theme["LIME"]; self.color_steel = theme["STEEL"]
        self.color_mint = theme["MINT"]; self.color_pale = theme["PALE"]

    def change_theme(self, event=None):
        self.set_colors()
        self.root.configure(bg=self.color_white)
        self.main_container.destroy()
        self.setup_styles()
        self.main_container = tk.Frame(self.root, bg=self.color_white)
        self.main_container.pack(fill="both", expand=True)
        self.setup_ui()
        for f in self.files: self.file_list.insert(tk.END, os.path.basename(f))
        for step in self.action_queue: self.queue_box.insert(tk.END, self._get_step_display_text(step))
        if self.active_history_index >= 0: self.queue_box.selection_set(self.active_history_index)
        self.render_live_preview()

    def setup_styles(self):
        self.style = ttk.Style(); self.style.theme_use('clam')
        self.style.configure("TLabelframe", background=self.color_white, bordercolor=self.color_steel, borderwidth=1)
        self.style.configure("TLabelframe.Label", background=self.color_white, foreground=self.color_navy, font=("Arial", 11, "bold"))
        self.style.configure("TFrame", background=self.color_white)
        self.style.configure("TCheckbutton", background=self.color_white, foreground=self.color_navy, font=("Arial", 9))
        self.style.map("TCheckbutton", background=[("active", self.color_white)])
        self.style.configure("TRadiobutton", background=self.color_white, foreground=self.color_navy, font=("Arial", 9))
        self.style.map("TRadiobutton", background=[("active", self.color_white)])

    def _create_btn(self, parent, text, bg, fg, command, width=None):
        btn = tk.Button(parent, text=text, bg=bg, fg=fg, activebackground=self.color_navy, activeforeground=self.color_white,
                        relief="flat", borderwidth=0, font=("Arial", 10, "bold"), padx=15, pady=8, cursor="hand2", command=command)
        if width: btn.config(width=width)
        return btn

    def _add_tab_btn(self, parent, text, key):
        btn = tk.Button(parent, text=text, bg=self.color_mint, fg=self.color_navy, activebackground=self.color_steel, activeforeground=self.color_white,
                        relief="flat", borderwidth=0, font=("Arial", 10, "bold"), padx=15, pady=8, cursor="hand2", command=lambda: self.select_tab(key))
        btn.pack(side="left", padx=(0, 2))
        self.tab_btns[key] = btn

    def select_tab(self, key):
        for k, btn in self.tab_btns.items(): btn.config(bg=self.color_mint, fg=self.color_navy)
        self.tab_btns[key].config(bg=self.color_steel, fg=self.color_white)
        for k, tab in self.tabs.items(): tab.pack_forget()
        self.tabs[key].pack(fill="both", expand=True)

    def setup_ui(self):
        h = tk.Frame(self.main_container, bg=self.color_white, padx=20, pady=15); h.pack(fill="x")
        if os.path.exists(self.logo_path):
            try:
                pil_img = Image.open(self.logo_path)
                ratio = 50.0 / float(pil_img.height); new_w = int(float(pil_img.width) * ratio)
                pil_img = pil_img.resize((new_w, 50)); self.header_logo_img = ImageTk.PhotoImage(pil_img)
                tk.Label(h, image=self.header_logo_img, bg=self.color_white).pack(side="left", padx=(0, 10))
            except Exception: pass
                
        tk.Label(h, text="ReadySetPDF", font=("Arial", 22, "bold"), bg=self.color_white, fg=self.color_navy).pack(side="left")
        theme_combo = ttk.Combobox(h, values=list(self.themes.keys()), textvariable=self.current_theme_var, state="readonly", width=22, font=("Arial", 9))
        theme_combo.pack(side="right", padx=(15, 0), pady=12); theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
        
        self._create_btn(h, "🚀 Build & Save Final PDF", self.color_lime, self.color_navy, self.show_export_dialog).pack(side="right")
        self._create_btn(h, "🖼️ Export Proof Images", self.color_mint, self.color_navy, self.export_as_images).pack(side="right", padx=15)
        
        paned = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL); paned.pack(fill="both", expand=True, padx=15, pady=10)
        l = ttk.PanedWindow(paned, orient=tk.VERTICAL)
        
        f = ttk.LabelFrame(l, text=" 1. Assets Manager ")
        self.file_list = tk.Listbox(f, height=8, bg=self.color_pale, fg=self.color_navy, selectbackground=self.color_steel, relief="flat", highlightthickness=1)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_list.drop_target_register(DND_FILES); self.file_list.dnd_bind('<<Drop>>', self.drop_files)
        btn_row_f = ttk.Frame(f); btn_row_f.pack(fill="x", pady=(0,5), padx=5)
        self._create_btn(btn_row_f, "➕ Add Files", self.color_steel, self.color_white, self.load_pdfs).pack(side="left", fill="x", expand=True, padx=(0,2))
        self._create_btn(btn_row_f, "❌ Clear", self.color_mint, self.color_navy, self.clear_files).pack(side="left", fill="x", expand=True, padx=(2,0))
        l.add(f, weight=1)
        
        q = ttk.LabelFrame(l, text=" 2. Applied Steps Stack ")
        self.queue_box = tk.Listbox(q, height=8, bg=self.color_pale, fg=self.color_navy, selectbackground=self.color_steel, relief="flat", highlightthickness=1, font=("Arial", 10, "bold"))
        self.queue_box.pack(fill="both", expand=True, padx=5, pady=5); self.queue_box.bind("<<ListboxSelect>>", self.handle_history_selection)
        
        btn_row_q1 = ttk.Frame(q); btn_row_q1.pack(fill="x", pady=(0,2), padx=5)
        self._create_btn(btn_row_q1, "🔼 Move Up", self.color_steel, self.color_white, lambda: self.move_queue_step(-1)).pack(side="left", fill="x", expand=True, padx=(0,2))
        self._create_btn(btn_row_q1, "🔽 Move Down", self.color_steel, self.color_white, lambda: self.move_queue_step(1)).pack(side="left", fill="x", expand=True, padx=(2,0))
        btn_row_q2 = ttk.Frame(q); btn_row_q2.pack(fill="x", pady=(0,2), padx=5)
        self._create_btn(btn_row_q2, "🗑️ Remove", self.color_steel, self.color_white, self.remove_queue_step).pack(side="left", fill="x", expand=True, padx=(0,2))
        self._create_btn(btn_row_q2, "🔄 Reset", self.color_mint, self.color_navy, self.clear_queue).pack(side="left", fill="x", expand=True, padx=(2,0))
        btn_row_q3 = ttk.Frame(q); btn_row_q3.pack(fill="x", pady=(0,5), padx=5)
        self._create_btn(btn_row_q3, "💾 Save Recipe", self.color_lime, self.color_navy, self.save_recipe).pack(side="left", fill="x", expand=True, padx=(0,2))
        self._create_btn(btn_row_q3, "📂 Load Recipe", self.color_lime, self.color_navy, self.load_recipe).pack(side="left", fill="x", expand=True, padx=(2,0))
        l.add(q, weight=1); paned.add(l, weight=1)

        self.middle_pane = tk.Frame(paned, bg=self.color_white); paned.add(self.middle_pane, weight=1)
        self.tab_nav_frame = tk.Frame(self.middle_pane, bg=self.color_white); self.tab_nav_frame.pack(fill="x")
        tk.Label(self.tab_nav_frame, text="* Indicates tools planned for future Pro Tier", bg=self.color_white, fg=self.color_steel, font=("Arial", 9, "italic")).pack(anchor="w", pady=(0, 5))

        self.tab_row1 = tk.Frame(self.tab_nav_frame, bg=self.color_white); self.tab_row1.pack(fill="x", pady=(0, 2))
        self.tab_row2 = tk.Frame(self.tab_nav_frame, bg=self.color_white); self.tab_row2.pack(fill="x", pady=(0, 5))
        self.tab_content_frame = tk.Frame(self.middle_pane, bg=self.color_white, highlightbackground=self.color_steel, highlightthickness=1); self.tab_content_frame.pack(fill="both", expand=True)

        self.tabs = {}; self.tab_btns = {}
        self.build_resize_tab(); self.build_crop_tab(); self.build_monkey_tab(); self.build_grid_tab()
        self.build_booklet_tab(); self.build_cutter_tab(); self.build_rotate_tab(); self.build_vdp_tab()
        self.build_color_tab(); self.build_preflight_tab(); self.build_batch_tab(); self.build_unlock_tab() 

        self._add_tab_btn(self.tab_row1, "📐 Resize", "Resize"); self._add_tab_btn(self.tab_row1, "📏 Crop", "Crop")
        self._add_tab_btn(self.tab_row1, "🐒 Monkey", "Monkey"); self._add_tab_btn(self.tab_row1, "🔲 Grid", "Grid")
        self._add_tab_btn(self.tab_row1, "📖 Booklet", "Booklet"); self._add_tab_btn(self.tab_row1, "✂️ Cutter", "Cutter")
        self._add_tab_btn(self.tab_row1, "🔄 Rotate", "Rotate")
        self._add_tab_btn(self.tab_row2, "🏷️ VDP Mail Merge *", "VDP"); self._add_tab_btn(self.tab_row2, "🎨 Color *", "Color")
        self._add_tab_btn(self.tab_row2, "✅ Preflight *", "Preflight"); self._add_tab_btn(self.tab_row2, "📂 Automation *", "Automation")
        self._add_tab_btn(self.tab_row2, "🔓 Unlock *", "Unlock")

        self.select_tab("Resize")

        r = ttk.LabelFrame(paned, text=" 4. Real-Time Monitor "); paned.add(r, weight=2)
        nav_frame = ttk.Frame(r); nav_frame.pack(fill="x", pady=5, padx=5)
        self._create_btn(nav_frame, "◀ Previous", self.color_steel, self.color_white, lambda: self.navigate_preview(-1)).pack(side="left")
        self.preview_page_label = tk.Label(nav_frame, text="Spread: 0 / 0", font=("Arial", 11, "bold"), bg=self.color_white, fg=self.color_navy); self.preview_page_label.pack(side="left", expand=True)
        self._create_btn(nav_frame, "Next ▶", self.color_steel, self.color_white, lambda: self.navigate_preview(1)).pack(side="left")
        ctrl_row = ttk.Frame(r); ctrl_row.pack(fill="x", pady=5, padx=5)
        self.history_status_label = tk.Label(ctrl_row, text="Viewing: Original Baseline", fg=self.color_steel, bg=self.color_white, font=("Arial", 10, "bold"), anchor="w"); self.history_status_label.pack(side="left", fill="x", expand=True)
        tk.Label(ctrl_row, text="🔎 Zoom:", font=("Arial", 10, "bold"), bg=self.color_white, fg=self.color_navy).pack(side="left", padx=2)
        self.zoom_combo = ttk.Combobox(ctrl_row, values=["1.0x (Standard Fit)", "1.5x Zoom", "2.0x High Zoom", "3.0x Max Detail"], textvariable=self.preview_zoom_var, width=18, state="readonly", font=("Arial", 9))
        self.zoom_combo.pack(side="left", padx=5); self.zoom_combo.bind("<<ComboboxSelected>>", lambda e: self.render_live_preview())

        self.preview_container = tk.Frame(r, bg=self.color_navy, bd=0); self.preview_container.pack(fill="both", expand=True, padx=5, pady=5)
        self.preview_container.grid_rowconfigure(0, weight=1); self.preview_container.grid_columnconfigure(0, weight=1)
        self.preview_canvas = tk.Canvas(self.preview_container, bg=self.color_navy, highlightthickness=0); self.preview_canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scroll = ttk.Scrollbar(self.preview_container, orient="vertical", command=self.preview_canvas.yview); self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self.preview_container, orient="horizontal", command=self.preview_canvas.xview); self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.preview_canvas.configure(yscrollcommand=self.v_scroll.set, xscrollcommand=self.h_scroll.set)
        
        self.preview_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.preview_canvas.bind("<Button-1>", self.on_canvas_click)
        
        footer = tk.Frame(self.main_container, bg=self.color_white, padx=10, pady=5); footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="System Ready.", fg=self.color_steel, bg=self.color_white, font=("Arial", 10, "bold")).pack(side="left")
        
        btn_feedback = tk.Button(footer, text="🐞 Report Bug / Feedback", bg=self.color_white, fg=self.color_steel, relief="flat", bd=0, font=("Arial", 9, "underline", "bold"), cursor="hand2", activebackground=self.color_white, activeforeground=self.color_navy, command=self.open_feedback_form)
        btn_feedback.pack(side="left", padx=(10, 0))
        
        tk.Label(footer, text="Rev 2.19 (Feedback Form) | by Darren Moeller 2026", fg=self.color_steel, bg=self.color_white, font=("Arial", 9, "italic")).pack(side="right", padx=10)

    # --- HELPERS ---
    def _on_mousewheel(self, event):
        self.preview_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def convert_to_points(self, val_str, unit):
        try:
            val = float(val_str)
            if unit == "inches": return val * 72.0
            if unit == "mm": return val * 2.83465
            return val
        except ValueError: return 72.0
        
    def parse_page_selection(self, page_str, total_pages):
        p_str = page_str.strip().lower()
        if p_str == "all" or p_str == "": return list(range(total_pages))
        pages = set()
        for part in p_str.split(","):
            if "-" in part:
                try:
                    start, end = part.split("-")
                    for i in range(max(1, int(start)), min(total_pages, int(end)) + 1): pages.add(i - 1)
                except ValueError: continue
            else:
                try: p_num = int(part); pages.add(p_num - 1) if 1 <= p_num <= total_pages else None
                except ValueError: continue
        return sorted(list(pages))

    # --- TAB BUILDERS ---
    def build_resize_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Resize"] = tab
        dim_frame = ttk.LabelFrame(tab, text="Target Fixed Paper Size Settings", padding=10); dim_frame.pack(fill="x", pady=10)
        tk.Label(dim_frame, text="Presets:", bg=self.color_white, fg=self.color_navy).grid(row=0, column=0, sticky="w")
        size_combo = ttk.Combobox(dim_frame, values=["Letter", "Legal", "Tabloid", "A4", "Custom"], textvariable=self.resize_preset_var, width=12, state="readonly")
        size_combo.grid(row=0, column=1, padx=5, pady=5); size_combo.bind("<<ComboboxSelected>>", lambda e: self.handle_resize_preset())
        tk.Label(dim_frame, text="Width:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(dim_frame, textvariable=self.resize_w_var, width=8, bg=self.color_pale).grid(row=1, column=1, padx=5, pady=5)
        ttk.Combobox(dim_frame, values=["inches", "mm", "points"], textvariable=self.resize_unit_var, width=8, state="readonly").grid(row=1, column=2, padx=5)
        tk.Label(dim_frame, text="Height:", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w"); tk.Entry(dim_frame, textvariable=self.resize_h_var, width=8, bg=self.color_pale).grid(row=2, column=1, padx=5, pady=5)
        cb_land = ttk.Checkbutton(tab, text="Force Landscape Orientation Layout", variable=self.resize_landscape_var); cb_land.pack(anchor="w", pady=2)
        cb_stretch = ttk.Checkbutton(tab, text="Stretch content layer to fit bounding box", variable=self.resize_stretch_var); cb_stretch.pack(anchor="w", pady=2)
        self._create_btn(tab, "➕ Add Resize Step", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Resize")).pack(fill="x", side="bottom", pady=10)

    def handle_resize_preset(self):
        val = self.resize_preset_var.get(); self.resize_unit_var.set("inches")
        if val == "Letter": self.resize_w_var.set("8.5"); self.resize_h_var.set("11")
        elif val == "Legal": self.resize_w_var.set("8.5"); self.resize_h_var.set("14")
        elif val == "Tabloid": self.resize_w_var.set("11"); self.resize_h_var.set("17")
        elif val == "A4": self.resize_w_var.set("8.27"); self.resize_h_var.set("11.69")

    def build_crop_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Crop"] = tab
        tk.Label(tab, text="Trim white space or margins from the document.", bg=self.color_white, fg=self.color_steel, font=("Arial", 10, "italic")).pack(anchor="w", pady=(0, 10))
        margin_frame = ttk.LabelFrame(tab, text="Margin Crop Settings", padding=10); margin_frame.pack(fill="x", pady=5)
        unit_row = ttk.Frame(margin_frame); unit_row.pack(fill="x", pady=(0, 10))
        tk.Label(unit_row, text="Units:", bg=self.color_white, fg=self.color_navy).pack(side="left")
        ttk.Combobox(unit_row, values=["inches", "mm", "points"], textvariable=self.crop_unit_var, width=8, state="readonly").pack(side="left", padx=5)
        grid_f = tk.Frame(margin_frame, bg=self.color_white); grid_f.pack(fill="x", pady=5)
        tk.Label(grid_f, text="Top:", bg=self.color_white, fg=self.color_navy).grid(row=0, column=2, padx=5, pady=5); tk.Entry(grid_f, textvariable=self.crop_top_var, width=6, bg=self.color_pale).grid(row=0, column=3, padx=5)
        tk.Label(grid_f, text="Left:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, padx=5, pady=5); tk.Entry(grid_f, textvariable=self.crop_left_var, width=6, bg=self.color_pale).grid(row=1, column=1, padx=5)
        tk.Label(grid_f, text="Right:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=4, padx=5, pady=5); tk.Entry(grid_f, textvariable=self.crop_right_var, width=6, bg=self.color_pale).grid(row=1, column=5, padx=5)
        tk.Label(grid_f, text="Bottom:", bg=self.color_white, fg=self.color_navy).grid(row=2, column=2, padx=5, pady=5); tk.Entry(grid_f, textvariable=self.crop_bottom_var, width=6, bg=self.color_pale).grid(row=2, column=3, padx=5)
        self._create_btn(tab, "➕ Add Crop Step", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Crop Margin")).pack(fill="x", side="bottom", pady=10)

    def build_monkey_tab(self):
        main_frame = ttk.Frame(self.tab_content_frame); self.tabs["Monkey"] = main_frame
        canvas = tk.Canvas(main_frame, bg=self.color_white, highlightthickness=0); scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=10); tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tab, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        paper_frame = ttk.LabelFrame(tab, text="Paper Size", padding=10); paper_frame.pack(fill="x", pady=(0, 5))
        size_combo = ttk.Combobox(paper_frame, values=["12x18", "13x19", "Letter", "Tabloid", "Custom"], textvariable=self.monkey_preset_var, width=15, state="readonly")
        size_combo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5)); size_combo.bind("<<ComboboxSelected>>", lambda e: self.handle_monkey_preset())
        tk.Label(paper_frame, text="Width", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(paper_frame, textvariable=self.monkey_w_var, width=6, bg=self.color_pale).grid(row=1, column=1, sticky="w")
        ttk.Combobox(paper_frame, values=["inches", "mm"], textvariable=self.monkey_unit_var, width=6, state="readonly").grid(row=1, column=2, padx=5)
        tk.Label(paper_frame, text="Height", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w", pady=(5,0)); tk.Entry(paper_frame, textvariable=self.monkey_h_var, width=6, bg=self.color_pale).grid(row=2, column=1, sticky="w", pady=(5,0))
        ttk.Checkbutton(paper_frame, text="Landscape", variable=self.monkey_landscape_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5,0))
        order_frame = ttk.LabelFrame(tab, text="Page Order", padding=10); order_frame.pack(fill="x", pady=5)
        ttk.Combobox(order_frame, values=["Sequential", "Step and Repeat"], textvariable=self.monkey_order_var, width=15, state="readonly").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(order_frame, text="Double sided", variable=self.monkey_double_sided_var).grid(row=0, column=1, padx=10)
        tk.Label(order_frame, text="Repeat each page", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w", pady=(5,0)); tk.Entry(order_frame, textvariable=self.monkey_repeat_var, width=6, bg=self.color_pale).grid(row=1, column=1, sticky="w", pady=(5,0))
        layout_frame = ttk.LabelFrame(tab, text="Layout (Auto Max-Fit)", padding=10); layout_frame.pack(fill="x", pady=5)
        tk.Radiobutton(layout_frame, text="[ Z ➔ ] Left-to-Right", variable=self.monkey_direction_var, value="LTR", indicatoron=0, width=18, bg=self.color_pale, fg=self.color_navy, relief="flat").pack(side="left", padx=5)
        tk.Radiobutton(layout_frame, text="[ ⬅ Z ] Right-to-Left", variable=self.monkey_direction_var, value="RTL", indicatoron=0, width=18, bg=self.color_pale, fg=self.color_navy, relief="flat").pack(side="left", padx=5)
        space_frame = ttk.LabelFrame(tab, text="White Space", padding=10); space_frame.pack(fill="x", pady=5)
        tk.Label(space_frame, text="Margins:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(space_frame, textvariable=self.monkey_margin_l_var, width=6, bg=self.color_pale).grid(row=1, column=1, padx=(0,5)); tk.Entry(space_frame, textvariable=self.monkey_margin_t_var, width=6, bg=self.color_pale).grid(row=1, column=2, padx=(0,5))
        tk.Label(space_frame, text="Gutters:", bg=self.color_white, fg=self.color_navy).grid(row=3, column=0, sticky="w"); tk.Entry(space_frame, textvariable=self.monkey_gutter_h_var, width=6, bg=self.color_pale).grid(row=3, column=1, padx=(0,5)); tk.Entry(space_frame, textvariable=self.monkey_gutter_v_var, width=6, bg=self.color_pale).grid(row=3, column=2, padx=(0,5))
        ttk.Checkbutton(space_frame, text="Center output on page", variable=self.monkey_center_var).grid(row=4, column=0, columnspan=4, sticky="w", pady=(5,0))
        marks_frame = ttk.LabelFrame(tab, text="Printer's Marks", padding=10); marks_frame.pack(fill="x", pady=5)
        ttk.Checkbutton(marks_frame, text="Draw perimeter crop marks (Edge-to-edge)", variable=self.monkey_draw_marks_var).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(marks_frame, text="Gap distance:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w", pady=(5,0)); tk.Entry(marks_frame, textvariable=self.monkey_mark_dist_var, width=8, bg=self.color_pale).grid(row=1, column=1, pady=(5,0), padx=5); tk.Label(marks_frame, text="inches", bg=self.color_white, fg=self.color_navy).grid(row=1, column=2, sticky="w", pady=(5,0))
        tk.Label(marks_frame, text="Line thickness:", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w"); tk.Entry(marks_frame, textvariable=self.monkey_mark_thick_var, width=8, bg=self.color_pale).grid(row=2, column=1, padx=5); tk.Label(marks_frame, text="inches", bg=self.color_white, fg=self.color_navy).grid(row=2, column=2, sticky="w")
        self._create_btn(tab, "➕ Add Monkey Imposition", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Monkey Imposition")).pack(fill="x", pady=10)

    def handle_monkey_preset(self):
        val = self.monkey_preset_var.get()
        if val == "12x18": self.monkey_w_var.set("12"); self.monkey_h_var.set("18")
        elif val == "13x19": self.monkey_w_var.set("13"); self.monkey_h_var.set("19")
        elif val == "Letter": self.monkey_w_var.set("8.5"); self.monkey_h_var.set("11")
        elif val == "Tabloid": self.monkey_w_var.set("11"); self.monkey_h_var.set("17")

    def build_grid_tab(self):
        main_frame = ttk.Frame(self.tab_content_frame); self.tabs["Grid"] = main_frame
        canvas = tk.Canvas(main_frame, bg=self.color_white, highlightthickness=0); scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=10); tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tab, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        paper_frame = ttk.LabelFrame(tab, text="Paper Size", padding=10); paper_frame.pack(fill="x", pady=(0, 5))
        size_combo = ttk.Combobox(paper_frame, values=["12x18", "13x19", "Letter", "Tabloid", "Custom"], textvariable=self.grid_preset_var, width=15, state="readonly")
        size_combo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5)); size_combo.bind("<<ComboboxSelected>>", lambda e: self.handle_grid_preset())
        tk.Label(paper_frame, text="Width", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(paper_frame, textvariable=self.grid_w_var, width=6, bg=self.color_pale).grid(row=1, column=1, sticky="w")
        ttk.Combobox(paper_frame, values=["inches", "mm"], textvariable=self.grid_unit_var, width=6, state="readonly").grid(row=1, column=2, padx=5)
        tk.Label(paper_frame, text="Height", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w", pady=(5,0)); tk.Entry(paper_frame, textvariable=self.grid_h_var, width=6, bg=self.color_pale).grid(row=2, column=1, sticky="w", pady=(5,0))
        ttk.Checkbutton(paper_frame, text="Landscape", variable=self.grid_landscape_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5,0))
        order_frame = ttk.LabelFrame(tab, text="Page Order", padding=10); order_frame.pack(fill="x", pady=5)
        ttk.Combobox(order_frame, values=["Sequential", "Step and Repeat"], textvariable=self.grid_order_var, width=15, state="readonly").grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(order_frame, text="Double sided", variable=self.grid_double_sided_var).grid(row=0, column=1, padx=10)
        tk.Label(order_frame, text="Repeat each page", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w", pady=(5,0)); tk.Entry(order_frame, textvariable=self.grid_repeat_var, width=6, bg=self.color_pale).grid(row=1, column=1, sticky="w", pady=(5,0))
        layout_frame = ttk.LabelFrame(tab, text="Layout", padding=10); layout_frame.pack(fill="x", pady=5)
        tk.Label(layout_frame, text="Columns", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w", pady=(5,0)); tk.Entry(layout_frame, textvariable=self.grid_cols_var, width=6, bg=self.color_pale).grid(row=2, column=1, sticky="w", pady=(5,0), padx=(0,10))
        tk.Label(layout_frame, text="Rows", bg=self.color_white, fg=self.color_navy).grid(row=2, column=2, sticky="w", pady=(5,0)); tk.Entry(layout_frame, textvariable=self.grid_rows_var, width=6, bg=self.color_pale).grid(row=2, column=3, sticky="w", pady=(5,0))
        space_frame = ttk.LabelFrame(tab, text="White Space", padding=10); space_frame.pack(fill="x", pady=5)
        tk.Label(space_frame, text="Margins:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(space_frame, textvariable=self.grid_margin_l_var, width=6, bg=self.color_pale).grid(row=1, column=1, padx=(0,5)); tk.Entry(space_frame, textvariable=self.grid_margin_t_var, width=6, bg=self.color_pale).grid(row=1, column=2, padx=(0,5))
        tk.Label(space_frame, text="Gutters:", bg=self.color_white, fg=self.color_navy).grid(row=3, column=0, sticky="w"); tk.Entry(space_frame, textvariable=self.grid_gutter_h_var, width=6, bg=self.color_pale).grid(row=3, column=1, padx=(0,5)); tk.Entry(space_frame, textvariable=self.grid_gutter_v_var, width=6, bg=self.color_pale).grid(row=3, column=2, padx=(0,5))
        ttk.Checkbutton(space_frame, text="Center output on page", variable=self.grid_center_var).grid(row=4, column=0, columnspan=4, sticky="w", pady=(5,0))
        
        marks_frame = ttk.LabelFrame(tab, text="Printer's Marks", padding=10); marks_frame.pack(fill="x", pady=5)
        ttk.Checkbutton(marks_frame, text="Draw perimeter crop marks (Edge-to-edge)", variable=self.grid_draw_marks_var).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(marks_frame, text="Gap distance:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w", pady=(5,0)); tk.Entry(marks_frame, textvariable=self.grid_mark_dist_var, width=8, bg=self.color_pale).grid(row=1, column=1, pady=(5,0), padx=5); tk.Label(marks_frame, text="inches", bg=self.color_white, fg=self.color_navy).grid(row=1, column=2, sticky="w", pady=(5,0))
        tk.Label(marks_frame, text="Line thickness:", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w"); tk.Entry(marks_frame, textvariable=self.grid_mark_thick_var, width=8, bg=self.color_pale).grid(row=2, column=1, padx=5); tk.Label(marks_frame, text="inches", bg=self.color_white, fg=self.color_navy).grid(row=2, column=2, sticky="w")
        self._create_btn(tab, "➕ Add Grid Imposition", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Grid Imposition")).pack(fill="x", pady=10)

    def handle_grid_preset(self):
        val = self.grid_preset_var.get()
        if val == "12x18": self.grid_w_var.set("12"); self.grid_h_var.set("18")
        elif val == "13x19": self.grid_w_var.set("13"); self.grid_h_var.set("19")
        elif val == "Letter": self.grid_w_var.set("8.5"); self.grid_h_var.set("11")
        elif val == "Tabloid": self.grid_w_var.set("11"); self.grid_h_var.set("17")

    def build_booklet_tab(self):
        main_frame = ttk.Frame(self.tab_content_frame); self.tabs["Booklet"] = main_frame
        canvas = tk.Canvas(main_frame, bg=self.color_white, highlightthickness=0); scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=10); tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tab, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        tk.Label(tab, text="Note: Source document page count must be divisible by 4.", bg=self.color_white, fg=self.color_steel, font=("Arial", 10, "bold", "italic")).pack(anchor="w", pady=(0, 10))
        blank_frame = ttk.LabelFrame(tab, text="Pad Document", padding=10); blank_frame.pack(fill="x", pady=(0, 10))
        tk.Label(blank_frame, text="Insert blank page at:", bg=self.color_white, fg=self.color_navy).pack(side="left")
        ttk.Combobox(blank_frame, values=["End of Document", "Beginning of Document", "After Page #"], textvariable=self.blank_pos_var, state="readonly", width=20).pack(side="left", padx=5)
        tk.Entry(blank_frame, textvariable=self.blank_page_num_var, width=5, bg=self.color_pale).pack(side="left", padx=5)
        self._create_btn(blank_frame, "➕ Insert Blank Page", self.color_mint, self.color_navy, lambda: self.add_step_to_queue("Insert Blank Page")).pack(side="right")
        paper_frame = ttk.LabelFrame(tab, text="Paper Size", padding=10); paper_frame.pack(fill="x", pady=(0, 5))
        size_combo = ttk.Combobox(paper_frame, values=["Tabloid (11x17)", "Letter (8.5x11)", "Custom"], textvariable=self.booklet_preset_var, width=18, state="readonly")
        size_combo.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,5)); size_combo.bind("<<ComboboxSelected>>", lambda e: self.handle_booklet_preset())
        tk.Label(paper_frame, text="Width", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(paper_frame, textvariable=self.booklet_w_var, width=6, bg=self.color_pale).grid(row=1, column=1, sticky="w")
        ttk.Combobox(paper_frame, values=["inches", "mm"], textvariable=self.booklet_unit_var, width=6, state="readonly").grid(row=1, column=2, padx=5)
        tk.Label(paper_frame, text="Height", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="w", pady=(5,0)); tk.Entry(paper_frame, textvariable=self.booklet_h_var, width=6, bg=self.color_pale).grid(row=2, column=1, sticky="w", pady=(5,0))
        ttk.Checkbutton(paper_frame, text="Landscape", variable=self.booklet_landscape_var).grid(row=3, column=0, columnspan=3, sticky="w", pady=(5,0))
        space_frame = ttk.LabelFrame(tab, text="White Space", padding=10); space_frame.pack(fill="x", pady=5)
        tk.Label(space_frame, text="Margins:", bg=self.color_white, fg=self.color_navy).grid(row=1, column=0, sticky="w"); tk.Entry(space_frame, textvariable=self.booklet_margin_l_var, width=6, bg=self.color_pale).grid(row=1, column=1, padx=(0,5)); tk.Entry(space_frame, textvariable=self.booklet_margin_t_var, width=6, bg=self.color_pale).grid(row=1, column=2, padx=(0,5))
        tk.Label(space_frame, text="Center Gutter:", bg=self.color_white, fg=self.color_navy).grid(row=2, column=0, sticky="e", pady=(5,0)); tk.Entry(space_frame, textvariable=self.booklet_center_gutter_var, width=6, bg=self.color_pale).grid(row=2, column=1, pady=(5,0), padx=(0,5))
        tk.Label(space_frame, text="Page Creep:", bg=self.color_white, fg=self.color_navy).grid(row=3, column=0, sticky="e", pady=(5,0)); tk.Entry(space_frame, textvariable=self.booklet_creep_var, width=6, bg=self.color_pale).grid(row=3, column=1, pady=(5,0), padx=(0,5))
        ttk.Radiobutton(space_frame, text="Creep Outward", variable=self.booklet_creep_dir_var, value="Outward").grid(row=4, column=1, columnspan=3, sticky="w")
        ttk.Radiobutton(space_frame, text="Creep Inward", variable=self.booklet_creep_dir_var, value="Inward").grid(row=5, column=1, columnspan=3, sticky="w")
        ttk.Checkbutton(space_frame, text="Center output on page", variable=self.booklet_center_var).grid(row=6, column=0, columnspan=4, sticky="w", pady=(5,0))
        self._create_btn(tab, "➕ Add Booklet Step", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Booklet Spread")).pack(fill="x", pady=10)

    def handle_booklet_preset(self):
        val = self.booklet_preset_var.get()
        if "Tabloid" in val: self.booklet_w_var.set("17"); self.booklet_h_var.set("11")
        elif "Letter" in val: self.booklet_w_var.set("11"); self.booklet_h_var.set("8.5")

    def build_cutter_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Cutter"] = tab
        marks_frame = ttk.LabelFrame(tab, text="Registration Marks", padding=10); marks_frame.pack(fill="x", pady=5)
        row1 = ttk.Frame(marks_frame); row1.pack(fill="x", pady=2)
        tk.Label(row1, text="Size:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(row1, textvariable=self.cutter_size_var, width=6, bg=self.color_pale).pack(side="left", padx=5)
        tk.Label(row1, text="Thickness:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(row1, textvariable=self.cutter_thick_var, width=6, bg=self.color_pale).pack(side="left", padx=5)
        row2 = ttk.Frame(marks_frame); row2.pack(fill="x", pady=8)
        ttk.Combobox(row2, values=["Inside", "Outside"], textvariable=self.cutter_placement_var, width=8, state="readonly").pack(side="left")
        tk.Label(row2, text="Media box", bg=self.color_white, fg=self.color_navy).pack(side="left", padx=5)
        row3 = ttk.Frame(marks_frame); row3.pack(fill="x", pady=2)
        tk.Label(row3, text="Margins:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(row3, textvariable=self.cutter_margin_var, width=6, bg=self.color_pale).pack(side="left", padx=5)
        row4 = ttk.Frame(marks_frame); row4.pack(fill="x", pady=8)
        tk.Label(row4, text="Pages:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(row4, textvariable=self.cutter_pages_var, width=15, bg=self.color_pale).pack(side="left", padx=5)
        art_frame = ttk.LabelFrame(tab, text="Artwork", padding=10); art_frame.pack(fill="x", pady=10)
        ttk.Checkbutton(art_frame, text="Remove artwork (create a cut-marks only file)", variable=self.cutter_remove_art_var).pack(anchor="w")
        self._create_btn(tab, "➕ Add Cutter Marks", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Cutter Marks")).pack(fill="x", side="bottom", pady=10)

    def build_color_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Color"] = tab
        mode_frame = ttk.LabelFrame(tab, text="Color Space Conversion", padding=10); mode_frame.pack(fill="x", pady=5)
        modes = [("Keep Original Document Colors", "Keep Original"), ("Grayscale (256 Levels)", "Grayscale"),
                 ("Black & White (High Contrast)", "BW"), ("CMYK (Commercial Print)", "CMYK"), ("RGB (Digital/Web)", "RGB")]
        for text, val in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.color_mode_var, value=val, indicatoron=0, width=40, bg=self.color_pale, fg=self.color_navy, selectcolor=self.color_mint, relief="flat", font=("Arial", 10)).pack(anchor="w", pady=3)
        res_frame = ttk.LabelFrame(tab, text="Rasterization Resolution", padding=10); res_frame.pack(fill="x", pady=10)
        dpi_row = tk.Frame(res_frame, bg=self.color_white); dpi_row.pack(fill="x")
        tk.Label(dpi_row, text="Target DPI:", bg=self.color_white, fg=self.color_navy, font=("Arial", 10, "bold")).pack(side="left")
        ttk.Combobox(dpi_row, values=["300", "400", "600", "1200"], textvariable=self.color_dpi_var, width=10, state="readonly", font=("Arial", 10)).pack(side="left", padx=10)
        self._create_btn(tab, "➕ Add Color Conversion", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Color Conversion")).pack(fill="x", side="bottom", pady=10)

    def build_rotate_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Rotate"] = tab
        rot_frame = ttk.LabelFrame(tab, text="Rotate Pages Control", padding=12); rot_frame.pack(fill="x", pady=5)
        rot_row = ttk.Frame(rot_frame); rot_row.pack(fill="x")
        tk.Entry(rot_row, textvariable=self.rotate_deg_var, width=8, justify="center", bg=self.color_pale).pack(side="left")
        tk.Label(rot_row, text="degrees", bg=self.color_white, fg=self.color_navy).pack(side="left", padx=5)
        tk.Label(rot_frame, text="Pages Selector Filter: ", bg=self.color_white, fg=self.color_navy).pack(anchor="w", pady=(4,0))
        tk.Entry(rot_frame, textvariable=self.rotate_pages_var, bg=self.color_pale).pack(fill="x", pady=2)
        self._create_btn(rot_frame, "➕ Add Rotation Step", self.color_steel, self.color_white, lambda: self.add_step_to_queue("Rotate Pages")).pack(fill="x", pady=8)

    def build_preflight_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Preflight"] = tab
        self._create_btn(tab, "🔍 Run Preflight Analysis", self.color_lime, self.color_navy, self.run_preflight).pack(fill="x", pady=5)
        report_frame = ttk.LabelFrame(tab, text="Preflight Report", padding=10); report_frame.pack(fill="both", expand=True, pady=10)
        self.report_text = tk.Text(report_frame, bg=self.color_navy, fg=self.color_lime, font=("Courier", 10), wrap="word", state="disabled", relief="flat", padx=10, pady=10)
        self.report_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(report_frame, command=self.report_text.yview); scroll.pack(side="right", fill="y")
        self.report_text.config(yscrollcommand=scroll.set)

    def build_batch_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Automation"] = tab
        dir_frame = ttk.LabelFrame(tab, text="Folder Setup", padding=10); dir_frame.pack(fill="x", pady=5)
        r1 = tk.Frame(dir_frame, bg=self.color_white); r1.pack(fill="x", pady=5)
        tk.Label(r1, text="Input Folder:", bg=self.color_white, fg=self.color_navy, width=12, anchor="w").pack(side="left"); tk.Entry(r1, textvariable=self.batch_in_var, bg=self.color_pale).pack(side="left", fill="x", expand=True, padx=5)
        self._create_btn(r1, "Browse", self.color_mint, self.color_navy, lambda: self.batch_in_var.set(filedialog.askdirectory())).pack(side="left")
        r2 = tk.Frame(dir_frame, bg=self.color_white); r2.pack(fill="x", pady=5)
        tk.Label(r2, text="Output Folder:", bg=self.color_white, fg=self.color_navy, width=12, anchor="w").pack(side="left"); tk.Entry(r2, textvariable=self.batch_out_var, bg=self.color_pale).pack(side="left", fill="x", expand=True, padx=5)
        self._create_btn(r2, "Browse", self.color_mint, self.color_navy, lambda: self.batch_out_var.set(filedialog.askdirectory())).pack(side="left")
        r3 = tk.Frame(dir_frame, bg=self.color_white); r3.pack(fill="x", pady=5)
        tk.Label(r3, text="Recipe (.json):", bg=self.color_white, fg=self.color_navy, width=12, anchor="w").pack(side="left"); tk.Entry(r3, textvariable=self.batch_recipe_var, bg=self.color_pale).pack(side="left", fill="x", expand=True, padx=5)
        self._create_btn(r3, "Browse", self.color_mint, self.color_navy, lambda: self.batch_recipe_var.set(filedialog.askopenfilename(filetypes=[("JSON Recipe", "*.json")]))).pack(side="left")
        action_frame = ttk.LabelFrame(tab, text="Execution", padding=10); action_frame.pack(fill="both", expand=True, pady=10)
        self.btn_batch = self._create_btn(action_frame, "▶ Run Batch Once", self.color_steel, self.color_white, self.run_batch); self.btn_batch.pack(fill="x", pady=5)
        self.btn_watch = self._create_btn(action_frame, "🔥 Start Hot Folder Watch", self.color_lime, self.color_navy, self.toggle_watch); self.btn_watch.pack(fill="x", pady=5)

    def build_vdp_tab(self):
        main_frame = ttk.Frame(self.tab_content_frame); self.tabs["VDP"] = main_frame
        canvas = tk.Canvas(main_frame, bg=self.color_white, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        tab = ttk.Frame(canvas, padding=10); tab.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=tab, anchor="nw"); canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True); scrollbar.pack(side="right", fill="y")
        csv_frame = ttk.LabelFrame(tab, text="1. Link Data Source", padding=10); csv_frame.pack(fill="x", pady=(0,5))
        r1 = tk.Frame(csv_frame, bg=self.color_white); r1.pack(fill="x")
        tk.Entry(r1, textvariable=self.vdp_csv_path_var, bg=self.color_pale, state="readonly").pack(side="left", fill="x", expand=True, padx=(0,5))
        self._create_btn(r1, "Browse CSV", self.color_mint, self.color_navy, self.load_vdp_csv).pack(side="left")
        map_frame = ttk.LabelFrame(tab, text="2. Map Field", padding=10); map_frame.pack(fill="x", pady=5)
        r_type = tk.Frame(map_frame, bg=self.color_white); r_type.pack(fill="x", pady=2)
        tk.Label(r_type, text="Data Column:", bg=self.color_white, fg=self.color_navy, width=12, anchor="w").pack(side="left")
        self.vdp_header_combo = ttk.Combobox(r_type, textvariable=self.vdp_col_var, state="readonly", width=15); self.vdp_header_combo.pack(side="left", padx=5)
        tk.Label(r_type, text="Inject As:", bg=self.color_white, fg=self.color_navy).pack(side="left", padx=5)
        ttk.Combobox(r_type, values=["Text", "QR Code"], textvariable=self.vdp_type_var, state="readonly", width=10).pack(side="left", padx=5)
        r_pos = tk.Frame(map_frame, bg=self.color_white); r_pos.pack(fill="x", pady=8)
        tk.Label(r_pos, text="Position (Inches):", bg=self.color_white, fg=self.color_navy, width=15, anchor="w").pack(side="left")
        tk.Label(r_pos, text="X:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(r_pos, textvariable=self.vdp_x_var, width=6, bg=self.color_pale).pack(side="left", padx=2)
        tk.Label(r_pos, text="Y:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(r_pos, textvariable=self.vdp_y_var, width=6, bg=self.color_pale).pack(side="left", padx=2)
        tk.Label(r_pos, text="Box W:", bg=self.color_white, fg=self.color_navy).pack(side="left", padx=(10,0)); tk.Entry(r_pos, textvariable=self.vdp_w_var, width=6, bg=self.color_pale).pack(side="left", padx=2)
        tk.Label(r_pos, text="Box H:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(r_pos, textvariable=self.vdp_h_var, width=6, bg=self.color_pale).pack(side="left", padx=2)
        self._create_btn(r_pos, "🎯 Click to Target", self.color_steel, self.color_white, self.activate_target_mode).pack(side="left", padx=15)
        r_format = tk.Frame(map_frame, bg=self.color_white); r_format.pack(fill="x", pady=2)
        tk.Label(r_format, text="Rich Text:", bg=self.color_white, fg=self.color_navy, width=12, anchor="w").pack(side="left")
        local_fonts = list(tkfont.families()); local_fonts.sort()
        font_combo = ttk.Combobox(r_format, values=local_fonts, textvariable=self.vdp_font_var, state="readonly", width=15); font_combo.pack(side="left", padx=5)
        tk.Label(r_format, text="Size:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(r_format, textvariable=self.vdp_size_var, width=4, bg=self.color_pale).pack(side="left", padx=2)
        tk.Label(r_format, text="Align:", bg=self.color_white, fg=self.color_navy).pack(side="left"); ttk.Combobox(r_format, values=["Left", "Center", "Right"], textvariable=self.vdp_align_var, state="readonly", width=6).pack(side="left", padx=2)
        tk.Label(r_format, text="Hex:", bg=self.color_white, fg=self.color_navy).pack(side="left"); tk.Entry(r_format, textvariable=self.vdp_color_var, width=8, bg=self.color_pale).pack(side="left", padx=2)
        self._create_btn(map_frame, "➕ Add Field Mapping", self.color_mint, self.color_navy, self.add_vdp_mapping).pack(fill="x", pady=(15, 0))
        list_frame = ttk.LabelFrame(tab, text="3. Applied Mappings", padding=10); list_frame.pack(fill="x", pady=5)
        self.vdp_mapped_listbox = tk.Listbox(list_frame, height=5, bg=self.color_pale, fg=self.color_navy, selectbackground=self.color_steel, relief="flat", highlightthickness=1); self.vdp_mapped_listbox.pack(fill="both", expand=True, pady=(0,5))
        self._create_btn(list_frame, "🗑️ Remove Selected Field", self.color_steel, self.color_white, self.remove_vdp_mapping).pack(fill="x")
        self._create_btn(tab, "✅ Add Mail Merge Step to Stack", self.color_lime, self.color_navy, lambda: self.add_step_to_queue("VDP Mail Merge")).pack(fill="x", pady=10)

    def build_unlock_tab(self):
        tab = ttk.Frame(self.tab_content_frame, padding=15); self.tabs["Unlock"] = tab
        setup_f = ttk.LabelFrame(tab, text="Decryption Setup", padding=10); setup_f.pack(fill="x", pady=5)
        r1 = tk.Frame(setup_f, bg=self.color_white); r1.pack(fill="x", pady=5)
        tk.Label(r1, text="Target File:", bg=self.color_white, fg=self.color_navy, width=15, anchor="w").pack(side="left")
        tk.Entry(r1, textvariable=self.unlock_source_var, bg=self.color_pale, state="readonly").pack(side="left", fill="x", expand=True, padx=5)
        self._create_btn(r1, "Select PDF", self.color_mint, self.color_navy, lambda: self.unlock_source_var.set(filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")]))).pack(side="left")
        r2 = tk.Frame(setup_f, bg=self.color_white); r2.pack(fill="x", pady=5)
        tk.Label(r2, text="Password (If any):", bg=self.color_white, fg=self.color_navy, width=15, anchor="w").pack(side="left")
        tk.Entry(r2, textvariable=self.unlock_pass_var, bg=self.color_pale).pack(side="left", fill="x", expand=True, padx=5)
        self._create_btn(tab, "🔓 Strip Security & Save Unlocked Copy", self.color_lime, self.color_navy, self.execute_standalone_unlock).pack(fill="x", pady=15)

    def execute_standalone_unlock(self):
        src_path = self.unlock_source_var.get(); pw = self.unlock_pass_var.get()
        if not src_path:
            messagebox.showwarning("Missing Input", "Please select a target PDF file first.")
            return
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile="Unlocked_Output.pdf", filetypes=[("PDF Files", "*.pdf")])
        if not out_path: return
        try:
            doc = fitz.open(src_path)
            if doc.is_encrypted:
                if not doc.authenticate(pw):
                    messagebox.showerror("Authentication Failure", "Invalid password provided for this encrypted file.")
                    doc.close(); return
            clean_doc = fitz.open(); clean_doc.insert_pdf(doc)
            clean_doc.save(out_path, garbage=4, deflate=True, clean=True)
            clean_doc.close(); doc.close()
            messagebox.showinfo("Success", f"All restriction tokens purged. File saved to:\n{out_path}")
        except Exception as e: messagebox.showerror("Decryption Crash", str(e))

    def load_vdp_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.vdp_csv_path_var.set(path)
            try:
                with open(path, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.reader(f); headers = next(reader)
                    self.vdp_headers = [h.strip() for h in headers if h.strip()]
                    self.vdp_header_combo.config(values=self.vdp_headers)
                    if self.vdp_headers: self.vdp_header_combo.current(0)
            except Exception as e: messagebox.showerror("CSV Error", f"Could not read headers:\n{e}")

    def activate_target_mode(self):
        if not self.preview_doc:
            messagebox.showwarning("No Document", "Load a PDF first to target coordinates."); return
        self.vdp_target_mode = True; self.root.config(cursor="crosshair")

    def on_canvas_click(self, event):
        if getattr(self, 'vdp_target_mode', False) and self.preview_doc:
            x_scroll = self.preview_canvas.canvasx(0); y_scroll = self.preview_canvas.canvasy(0)
            actual_x = event.x + x_scroll; actual_y = event.y + y_scroll
            img_x_start = self.preview_pos_x - (self.preview_img_w / 2.0); img_y_start = self.preview_pos_y - (self.preview_img_h / 2.0)
            click_img_x = actual_x - img_x_start; click_img_y = actual_y - img_y_start
            
            if 0 <= click_img_x <= self.preview_img_w and 0 <= click_img_y <= self.preview_img_h:
                pdf_x = click_img_x / self.preview_final_scale; pdf_y = click_img_y / self.preview_final_scale
                self.vdp_x_var.set(f"{pdf_x / 72.0:.3f}"); self.vdp_y_var.set(f"{pdf_y / 72.0:.3f}")
        self.vdp_target_mode = False; self.root.config(cursor="")

    def add_vdp_mapping(self):
        col = self.vdp_col_var.get()
        if not col:
            messagebox.showwarning("Missing Data", "Please select a Data Column."); return
        mapping = {
            "column": col, "type": self.vdp_type_var.get(), "x": self.vdp_x_var.get(), "y": self.vdp_y_var.get(),
            "w": self.vdp_w_var.get(), "h": self.vdp_h_var.get(), "font": self.vdp_font_var.get(), 
            "size": self.vdp_size_var.get(), "align": self.vdp_align_var.get(), "color": self.vdp_color_var.get()
        }
        self.vdp_mapped_fields.append(mapping)
        self.vdp_mapped_listbox.insert(tk.END, f"[{mapping['type']}] {col} -> Pos: {mapping['x']}, {mapping['y']}")

    def remove_vdp_mapping(self):
        sel = self.vdp_mapped_listbox.curselection()
        if sel:
            idx = sel[0]; self.vdp_mapped_listbox.delete(idx); self.vdp_mapped_fields.pop(idx)

    # --- BUG REPORTER INTEGRATION ---
    def open_feedback_form(self):
        fb_win = tk.Toplevel(self.root)
        fb_win.title("Submit Feedback"); fb_win.geometry("450x450")
        fb_win.configure(bg=self.color_white); fb_win.transient(self.root); fb_win.grab_set()

        tk.Label(fb_win, text="Help us improve ReadySetPDF!", font=("Arial", 14, "bold"), bg=self.color_white, fg=self.color_navy).pack(pady=(15, 5))
        
        f1 = tk.Frame(fb_win, bg=self.color_white); f1.pack(fill="x", padx=20, pady=5)
        tk.Label(f1, text="Category:", bg=self.color_white, fg=self.color_navy, width=10, anchor="w").pack(side="left")
        type_var = tk.StringVar(value="Bug Report")
        ttk.Combobox(f1, values=["Bug Report", "Feature Request", "General Feedback"], textvariable=type_var, state="readonly", width=25).pack(side="left")

        f2 = tk.Frame(fb_win, bg=self.color_white); f2.pack(fill="x", padx=20, pady=5)
        tk.Label(f2, text="Your Email:", bg=self.color_white, fg=self.color_navy, width=10, anchor="w").pack(side="left")
        email_var = tk.StringVar()
        tk.Entry(f2, textvariable=email_var, bg=self.color_pale, width=30).pack(side="left")

        tk.Label(fb_win, text="Message / Description:", bg=self.color_white, fg=self.color_navy).pack(anchor="w", padx=20, pady=(10, 0))
        msg_box = tk.Text(fb_win, height=10, bg=self.color_pale, fg=self.color_navy, font=("Arial", 10), relief="flat", highlightthickness=1, highlightbackground=self.color_steel)
        msg_box.pack(fill="both", expand=True, padx=20, pady=5)

        def send_data():
            msg = msg_box.get("1.0", "end-1c").strip()
            if not msg:
                messagebox.showwarning("Empty Message", "Please enter a message before submitting.", parent=fb_win)
                return
            btn_submit.config(text="Sending...", state="disabled"); fb_win.update()
            
            webhook_url = "https://formspree.io/f/xqevaono" 
            data = urllib.parse.urlencode({"Category": type_var.get(), "Email": email_var.get(), "Message": msg}).encode("utf-8")

            try:
                req = urllib.request.Request(webhook_url, data=data)
                urllib.request.urlopen(req)
                messagebox.showinfo("Success", "Your feedback has been sent successfully. Thank you!", parent=fb_win)
                fb_win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to send feedback. Please check your internet connection.\n\n{e}", parent=fb_win)
                btn_submit.config(text="📨 Send Feedback", state="normal")

        btn_submit = self._create_btn(fb_win, "📨 Send Feedback", self.color_lime, self.color_navy, send_data)
        btn_submit.pack(pady=15, fill="x", padx=20)

    # --- ENGINE & PIPELINE ---
    def _get_step_display_text(self, step_data):
        stype = step_data["type"]; params = step_data.get("params", {})
        if stype == "Crop Margin": return f"📏 Crop: L:{params.get('left')} T:{params.get('top')} R:{params.get('right')} B:{params.get('bottom')}"
        elif stype == "Resize": return f"📐 Resize: {params.get('preset')}"
        elif stype == "Insert Blank Page":
            pos = params.get('position')
            return f"📄 Insert Blank Page (After Pg {params.get('page_num')})" if pos == "After Page #" else f"📄 Insert Blank Page ({pos})"
        elif stype == "Color Conversion":
            return "🎨 Color: Keep Original" if params.get('mode') == "Keep Original" else f"🎨 Color: {params.get('mode')} ({params.get('dpi')} DPI)"
        elif stype == "Monkey Imposition": return "🐒 Monkey: Max-Fit"
        elif stype == "Grid Imposition": return f"🔲 Grid: {params.get('cols')}x{params.get('rows')}"
        elif stype == "Booklet Spread": return f"📖 Booklet: {params.get('sheet_w')}x{params.get('sheet_h')}"
        elif stype == "Cutter Marks": return "✂️ Cutter Marks"
        elif stype == "Rotate Pages": return f"🔄 Rotate: {params.get('angle')}°"
        elif stype == "VDP Mail Merge": return f"🏷️ VDP Mail Merge ({os.path.basename(params.get('csv_path', ''))})"
        return stype

    def add_step_to_queue(self, step_type):
        if not self.files:
            messagebox.showwarning("No Assets", "Load source PDF documents first."); return
        step_data = {"type": step_type}
        
        if step_type == "Crop Margin":
            step_data["params"] = {
                "left": self.crop_left_var.get(), "top": self.crop_top_var.get(),
                "right": self.crop_right_var.get(), "bottom": self.crop_bottom_var.get(), "unit": self.crop_unit_var.get()
            }
        elif step_type == "Resize":
            step_data["params"] = {
                "preset": self.resize_preset_var.get(), "w": self.resize_w_var.get(), "h": self.resize_h_var.get(), 
                "unit": self.resize_unit_var.get(), "landscape": self.resize_landscape_var.get(), "stretch": self.resize_stretch_var.get()
            }
        elif step_type == "Insert Blank Page":
            step_data["params"] = {"position": self.blank_pos_var.get(), "page_num": self.blank_page_num_var.get()}
        elif step_type == "Color Conversion":
            step_data["params"] = {"mode": self.color_mode_var.get(), "dpi": self.color_dpi_var.get()}
        elif step_type == "Monkey Imposition":
            step_data["params"] = {
                "sheet_w": self.monkey_w_var.get(), "sheet_h": self.monkey_h_var.get(), "landscape": self.monkey_landscape_var.get(), 
                "repeat": self.monkey_repeat_var.get(), "margin_l": self.monkey_margin_l_var.get(), "margin_t": self.monkey_margin_t_var.get(),
                "gutter_h": self.monkey_gutter_h_var.get(), "gutter_v": self.monkey_gutter_v_var.get(), "center": self.monkey_center_var.get(), 
                "draw_marks": self.monkey_draw_marks_var.get(), "mark_dist": self.monkey_mark_dist_var.get(), "mark_thick": self.monkey_mark_thick_var.get(), 
                "direction": self.monkey_direction_var.get()
            }
        elif step_type == "Grid Imposition":
            step_data["params"] = {
                "cols": self.grid_cols_var.get(), "rows": self.grid_rows_var.get(), "sheet_w": self.grid_w_var.get(), 
                "sheet_h": self.grid_h_var.get(), "landscape": self.grid_landscape_var.get(), "repeat": self.grid_repeat_var.get(),
                "margin_l": self.grid_margin_l_var.get(), "margin_t": self.grid_margin_t_var.get(), "gutter_h": self.grid_gutter_h_var.get(), 
                "gutter_v": self.grid_gutter_v_var.get(), "center": self.grid_center_var.get(), "draw_marks": self.grid_draw_marks_var.get(),
                "mark_dist": self.grid_mark_dist_var.get(), "mark_thick": self.grid_mark_thick_var.get()
            }
        elif step_type == "Booklet Spread":
            step_data["params"] = {
                "sheet_w": self.booklet_w_var.get(), "sheet_h": self.booklet_h_var.get(), "landscape": self.booklet_landscape_var.get(),
                "margin_l": self.booklet_margin_l_var.get(), "margin_t": self.booklet_margin_t_var.get(), "center_gutter": self.booklet_center_gutter_var.get(), 
                "creep_val": self.booklet_creep_var.get(), "creep_dir": self.booklet_creep_dir_var.get(), "center": self.booklet_center_var.get(),
            }
        elif step_type == "Cutter Marks":
            step_data["params"] = {
                "size": self.cutter_size_var.get(), "thick": self.cutter_thick_var.get(), "placement": self.cutter_placement_var.get(), 
                "margin": self.cutter_margin_var.get(), "pages": self.cutter_pages_var.get(), "remove_art": self.cutter_remove_art_var.get()
            }
        elif step_type == "Rotate Pages":
            step_data["params"] = {"angle": self.rotate_deg_var.get(), "pages": self.rotate_pages_var.get()}
        elif step_type == "VDP Mail Merge":
            if not self.vdp_csv_path_var.get() or not self.vdp_mapped_fields:
                messagebox.showwarning("VDP Error", "You must load a CSV and map at least one field."); return
            step_data["params"] = {"csv_path": self.vdp_csv_path_var.get(), "fields": list(self.vdp_mapped_fields)}

        display_text = self._get_step_display_text(step_data)

        if self.active_history_index != -1 and self.active_history_index < len(self.action_queue) - 1:
            insert_pos = self.active_history_index + 1
            self.action_queue.insert(insert_pos, step_data)
            self.queue_box.insert(insert_pos, display_text)
            self.active_history_index = insert_pos
        else:
            self.action_queue.append(step_data)
            self.queue_box.insert(tk.END, display_text)
            self.active_history_index = len(self.action_queue) - 1

        self.queue_box.selection_clear(0, tk.END); self.queue_box.selection_set(self.active_history_index)
        self.render_live_preview()

    def _execute_pipeline(self, active_doc, action_queue, preview_mode=False):
        for step in action_queue:
            stype = step["type"]; params = step["params"]
            if stype == "Crop Margin":
                next_doc = fitz.open()
                for page in active_doc:
                    left = self.convert_to_points(params["left"], params.get("unit", "inches"))
                    top = self.convert_to_points(params["top"], params.get("unit", "inches"))
                    right = self.convert_to_points(params["right"], params.get("unit", "inches"))
                    bottom = self.convert_to_points(params["bottom"], params.get("unit", "inches"))
                    r = page.rect
                    new_w = max(1.0, r.width - left - right); new_h = max(1.0, r.height - top - bottom)
                    new_p = next_doc.new_page(width=new_w, height=new_h)
                    target_rect = fitz.Rect(-left, -top, -left + r.width, -top + r.height)
                    new_p.show_pdf_page(target_rect, active_doc, page.number)
                active_doc.close(); active_doc = next_doc
                
            elif stype == "VDP Mail Merge":
                csv_path = params.get("csv_path"); fields = params.get("fields", [])
                if not os.path.exists(csv_path): continue
                rows = []
                with open(csv_path, mode='r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for r in reader: rows.append(r)
                if preview_mode: rows = rows[:3]
                next_doc = fitz.open()
                for row in rows:
                    for page in active_doc:
                        w, h = page.rect.width, page.rect.height
                        new_p = next_doc.new_page(width=w, height=h)
                        new_p.show_pdf_page(new_p.rect, active_doc, page.number)
                        for field in fields:
                            val = str(row.get(field["column"], ""))
                            f_type = field.get("type", "Text")
                            x = float(field.get("x", 0)) * 72.0; y = float(field.get("y", 0)) * 72.0
                            w_box = float(field.get("w", 2.0)) * 72.0; h_box = float(field.get("h", 0.5)) * 72.0
                            rect = fitz.Rect(x, y, x + w_box, y + h_box)
                            if f_type == "Text":
                                align_str = field.get("align", "Left"); align_val = 0
                                if align_str == "Center": align_val = 1
                                elif align_str == "Right": align_val = 2
                                color_val = self._hex_to_rgb(field.get("color", "#000000"))
                                f_name = field.get("font", "helv")
                                try: new_p.insert_textbox(rect, val, fontname=f_name, fontsize=float(field.get("size", 12)), color=color_val, align=align_val)
                                except Exception: new_p.insert_textbox(rect, val, fontname="helv", fontsize=float(field.get("size", 12)), color=color_val, align=align_val)
                            elif f_type == "QR Code":
                                if not QR_AVAILABLE:
                                    new_p.insert_textbox(rect, "[QR Missing - pip install qrcode[pil]]", color=(1,0,0)); continue
                                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=0)
                                qr.add_data(val); qr.make(fit=True)
                                img = qr.make_image(fill_color="black", back_color="white")
                                img_bytes = io.BytesIO(); img.save(img_bytes, format='PNG')
                                new_p.insert_image(rect, stream=img_bytes.getvalue())
                active_doc.close(); active_doc = next_doc
            
            elif stype == "Insert Blank Page":
                next_doc = fitz.open()
                pos = params.get("position", "End of Document")
                try: pnum = int(params.get("page_num", "1")) - 1
                except ValueError: pnum = len(active_doc) - 1
                if len(active_doc) == 0: next_doc.new_page(width=612, height=792)
                else:
                    for p_idx, page in enumerate(active_doc):
                        w, h = page.rect.width, page.rect.height
                        if pos == "Beginning of Document" and p_idx == 0: next_doc.new_page(width=w, height=h)
                        new_p = next_doc.new_page(width=w, height=h)
                        new_p.show_pdf_page(new_p.rect, active_doc, page.number)
                        if pos == "After Page #" and p_idx == pnum: next_doc.new_page(width=w, height=h)
                    if pos == "End of Document":
                        last_p = active_doc[-1]
                        next_doc.new_page(width=last_p.rect.width, height=last_p.rect.height)
                active_doc.close(); active_doc = next_doc
                
            elif stype == "Color Conversion":
                next_doc = fitz.open()
                mode = params.get("mode", "Grayscale"); dpi = int(params.get("dpi", 300))
                for page in active_doc:
                    w, h = page.rect.width, page.rect.height
                    new_p = next_doc.new_page(width=w, height=h)
                    if mode == "Keep Original": new_p.show_pdf_page(new_p.rect, active_doc, page.number)
                    else:
                        cs = fitz.csGRAY
                        if mode == "CMYK": cs = fitz.csCMYK
                        elif mode == "RGB": cs = fitz.csRGB
                        pix = page.get_pixmap(colorspace=cs, dpi=dpi, alpha=False)
                        new_p.insert_image(new_p.rect, pixmap=pix)
                active_doc.close(); active_doc = next_doc

            elif stype == "Resize":
                next_doc = fitz.open()
                for page in active_doc:
                    w, h = page.rect.width, page.rect.height
                    tw = self.convert_to_points(params["w"], params["unit"])
                    th = self.convert_to_points(params["h"], params["unit"])
                    if params.get("landscape", False) and tw < th: tw, th = th, tw
                    new_p = next_doc.new_page(width=tw, height=th)
                    if params.get("stretch", False): dest = new_p.rect
                    else:
                        sc = min(tw / w, th / h)
                        fw, fh = w * sc, h * sc
                        dest = fitz.Rect((tw - fw)/2, (th - fh)/2, (tw - fw)/2 + fw, (th - fh)/2 + fh)
                    new_p.show_pdf_page(dest, active_doc, page.number)
                active_doc.close(); active_doc = next_doc

            elif stype == "Monkey Imposition":
                next_doc = fitz.open()
                sw, sh = float(params["sheet_w"])*72.0, float(params["sheet_h"])*72.0
                if params.get("landscape", False) and sw < sh: sw, sh = sh, sw
                g_h = float(params["gutter_h"])*72.0; g_v = float(params["gutter_v"])*72.0
                m_l = float(params["margin_l"])*72.0; m_t = float(params["margin_t"])*72.0
                center = params["center"]; draw_marks = params.get("draw_marks", True)
                m_dist = float(params.get("mark_dist", "0.125")) * 72.0
                m_thick = float(params.get("mark_thick", "0.007")) * 72.0
                
                pw, ph = active_doc[0].rect.width, active_doc[0].rect.height
                cols = max(1, int((sw - 2*m_l + g_h) / (pw + g_h + 0.001)))
                rows = max(1, int((sh - 2*m_t + g_v) / (ph + g_v + 0.001)))
                direction = params.get("direction", "LTR")
                
                page_sequence = []
                for p_idx in range(len(active_doc)):
                    for _ in range(int(params.get("repeat", 1))): page_sequence.append(p_idx)

                cells_per_sheet = cols * rows
                if cells_per_sheet > 0:
                    for i in range(0, len(page_sequence), cells_per_sheet):
                        new_p = next_doc.new_page(width=sw, height=sh)
                        chunk = page_sequence[i:i+cells_per_sheet]
                        
                        cut_xs, cut_ys = set(), set()
                        grid_x0, grid_y0 = sw, sh
                        grid_x1, grid_y1 = 0, 0

                        for idx, src_page_num in enumerate(chunk):
                            r = idx // cols
                            c = idx % cols if direction == "LTR" else cols - 1 - (idx % cols)
                            if center:
                                total_grid_w = (pw * cols) + (g_h * (cols - 1)); total_grid_h = (ph * rows) + (g_v * (rows - 1))
                                start_x = (sw - total_grid_w) / 2.0; start_y = (sh - total_grid_h) / 2.0
                            else: start_x, start_y = m_l, m_t
                                
                            x0 = start_x + c * (pw + g_h); y0 = start_y + r * (ph + g_v)
                            x1, y1 = x0 + pw, y0 + ph
                            new_p.show_pdf_page(fitz.Rect(x0, y0, x1, y1), active_doc, src_page_num)
                            
                            if draw_marks:
                                cut_xs.update([x0, x1]); cut_ys.update([y0, y1])
                                grid_x0 = min(grid_x0, x0); grid_y0 = min(grid_y0, y0)
                                grid_x1 = max(grid_x1, x1); grid_y1 = max(grid_y1, y1)

                        if draw_marks and cut_xs and cut_ys:
                            for cx in cut_xs:
                                new_p.draw_line(fitz.Point(cx, grid_y0 - m_dist), fitz.Point(cx, 0), color=(0,0,0), width=m_thick)
                                new_p.draw_line(fitz.Point(cx, grid_y1 + m_dist), fitz.Point(cx, sh), color=(0,0,0), width=m_thick)
                            for cy in cut_ys:
                                new_p.draw_line(fitz.Point(grid_x0 - m_dist, cy), fitz.Point(0, cy), color=(0,0,0), width=m_thick)
                                new_p.draw_line(fitz.Point(grid_x1 + m_dist, cy), fitz.Point(sw, cy), color=(0,0,0), width=m_thick)

                active_doc.close(); active_doc = next_doc
                
            elif stype == "Grid Imposition":
                next_doc = fitz.open()
                cols, rows = int(params["cols"]), int(params["rows"])
                sw, sh = float(params["sheet_w"])*72.0, float(params["sheet_h"])*72.0
                if params.get("landscape", False) and sw < sh: sw, sh = sh, sw
                g_h = float(params["gutter_h"])*72.0; g_v = float(params["gutter_v"])*72.0
                m_l = float(params["margin_l"])*72.0; m_t = float(params["margin_t"])*72.0
                center = params["center"]; draw_marks = params.get("draw_marks", True)
                m_dist = float(params.get("mark_dist", "0.125")) * 72.0
                m_thick = float(params.get("mark_thick", "0.007")) * 72.0
                
                page_sequence = []
                for p_idx in range(len(active_doc)):
                    for _ in range(int(params.get("repeat", 1))): page_sequence.append(p_idx)

                cells_per_sheet = cols * rows
                if cells_per_sheet > 0:
                    for i in range(0, len(page_sequence), cells_per_sheet):
                        new_p = next_doc.new_page(width=sw, height=sh)
                        chunk = page_sequence[i:i+cells_per_sheet]

                        cut_xs, cut_ys = set(), set()
                        grid_x0, grid_y0 = sw, sh
                        grid_x1, grid_y1 = 0, 0

                        for idx, src_page_num in enumerate(chunk):
                            r, c = idx // cols, idx % cols
                            pw, ph = active_doc[src_page_num].rect.width, active_doc[src_page_num].rect.height
                            if center:
                                total_grid_w = (pw * cols) + (g_h * (cols - 1)); total_grid_h = (ph * rows) + (g_v * (rows - 1))
                                start_x = (sw - total_grid_w) / 2.0; start_y = (sh - total_grid_h) / 2.0
                            else: start_x, start_y = m_l, m_t
                                
                            x0 = start_x + c * (pw + g_h); y0 = start_y + r * (ph + g_v)
                            x1, y1 = x0 + pw, y0 + ph
                            new_p.show_pdf_page(fitz.Rect(x0, y0, x1, y1), active_doc, src_page_num)

                            if draw_marks:
                                cut_xs.update([x0, x1]); cut_ys.update([y0, y1])
                                grid_x0 = min(grid_x0, x0); grid_y0 = min(grid_y0, y0)
                                grid_x1 = max(grid_x1, x1); grid_y1 = max(grid_y1, y1)

                        if draw_marks and cut_xs and cut_ys:
                            for cx in cut_xs:
                                new_p.draw_line(fitz.Point(cx, grid_y0 - m_dist), fitz.Point(cx, 0), color=(0,0,0), width=m_thick)
                                new_p.draw_line(fitz.Point(cx, grid_y1 + m_dist), fitz.Point(cx, sh), color=(0,0,0), width=m_thick)
                            for cy in cut_ys:
                                new_p.draw_line(fitz.Point(grid_x0 - m_dist, cy), fitz.Point(0, cy), color=(0,0,0), width=m_thick)
                                new_p.draw_line(fitz.Point(grid_x1 + m_dist, cy), fitz.Point(sw, cy), color=(0,0,0), width=m_thick)

                active_doc.close(); active_doc = next_doc
                
            elif stype == "Booklet Spread":
                next_doc = fitz.open()
                sw = float(params.get("sheet_w", 17)) * 72.0
                sh = float(params.get("sheet_h", 11)) * 72.0
                if params.get("landscape", False) and sw < sh: sw, sh = sh, sw
                center_gutter = float(params.get("center_gutter", 0)) * 72.0
                margin_l = float(params.get("margin_l", 0)) * 72.0
                margin_t = float(params.get("margin_t", 0)) * 72.0
                center_mode = params.get("center", True)
                total_creep = float(params.get("creep_val", 0)) * 72.0
                creep_dir = params.get("creep_dir", "Outward")
                
                if len(active_doc) % 4 != 0:
                    for _ in range(4 - (len(active_doc) % 4)): active_doc.new_page()
                    
                total_p = len(active_doc); total_sheets = total_p // 4; half_w = sw / 2.0
                
                for s_idx in range(total_p // 2):
                    sheet_num = s_idx // 2
                    is_back = (s_idx % 2 == 1)
                    if not is_back: pl, pr = total_p - 1 - (sheet_num * 2), sheet_num * 2
                    else: pl, pr = (sheet_num * 2) + 1, total_p - 2 - (sheet_num * 2)
                        
                    new_p = next_doc.new_page(width=sw, height=sh)
                    creep_step = total_creep * (sheet_num / (total_sheets - 1)) if total_sheets > 1 and total_creep != 0 else 0.0
                    shift = center_gutter/2 + creep_step if creep_dir == "Inward" else center_gutter/2 - creep_step
                    
                    src_l = active_doc[pl].rect; src_r = active_doc[pr].rect
                    pw_l, ph_l = src_l.width, src_l.height; pw_r, ph_r = src_r.width, src_r.height
                    
                    if center_mode:
                        start_y_l, start_y_r = (sh - ph_l) / 2.0, (sh - ph_r) / 2.0
                        start_x_l, start_x_r = half_w - pw_l - shift, half_w + shift
                    else:
                        start_y_l, start_y_r = margin_t, margin_t
                        start_x_l, start_x_r = margin_l, half_w + shift + margin_l
                        
                    src_l_rect = fitz.Rect(active_doc[pl].rect)
                    tgt_l_rect = fitz.Rect(start_x_l, start_y_l, start_x_l + pw_l, start_y_l + ph_l)
                    if tgt_l_rect.x1 > half_w:
                        diff = tgt_l_rect.x1 - half_w
                        tgt_l_rect.x1 -= diff; src_l_rect.x1 -= diff
                    if tgt_l_rect.x0 < 0:
                        diff = 0 - tgt_l_rect.x0
                        tgt_l_rect.x0 += diff; src_l_rect.x0 += diff
                    if tgt_l_rect.width > 0 and tgt_l_rect.height > 0:
                        new_p.show_pdf_page(tgt_l_rect, active_doc, pl, clip=src_l_rect)

                    src_r_rect = fitz.Rect(active_doc[pr].rect)
                    tgt_r_rect = fitz.Rect(start_x_r, start_y_r, start_x_r + pw_r, start_y_r + ph_r)
                    if tgt_r_rect.x0 < half_w:
                        diff = half_w - tgt_r_rect.x0
                        tgt_r_rect.x0 += diff; src_r_rect.x0 += diff
                    if tgt_r_rect.x1 > sw:
                        diff = tgt_r_rect.x1 - sw
                        tgt_r_rect.x1 -= diff; src_r_rect.x1 -= diff
                    if tgt_r_rect.width > 0 and tgt_r_rect.height > 0:
                        new_p.show_pdf_page(tgt_r_rect, active_doc, pr, clip=src_r_rect)

                active_doc.close(); active_doc = next_doc

            elif stype == "Cutter Marks":
                next_doc = fitz.open()
                targets = self.parse_page_selection(params["pages"], len(active_doc))
                c_size = float(params["size"]) * 72.0; c_thick = float(params["thick"]) * 72.0
                c_margin = float(params["margin"]) * 72.0
                placement = params["placement"]; remove_art = params["remove_art"]

                for r_idx, page in enumerate(active_doc):
                    w, h = page.rect.width, page.rect.height
                    new_p = next_doc.new_page(width=w, height=h)
                    is_target = r_idx in targets
                    if not (remove_art and is_target): new_p.show_pdf_page(new_p.rect, active_doc, page.number)
                    if is_target:
                        m_l, m_r = c_margin, w - c_margin; m_t, m_b = c_margin, h - c_margin
                        d = c_size if placement == "Inside" else -c_size 
                        new_p.draw_line(fitz.Point(m_l, m_t), fitz.Point(m_l + d, m_t), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_l, m_t), fitz.Point(m_l, m_t + d), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_r, m_t), fitz.Point(m_r - d, m_t), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_r, m_t), fitz.Point(m_r, m_t + d), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_l, m_b), fitz.Point(m_l + d, m_b), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_l, m_b), fitz.Point(m_l, m_b - d), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_r, m_b), fitz.Point(m_r - d, m_b), width=c_thick, color=(0,0,0))
                        new_p.draw_line(fitz.Point(m_r, m_b), fitz.Point(m_r, m_b - d), width=c_thick, color=(0,0,0))
                active_doc.close(); active_doc = next_doc
                
            elif stype == "Rotate Pages":
                next_doc = fitz.open()
                angle = int(params["angle"]); targets = self.parse_page_selection(params["pages"], len(active_doc))
                for r_idx, page in enumerate(active_doc):
                    if r_idx in targets: page.set_rotation((page.rotation + angle) % 360)
                    new_p = next_doc.new_page(width=page.rect.width, height=page.rect.height)
                    new_p.show_pdf_page(new_p.rect, active_doc, page.number)
                active_doc.close(); active_doc = next_doc
                    
        return active_doc

    def compile_current_stack(self, flattening=False, preview_mode=False):
        if not self.files: return None
        active_doc = fitz.open()
        
        for p in self.files:
            ext = p.lower().split('.')[-1]
            if ext in ['png', 'jpg', 'jpeg', 'tif', 'tiff']:
                img_doc = fitz.open(p)
                pdf_bytes = img_doc.convert_to_pdf()
                src = fitz.open("pdf", pdf_bytes)
                img_doc.close()
                active_doc.insert_pdf(src)
                src.close()
            else:
                src = fitz.open(p)
                active_doc.insert_pdf(src)
                src.close()
                
        for page in active_doc:
            cb = page.cropbox
            page.set_mediabox(cb)
            page.set_bleedbox(cb)
            page.set_trimbox(cb)
            page.set_artbox(cb)
            if flattening: 
                try: page.flatten_annotations() 
                except Exception: pass
            
        end_point = len(self.action_queue) if self.active_history_index == -1 else self.active_history_index + 1
        return self._execute_pipeline(active_doc, self.action_queue[:end_point], preview_mode=preview_mode)

    def toggle_watch(self):
        if self.is_watching:
            self.is_watching = False
            self.btn_watch.config(text="🔥 Start Hot Folder Watch", bg=self.color_lime, fg=self.color_navy)
            self.btn_batch.config(state="normal")
        else:
            if not self.batch_in_var.get() or not self.batch_out_var.get() or not self.batch_recipe_var.get():
                messagebox.showwarning("Missing Info", "Set Input, Output, and Recipe first.")
                return
            self.is_watching = True
            self.btn_watch.config(text="⏹ Stop Auto-Watch Folder", bg=self.color_steel, fg=self.color_white)
            self.btn_batch.config(state="disabled")
            self.poll_hot_folder()

    def poll_hot_folder(self):
        if self.is_watching:
            in_dir = self.batch_in_var.get()
            if os.path.exists(in_dir):
                files = [f for f in os.listdir(in_dir) if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
                if files:
                    self.run_batch(silent=True)
            self.root.after(5000, self.poll_hot_folder)

    def run_batch(self, silent=False):
        in_dir = self.batch_in_var.get(); out_dir = self.batch_out_var.get(); recipe_path = self.batch_recipe_var.get()
        if not in_dir or not out_dir or not recipe_path:
            if not silent: messagebox.showwarning("Missing Info", "Please select Input, Output, and Recipe.")
            return
        try:
            with open(recipe_path, 'r') as f: recipe = json.load(f)
        except Exception as e:
            if not silent: messagebox.showerror("Recipe Error", str(e))
            return
        if not os.path.exists(in_dir): return
        files = [f for f in os.listdir(in_dir) if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'))]
        if not files: return
        done_dir = os.path.join(in_dir, "Processed_Originals"); os.makedirs(done_dir, exist_ok=True)
        success_count = 0
        for fname in files:
            in_path = os.path.join(in_dir, fname)
            out_path = os.path.join(out_dir, f"Processed_{os.path.splitext(fname)[0]}.pdf")
            try:
                active_doc = fitz.open()
                ext = in_path.lower().split('.')[-1]
                if ext in ['png', 'jpg', 'jpeg', 'tif', 'tiff']:
                    img_doc = fitz.open(in_path)
                    pdf_bytes = img_doc.convert_to_pdf()
                    src = fitz.open("pdf", pdf_bytes); img_doc.close(); active_doc.insert_pdf(src); src.close()
                else:
                    src = fitz.open(in_path); active_doc.insert_pdf(src); src.close()
                for page in active_doc:
                    cb = page.cropbox; page.set_mediabox(cb); page.set_bleedbox(cb); page.set_trimbox(cb); page.set_artbox(cb)
                final_doc = self._execute_pipeline(active_doc, recipe, preview_mode=False)
                final_doc.save(out_path, garbage=4, deflate=True, clean=True)
                final_doc.close()
                dest_path = os.path.join(done_dir, fname)
                if os.path.exists(dest_path): os.remove(dest_path)
                shutil.move(in_path, dest_path); success_count += 1
            except Exception as e: print(e)
        if not silent: messagebox.showinfo("Batch Complete", f"Successfully processed {success_count} files.")

    def run_preflight(self):
        if not self.files:
            messagebox.showwarning("No Assets", "Load source PDF documents first.")
            return
        self.report_text.config(state="normal")
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "Analyzing document pipeline...\n\n")
        self.root.update_idletasks()
        doc = self.compile_current_stack(flattening=False, preview_mode=True)
        if not doc: return
        report = [f"=== READYSETPDF PREFLIGHT REPORT ===", f"Total Pages: {len(doc)}\n"]
        has_rgb, has_cmyk, low_res_images, fonts_used = False, False, [], set()
        for pno in range(len(doc)):
            page = doc[pno]
            report.append(f"Page {pno + 1}: {page.rect.width/72:.2f}\" x {page.rect.height/72:.2f}\"")
            for f in page.get_fonts(): fonts_used.add(f[3]) 
            for img in page.get_image_info(xrefs=True):
                cs = img.get("colorspace")
                if cs == 3: has_rgb = True
                elif cs == 4: has_cmyk = True
                xref = img.get("xref")
                if xref:
                    try:
                        rects = page.get_image_rects(xref)
                        for r in rects:
                            rect_w_in = r.width / 72.0
                            if rect_w_in > 0:
                                dpi = img.get("width") / rect_w_in
                                if dpi < 250: low_res_images.append((pno + 1, dpi))
                    except: pass
        report.append("\n=== COLOR SPACE ===")
        if has_rgb: report.append("⚠️ WARNING: RGB color space detected.\n   (Consider adding a 'Color Conversion -> CMYK' step)")
        elif has_cmyk: report.append("✅ PASS: CMYK color space detected. No RGB found.")
        else: report.append("✅ PASS: Grayscale/Monochrome document.")
        report.append("\n=== IMAGE RESOLUTION ===")
        if low_res_images:
            report.append(f"⚠️ WARNING: {len(low_res_images)} low-resolution image instances (< 250 DPI).")
            for p, d in low_res_images: report.append(f"   - Page {p}: ~{int(d)} DPI")
        else: report.append("✅ PASS: All image instances are >= 250 DPI.")
        report.append("\n=== FONTS DETECTED ===")
        if fonts_used:
            for f in sorted(list(fonts_used)): report.append(f"   - {f}")
        else: report.append("   No fonts detected. (Fully rasterized or pure vector art)")
        report.append("\n--- END OF REPORT ---")
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(tk.END, "\n".join(report))
        self.report_text.config(state="disabled")
        doc.close()

    def save_recipe(self):
        if not self.action_queue: return
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Recipe", "*.json")])
        if path:
            try:
                with open(path, 'w') as f: json.dump(self.action_queue, f, indent=4)
                messagebox.showinfo("Success", "Recipe saved successfully.")
            except Exception as e: messagebox.showerror("Error", f"Failed to save recipe:\n{e}")

    def load_recipe(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Recipe", "*.json")])
        if path:
            try:
                with open(path, 'r') as f: data = json.load(f)
                if isinstance(data, list):
                    self.action_queue = data
                    self.queue_box.delete(0, tk.END)
                    for step in self.action_queue: self.queue_box.insert(tk.END, self._get_step_display_text(step))
                    self.active_history_index = len(self.action_queue) - 1
                    if self.active_history_index >= 0: self.queue_box.selection_set(self.active_history_index)
                    self.render_live_preview()
            except Exception as e: messagebox.showerror("Error", f"Failed to load recipe:\n{e}")

    def show_export_dialog(self):
        if not self.files:
            messagebox.showwarning("Empty Project", "No input files loaded.")
            return
        export_win = tk.Toplevel(self.root)
        export_win.title("Final Production Export"); export_win.geometry("500x420")
        export_win.configure(bg=self.color_white); export_win.transient(self.root); export_win.grab_set()
        tk.Label(export_win, text="Final Output Options", font=("Arial", 14, "bold"), bg=self.color_white, fg=self.color_navy).pack(pady=15)
        stamp_frame = ttk.LabelFrame(export_win, text="Visual Proofing Options", padding=10); stamp_frame.pack(fill="x", padx=15, pady=5)
        cb_stamp = ttk.Checkbutton(stamp_frame, text="Apply Production Proof Watermark *", variable=self.apply_stamp_var); cb_stamp.pack(anchor="w")
        tk.Label(stamp_frame, text="Watermark Text:", bg=self.color_white, fg=self.color_navy).pack(anchor="w", pady=(5,0))
        tk.Entry(stamp_frame, textvariable=self.stamp_text_var, font=("Arial", 11), fg="red", bg=self.color_pale).pack(fill="x", pady=2)
        sec_frame = ttk.LabelFrame(export_win, text="Document Security Lock", padding=10); sec_frame.pack(fill="x", padx=15, pady=10)
        cb_lock1 = ttk.Checkbutton(sec_frame, text="🔒 Print Lock (Disable Physical Printing) *", variable=self.lock_print_var); cb_lock1.pack(anchor="w", pady=2)
        cb_lock2 = ttk.Checkbutton(sec_frame, text="🔒 Edit Lock (Disable Extraction/Modifications) *", variable=self.lock_edit_var); cb_lock2.pack(anchor="w", pady=2)
        tk.Label(sec_frame, text="Master Password (Visible to avoid typos):", bg=self.color_white, fg=self.color_navy).pack(anchor="w", pady=(5,0))
        tk.Entry(sec_frame, textvariable=self.custom_owner_pw_var, bg=self.color_pale).pack(fill="x")
        self._create_btn(export_win, "💾 Choose Path & Save File", self.color_steel, self.color_white, lambda: self.execute_final_save(export_win)).pack(pady=20, fill="x", padx=15)

    def execute_final_save(self, window):
        base_origin_name = os.path.splitext(os.path.basename(self.files[0]))[0]
        suggested_filename = f"{base_origin_name}_readysetpdf.pdf"
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=suggested_filename, filetypes=[("PDF Files", "*.pdf")])
        if not out_path: return
        window.destroy()
        
        final_doc = self.compile_current_stack(flattening=True, preview_mode=False)
        if not final_doc: return
        
        if self.apply_stamp_var.get():
            temp_bytes = final_doc.tobytes(garbage=3)
            final_doc.close()
            final_doc = fitz.open("pdf", temp_bytes)
            stamp_text = self.stamp_text_var.get()
            for page in final_doc:
                w, h = page.rect.width, page.rect.height
                try: page.insert_text(fitz.Point(w * 0.10, h * 0.50), stamp_text, fontsize=min(w, h) * 0.10, color=(0.85, 0.2, 0.2), fontname="helv", fill_opacity=0.30)
                except Exception: page.insert_text(fitz.Point(w * 0.10, h * 0.50), stamp_text, fontsize=min(w, h) * 0.10, color=(0.95, 0.5, 0.5), fontname="helv")
                page.clean_contents()
        try:
            if self.lock_print_var.get() or self.lock_edit_var.get() or self.custom_owner_pw_var.get().strip() != "readysetpdf":
                perm_mask = fitz.PDF_PERM_ACCESSIBILITY
                if not self.lock_print_var.get(): perm_mask |= fitz.PDF_PERM_PRINT
                if not self.lock_edit_var.get(): perm_mask |= (fitz.PDF_PERM_MODIFY | fitz.PDF_PERM_ANNOTATE | fitz.PDF_PERM_COPY)
                owner_pass = self.custom_owner_pw_var.get().strip() or "readysetpdf"
                final_doc.save(out_path, garbage=4, deflate=True, clean=True, owner_pw=owner_pass, user_pw="", permissions=perm_mask, encryption=fitz.PDF_ENCRYPT_AES_128)
            else:
                final_doc.save(out_path, garbage=4, deflate=True, clean=True)
            final_doc.close()
            messagebox.showinfo("Success", f"Secured production layout successfully generated:\n{out_path}")
        except Exception as e: messagebox.showerror("Save Failure", str(e))

    def render_live_preview(self):
        self.preview_canvas.delete("all")
        if self.preview_doc: 
            self.preview_doc.close()
            self.preview_doc = None
            
        if not self.files:
            self.preview_page_label.config(text="Spread: 0 / 0")
            self.history_status_label.config(text="Viewing: Original Baseline")
            return

        if self.active_history_index == -1: 
            self.active_history_index = len(self.action_queue) - 1 if self.action_queue else -1
            
        self.preview_doc = self.compile_current_stack(flattening=False, preview_mode=True)
        
        if not self.action_queue or self.active_history_index == -1: 
            self.history_status_label.config(text="Viewing: Original Baseline", fg=self.color_steel)
        else: 
            self.history_status_label.config(text=f"Viewing Step State Slice: [ {self.queue_box.get(self.active_history_index)} ]", fg=self.color_navy)

        if not self.preview_doc or len(self.preview_doc) == 0: 
            return
        if self.current_preview_page >= len(self.preview_doc): 
            self.current_preview_page = len(self.preview_doc) - 1
            
        page = self.preview_doc[self.current_preview_page]
        zoom_str = self.preview_zoom_var.get()
        zoom_factor = 1.5 if "1.5x" in zoom_str else 2.0 if "2.0x" in zoom_str else 3.0 if "3.0x" in zoom_str else 1.0
        
        self.root.update_idletasks()
        c_width = self.preview_container.winfo_width()
        c_height = self.preview_container.winfo_height()
        if c_width < 10: 
            c_width = 700
            c_height = 600
        
        base_scale = min((c_width - 40) / page.rect.width, (c_height - 40) / page.rect.height)
        self.preview_final_scale = base_scale * zoom_factor
        
        pix = page.get_pixmap(matrix=fitz.Matrix(self.preview_final_scale, self.preview_final_scale), annots=True)
        self.preview_image = tk.PhotoImage(data=pix.tobytes("png"))
        self.preview_img_w, self.preview_img_h = pix.width, pix.height
        self.preview_canvas.config(scrollregion=(0, 0, max(c_width, self.preview_img_w), max(c_height, self.preview_img_h)))
        self.preview_pos_x = max(c_width, self.preview_img_w) / 2.0
        self.preview_pos_y = max(c_height, self.preview_img_h) / 2.0
        
        self.preview_canvas.create_image(self.preview_pos_x, self.preview_pos_y, image=self.preview_image)
        self.preview_page_label.config(text=f"Sheet Page Layout View: {self.current_preview_page + 1} / {len(self.preview_doc)}")

    def navigate_preview(self, direction):
        if not self.preview_doc: 
            return
        target = self.current_preview_page + direction
        if 0 <= target < len(self.preview_doc):
            self.current_preview_page = target
            self.render_live_preview()

    def handle_history_selection(self, event):
        selected = self.queue_box.curselection()
        if not selected: 
            return
        self.active_history_index = selected[0]
        self.current_preview_page = 0
        self.render_live_preview()

    def move_queue_step(self, direction):
        selected = self.queue_box.curselection()
        if not selected: 
            return
        old_idx = selected[0]
        new_idx = old_idx + direction
        if 0 <= new_idx < len(self.action_queue):
            self.action_queue[old_idx], self.action_queue[new_idx] = self.action_queue[new_idx], self.action_queue[old_idx]
            texts = self.queue_box.get(0, tk.END)
            self.queue_box.delete(0, tk.END)
            for idx, text in enumerate(texts):
                if idx == old_idx: 
                    self.queue_box.insert(tk.END, texts[new_idx])
                elif idx == new_idx: 
                    self.queue_box.insert(tk.END, texts[old_idx])
                else: 
                    self.queue_box.insert(tk.END, text)
            self.queue_box.selection_set(new_idx)
            self.active_history_index = new_idx
            self.render_live_preview()

    def remove_queue_step(self):
        selected = self.queue_box.curselection()
        if not selected: 
            return
        idx = selected[0]
        self.action_queue.pop(idx)
        self.queue_box.delete(idx)
        self.active_history_index = max(0, idx - 1) if self.action_queue else -1
        if self.active_history_index != -1: 
            self.queue_box.selection_set(self.active_history_index)
        self.render_live_preview()

    def clear_queue(self):
        self.action_queue.clear()
        self.queue_box.delete(0, tk.END)
        self.active_history_index = -1
        self.render_live_preview()

    def export_as_images(self):
        if not self.preview_doc: 
            return
        folder = filedialog.askdirectory(title="Select Destination Directory")
        if not folder: 
            return
        for idx in range(len(self.preview_doc)):
            pix = self.preview_doc[idx].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            pix.save(os.path.join(folder, f"ReadySetPDF_Proof_Spread_{idx+1}.png"))
        messagebox.showinfo("Proofs Generated", "PNG mockups generated.")

    def load_pdfs(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF & Images", "*.pdf *.png *.jpg *.jpeg *.tif *.tiff")])
        if files:
            self.files.extend([f for f in files if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'))])
            self.refresh_file_list()

    def drop_files(self, event):
        files = self.root.tk.splitlist(event.data)
        self.files.extend([f.strip('{}') for f in files if f.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'))])
        self.refresh_file_list()

    def refresh_file_list(self):
        self.file_list.delete(0, tk.END)
        for f in self.files: 
            self.file_list.insert(tk.END, os.path.basename(f))
        self.current_preview_page = 0
        self.active_history_index = len(self.action_queue) - 1 if self.action_queue else -1
        self.render_live_preview()

    def clear_files(self):
        self.files.clear()
        self.file_list.delete(0, tk.END)
        self.clear_queue()

if __name__ == "__main__":
    app = ReadySetPDFApp()
    app.root.update()
    app.render_live_preview()
    app.root.mainloop()