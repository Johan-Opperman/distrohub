"""Generate a branded one-page install/update guide PDF for a single distro."""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Preformatted,
                                HRFlowable)

NAVY=colors.HexColor("#0f1b2d"); CYAN=colors.HexColor("#17a2b8")
SLATE=colors.HexColor("#33475b"); CODEBG=colors.HexColor("#f4f6f8")
CODEBD=colors.HexColor("#d5dde3"); MUTED=colors.HexColor("#7a8896")

ss=getSampleStyleSheet()
H1=ParagraphStyle("H1",parent=ss["Heading2"],textColor=NAVY,fontSize=12.5,spaceBefore=11,
                  spaceAfter=3,fontName="Helvetica-Bold")
BODY=ParagraphStyle("BODY",parent=ss["Normal"],fontSize=9.5,leading=13.6,textColor=SLATE,spaceAfter=4)
STEP=ParagraphStyle("STEP",parent=BODY,leftIndent=6)
CODE=ParagraphStyle("CODE",parent=ss["Code"],fontName="Courier",fontSize=8,leading=11,textColor=NAVY,
                    backColor=CODEBG,borderColor=CODEBD,borderWidth=0.6,borderPadding=6,spaceBefore=2,spaceAfter=8)
NOTE=ParagraphStyle("NOTE",parent=BODY,fontSize=9,textColor=colors.HexColor("#5a3d00"),
                    backColor=colors.HexColor("#fff3d6"),borderColor=colors.HexColor("#e6b34d"),
                    borderWidth=0.6,borderPadding=6,spaceBefore=2,spaceAfter=8)

def _esc(t): return (t or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def build_distro_pdf(d):
    """d: dict with name, cat, pm, based, diff, url, blurb, usb, install(list), update, after, note."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=22*mm, bottomMargin=16*mm,
                            leftMargin=16*mm, rightMargin=16*mm,
                            title=f"{d['name']} — Install & Setup", author="Opperman Cybernetix")
    s=[]
    s.append(Paragraph(_esc(d["name"]), ParagraphStyle("T",parent=H1,fontSize=21,textColor=NAVY,spaceAfter=2)))
    s.append(Paragraph(_esc(d.get("blurb","")), ParagraphStyle("sub",parent=BODY,textColor=CYAN,fontSize=11,spaceAfter=2)))
    meta=f"category: {d.get('cat','')}  ·  package manager: {d.get('pm','')}  ·  based on: {d.get('based','')}  ·  level: {d.get('diff','')}"
    s.append(Paragraph(_esc(meta), ParagraphStyle("m",parent=BODY,textColor=MUTED,fontSize=8.5)))
    s.append(HRFlowable(width="100%",thickness=1.1,color=CYAN,spaceBefore=4,spaceAfter=6))
    s.append(Paragraph(f"Download: <font color='#17a2b8'>{_esc(d.get('url',''))}</font>", BODY))

    if d.get("note"):
        s.append(Paragraph("<b>Heads up —</b> "+_esc(d["note"]), NOTE))

    s.append(Paragraph("1 · Make the bootable USB", H1))
    s.append(Paragraph(_esc(d.get("usb","")), STEP))
    s.append(Paragraph("Tools: Ventoy (many ISOs on one stick), Rufus (best for Windows), balenaEtcher (simple), or dd on Linux. Verify the checksum first.", BODY))

    s.append(Paragraph("2 · Install", H1))
    for i, stp in enumerate(d.get("install",[]), 1):
        s.append(Paragraph(f"{i}. {_esc(stp)}", STEP))

    s.append(Paragraph("3 · Keep it updated", H1))
    s.append(Preformatted(d.get("update","").strip() or "# see distro docs", CODE))

    s.append(Paragraph("4 · After install — get working", H1))
    s.append(Preformatted((d.get("after","") or "").strip() or "# ready to go", CODE))

    s.append(Spacer(1,6))
    s.append(HRFlowable(width="100%",thickness=0.6,color=CODEBD,spaceBefore=2,spaceAfter=4))
    s.append(Paragraph("From DistroHub — a one-person project by Opperman Cybernetix. Commands current at time of download; check the distro's site for changes.  ·  Support: buymeacoffee.com/cybernetix88",
                       ParagraphStyle("foot",parent=BODY,fontSize=8,textColor=MUTED)))

    def _hf(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY); canvas.rect(0,A4[1]-15*mm,A4[0],15*mm,fill=1,stroke=0)
        canvas.setFillColor(CYAN); canvas.rect(16*mm,A4[1]-12*mm,8*mm,8*mm,fill=1,stroke=0)
        canvas.setFillColor(colors.white); canvas.setFont("Helvetica-Bold",7)
        canvas.drawCentredString(20*mm,A4[1]-9.4*mm,"OC")
        canvas.setFont("Helvetica-Bold",9.5); canvas.drawString(27*mm,A4[1]-9.4*mm,"DISTROHUB")
        canvas.setFont("Helvetica",7.5); canvas.setFillColor(colors.HexColor("#9fb3c8"))
        canvas.drawRightString(A4[0]-16*mm,A4[1]-9.4*mm,"by Opperman Cybernetix")
        canvas.restoreState()
    doc.build(s, onFirstPage=_hf, onLaterPages=_hf)
    buf.seek(0)
    return buf
