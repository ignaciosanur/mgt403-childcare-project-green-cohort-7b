"""
Build the PS4 Q2 write-up as a Word document (and a PDF exported by Microsoft Word, on macOS).

  PS4_Q2_writeup.md  --pandoc (reference_ps4.docx styles)-->  PS4_Q2_writeup.docx  --Word-->  PS4_Q2_writeup.pdf

pandoc writes LaTeX math as native Word equations and footnotes as Word footnotes. Afterwards, every paragraph
inside the footnotes (including table cells, which pandoc styles "Compact") is switched to the "Footnote Text"
style, which is dark grey and 8.5 pt.

Run:  python3 build_docx.py            (use --no-pdf to skip the Word export)
"""
import os
import re
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
MD = os.path.join(HERE, "PS4_Q2_writeup.md")
DOCX = os.path.join(HERE, "PS4_Q2_writeup.docx")
PDF = os.path.join(HERE, "PS4_Q2_writeup.pdf")
REF = os.path.join(HERE, "reference_ps4.docx")

subprocess.run(["pandoc", MD, "--reference-doc", REF, "--resource-path", HERE, "-o", DOCX], check=True)

# restyle footnote paragraphs
with zipfile.ZipFile(DOCX) as z:
    files = {n: z.read(n) for n in z.namelist()}
fn = files["word/footnotes.xml"].decode("utf8")
fn = re.sub(r'<w:pStyle w:val="(Compact|BodyText|FirstParagraph)" />', '<w:pStyle w:val="FootnoteText" />', fn)
files["word/footnotes.xml"] = fn.encode("utf8")
with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as z:
    for n, data in files.items():
        z.writestr(n, data)
print("wrote", DOCX)

if "--no-pdf" not in sys.argv and sys.platform == "darwin":
    if os.path.exists(PDF):
        os.remove(PDF)
    script = f'''with timeout of 120 seconds
tell application "Microsoft Word"
  open (POSIX file "{DOCX}")
  delay 4
  save as active document file name "{PDF}" file format format PDF
  close active document saving no
end tell
end timeout'''
    subprocess.run(["osascript", "-e", script], check=True)
    # Word stamps the local user's name as PDF author; replace it with the team label
    try:
        import pypdf
        r, w = pypdf.PdfReader(PDF), pypdf.PdfWriter()
        for page in r.pages:
            w.add_page(page)
        w.add_metadata({"/Title": "MGT 403 — Problem Set 4, Question 2: The Distribution of Childcare Prices",
                        "/Author": "MGT 403 Green Cohort Team 7B", "/Creator": "Microsoft Word"})
        with open(PDF, "wb") as f:
            w.write(f)
    except ImportError:
        print("pypdf not installed: PDF author metadata left as set by Word")
    print("wrote", PDF)
