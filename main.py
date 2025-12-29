from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader, PdfWriter
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image
from tkinter import filedialog
import os
import webbrowser

# ---------- APP CONFIG ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("PDF Toolkit")
app.geometry("1000x600")
app.resizable(False, False)

# ---------- GLOBAL STATE ----------
current_theme = "dark"
dpi_value = ctk.IntVar(value=200)
ocr_language = ctk.StringVar(value="eng")
recent_files = []

# ---------- HELPERS ----------
def add_recent_file(path):
    if path and path not in recent_files:
        recent_files.append(path)

def clear_content():
    for w in content.winfo_children():
        w.destroy()

def back_button(parent):
    return ctk.CTkButton(
        parent,
        text="← Back to Dashboard",
        command=show_home,
        height=32,
        fg_color="gray40",
        hover_color="gray30"
    )

# ---------- ICON LOADER ----------
def load_icons(theme):
    prefix = "L" if theme == "light" else ""
    base = os.path.join(os.path.dirname(__file__), "icons")

    try:
        return {
            "split": ctk.CTkImage(Image.open(f"{base}\\{prefix}split.png"), size=(20, 20)),
            "merge": ctk.CTkImage(Image.open(f"{base}\\{prefix}merge.png"), size=(20, 20)),
            "image": ctk.CTkImage(Image.open(f"{base}\\{prefix}image.png"), size=(20, 20)),
            "ocr": ctk.CTkImage(Image.open(f"{base}\\{prefix}ocr.png"), size=(20, 20)),
            "set": ctk.CTkImage(Image.open(f"{base}\\{prefix}set.png"), size=(20, 20)),
        }
    except FileNotFoundError:
        return {k: None for k in ["split", "merge", "image", "ocr", "set"]}

icons = load_icons("dark")

# ---------- PROGRESS UI ----------
def create_progress_ui(title):
    clear_content()
    back_button(content).pack(anchor="e", pady=(0, 10))

    ctk.CTkLabel(
        content, text=title,
        font=ctk.CTkFont(size=22, weight="bold")
    ).pack(anchor="w", pady=(10, 20))

    status = ctk.CTkLabel(content, text="Starting...", text_color="gray")
    status.pack(anchor="w", pady=(0, 10))

    bar = ctk.CTkProgressBar(content, width=400)
    bar.set(0)
    bar.pack(anchor="w")

    return status, bar

# ---------- SPLIT DIALOG ----------
def split_dialog(parent, total_pages, file_size_mb):
    result = {"value": None}

    dialog = ctk.CTkToplevel(parent)
    dialog.title("Split PDF")
    dialog.geometry("400x280")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    frame = ctk.CTkFrame(dialog)
    frame.pack(expand=True, fill="both", padx=20, pady=20)

    ctk.CTkLabel(frame, text="Split PDF", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", pady=(0, 10))
    ctk.CTkLabel(frame, text=f"Pages: {total_pages}\nSize: {file_size_mb:.2f} MB", text_color="gray").pack(anchor="w", pady=(0, 20))

    ctk.CTkLabel(frame, text="Pages per split").pack(anchor="w")
    pages_var = ctk.StringVar(value="1")
    entry = ctk.CTkEntry(frame, textvariable=pages_var, width=120)
    entry.pack(anchor="w", pady=(5, 10))

    error = ctk.CTkLabel(frame, text="", text_color="red")
    error.pack(anchor="w")

    def confirm():
        try:
            v = int(pages_var.get())
            if 1 <= v <= total_pages:
                result["value"] = v
                dialog.destroy()
            else:
                error.configure(text="Invalid number")
        except:
            error.configure(text="Enter a number")

    ctk.CTkButton(frame, text="Cancel", command=dialog.destroy).pack(side="right", padx=5)
    ctk.CTkButton(frame, text="Split", command=confirm).pack(side="right")

    parent.wait_window(dialog)
    return result["value"]

# ---------- PDF OPERATIONS ----------
def split_pdf():
    pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if not pdf_path:
        return
    add_recent_file(pdf_path)

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    size_mb = os.path.getsize(pdf_path) / (1024 * 1024)

    pages_per_split = split_dialog(app, total_pages, size_mb)
    if not pages_per_split:
        return

    output_dir = filedialog.askdirectory()
    if not output_dir:
        return

    status, bar = create_progress_ui("Splitting PDF")

    for start in range(0, total_pages, pages_per_split):
        writer = PdfWriter()
        end = min(start + pages_per_split, total_pages)
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out = os.path.join(output_dir, f"part_{start//pages_per_split+1}.pdf")
        with open(out, "wb") as f:
            writer.write(f)

        bar.set(end / total_pages)
        status.configure(text=f"Processed pages {start+1}-{end}")
        app.update_idletasks()

    messagebox.showinfo("Done", "PDF split successfully.")
    show_home()

def merge_pdfs():
    pdfs = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
    if len(pdfs) < 2:
        return
    for p in pdfs:
        add_recent_file(p)

    out = filedialog.asksaveasfilename(defaultextension=".pdf")
    if not out:
        return

    status, bar = create_progress_ui("Merging PDFs")
    writer = PdfWriter()
    total = len(pdfs)

    for i, pdf in enumerate(pdfs, start=1):
        reader = PdfReader(pdf)
        for page in reader.pages:
            writer.add_page(page)

        bar.set(i / total)
        status.configure(text=f"Merged {i}/{total}")
        app.update_idletasks()

    with open(out, "wb") as f:
        writer.write(f)

    messagebox.showinfo("Done", "PDFs merged successfully.")
    show_home()

def pdf_to_images():
    pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if not pdf:
        return
    add_recent_file(pdf)

    out_dir = filedialog.askdirectory()
    if not out_dir:
        return

    pages = convert_from_path(pdf, dpi=dpi_value.get())
    status, bar = create_progress_ui("Converting PDF to Images")

    for i, page in enumerate(pages, start=1):
        page.save(os.path.join(out_dir, f"page_{i}.png"))
        bar.set(i / len(pages))
        status.configure(text=f"Saved page {i}")
        app.update_idletasks()

    messagebox.showinfo("Done", "Images created.")
    show_home()

def extract_text_ocr():
    pdf = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if not pdf:
        return
    add_recent_file(pdf)

    out = filedialog.asksaveasfilename(defaultextension=".txt")
    if not out:
        return

    pages = convert_from_path(pdf, dpi=200)
    status, bar = create_progress_ui("Extracting Text (OCR)")
    text = []

    for i, page in enumerate(pages, start=1):
        text.append(pytesseract.image_to_string(page, lang=ocr_language.get()))
        bar.set(i / len(pages))
        status.configure(text=f"OCR page {i}")
        app.update_idletasks()

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n\n".join(text))

    messagebox.showinfo("Done", "Text extracted.")
    show_home()

# ---------- SIDEBAR ----------
sidebar = ctk.CTkFrame(app, width=220)
sidebar.pack(side="left", fill="y")

ctk.CTkLabel(sidebar, text="PDF Toolkit", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

def sb(text, key, cmd):
    return ctk.CTkButton(sidebar, text=text, image=icons[key], compound="left", command=cmd, height=42)

sb(" Split PDF", "split", split_pdf).pack(fill="x", padx=20, pady=6)
sb(" Merge PDFs", "merge", merge_pdfs).pack(fill="x", padx=20, pady=6)
sb(" PDF to Images", "image", pdf_to_images).pack(fill="x", padx=20, pady=6)
sb(" Extract Text (OCR)", "ocr", extract_text_ocr).pack(fill="x", padx=20, pady=6)

ctk.CTkLabel(sidebar, text="—").pack(pady=10)
sb(" Settings", "set", lambda: messagebox.showinfo("Settings", "Already implemented")).pack(fill="x", padx=20)

# ---------- MAIN ----------
main = ctk.CTkFrame(app)
main.pack(expand=True, fill="both")

content = ctk.CTkFrame(main)
content.pack(expand=True, fill="both", padx=30, pady=30)

# ---------- HOME ----------
def show_home():
    clear_content()
    ctk.CTkLabel(content, text="PDF Toolkit", font=ctk.CTkFont(size=34, weight="bold")).pack(anchor="w")
    ctk.CTkLabel(content, text="Created by bywzn", text_color="gray").pack(anchor="w", pady=(0, 20))

    ctk.CTkButton(
        content,
        text="View on GitHub",
        command=lambda: webbrowser.open("https://github.com/bywzn")
    ).pack(anchor="w", pady=(0, 30))

    ctk.CTkLabel(content, text="Recent Files", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")

    if not recent_files:
        ctk.CTkLabel(content, text="No recent files yet.", text_color="gray").pack(anchor="w")
    else:
        for f in recent_files[-5:][::-1]:
            ctk.CTkLabel(content, text=os.path.basename(f), text_color="gray").pack(anchor="w")

show_home()
app.mainloop()
