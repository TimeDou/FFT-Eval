"""Build the benchmark report; documentation dependencies are separate from EDA runtime."""
from pathlib import Path
from io import BytesIO
from html import escape
import re


def main():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from matplotlib.mathtext import math_to_image
    from matplotlib.font_manager import FontProperties

    root=Path(__file__).resolve().parent
    regular=Path('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf')
    bold=regular.with_name('DejaVuSerif-Bold.ttf')
    if regular.is_file()and bold.is_file():
        pdfmetrics.registerFont(TTFont('ReportSerif',str(regular)))
        pdfmetrics.registerFont(TTFont('ReportSerifBold',str(bold)))
        pdfmetrics.registerFontFamily('ReportSerif',normal='ReportSerif',bold='ReportSerifBold')
        font,bold_font='ReportSerif','ReportSerifBold'
    else:font,bold_font='Times-Roman','Times-Bold'
    styles=getSampleStyleSheet()
    body=ParagraphStyle('ReportBody',fontName=font,fontSize=9.8,leading=13.7,spaceAfter=6.7)
    title=ParagraphStyle('ReportTitle',parent=body,fontName=bold_font,fontSize=18,leading=23,
                         alignment=TA_CENTER,spaceAfter=15)
    heading=ParagraphStyle('ReportHeading',parent=body,fontName=bold_font,fontSize=12.4,
                           leading=17,spaceBefore=12,spaceAfter=7,keepWithNext=True)
    cell=ParagraphStyle('ReportCell',parent=body,fontSize=8.0,leading=11,spaceAfter=0)
    source=(root/'FFT64-Quant.md').read_text()
    document=SimpleDocTemplate(str(root/'FFT64-Quant.pdf'),pagesize=A4,
        leftMargin=49,rightMargin=49,topMargin=44,bottomMargin=46,
        title='FFT64-Quant: Architecture, Precision and Synthesis-Flow Co-Design',
        author='FFT64-Quant',pageCompression=1)
    width=A4[0]-98;story=[];lines=source.splitlines();i=0

    def inline(text):
        text=escape(text)
        text=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
        return re.sub(r'`([^`]+)`',r'<font name="Courier">\1</font>',text)

    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line=='$$':
            i+=1;math=[]
            while i<len(lines)and lines[i].strip()!='$$':math.append(lines[i].strip());i+=1
            stream=BytesIO()
            math_to_image('$'+''.join(math)+'$',stream,prop=FontProperties(size=11),dpi=260,format='png')
            stream.seek(0);pixels=ImageReader(stream).getSize();scale=min(72/260,width/pixels[0])
            image=Image(stream,width=pixels[0]*scale,height=pixels[1]*scale)
            image.hAlign='CENTER';story.extend([Spacer(1,4),image,Spacer(1,11)]);i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines)and lines[i].strip().startswith('|'):
                values=[v.strip()for v in lines[i].strip().strip('|').split('|')];i+=1
                if all(re.fullmatch(r':?-+:?',v)for v in values):continue
                rows.append([Paragraph(inline(v),cell)for v in values])
            count=len(rows[0]);fractions=[.27,.73]if count==2 else[.23,.38,.39]if count==3 else[1/count]*count
            table=Table(rows,colWidths=[width*f for f in fractions],repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([
                ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef3')),
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#536574')),
                ('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#cdd4da')),
                ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
                ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
            story.extend([table,Spacer(1,10)]);continue
        if line.startswith('# '):story.append(Paragraph(inline(line[2:]),title));i+=1;continue
        if line.startswith('## '):story.append(Paragraph(inline(line[3:]),heading));i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines)and lines[i].strip()and not lines[i].lstrip().startswith(('#','|','$$')):
            paragraph.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(' '.join(paragraph)),body))

    def footer(c,doc):
        c.saveState();c.setFont(font,8);c.setFillColor(colors.HexColor('#5b6770'))
        c.drawString(49,26,'FFT64-Quant | Technical Report')
        c.drawRightString(A4[0]-49,26,str(doc.page));c.restoreState()

    def deterministic_canvas(*args,**kwargs):
        kwargs['invariant']=1
        return canvas.Canvas(*args,**kwargs)

    document.build(story,onFirstPage=footer,onLaterPages=footer,canvasmaker=deterministic_canvas)
    print(root/'FFT64-Quant.pdf')


if __name__=='__main__':main()
