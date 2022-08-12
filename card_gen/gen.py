import pdfkit
import code128
import qrcode
from pathlib import Path
def cardgen(member_id,member_name,member_type,member_expire_date):
    member_expire_date = member_expire_date.strftime("%d/%m/%Y")
    qrgen(member_id)
    bargen(member_id)
    htmlgen(member_id,member_name,member_type,member_expire_date)
    pdf = PDFgen()

def htmlgen(member_id,member_name,member_type,member_expire_date):
    html = f"""<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="./card.css"><body><div class="face face-front" ><img src="./front.png"></div><div id="infoi"><img src="./qr.png" height="89.5" width="83" />
        <div style="margin-left: 1.3cm;margin-top: -0.6cm;">
            <br>
            <div style="font-size: 0.7em;margin-top: 5%;font-family: sans-serif;color: aliceblue;text-transform: uppercase;"><b>{member_name}</b></div><br>
        <div style="font-size: 0.7em;margin-top: -0.4cm;font-family: sans-serif;color: aliceblue;text-transform: capitalize;">{member_type}</div>
        </div>
    </div>
    <div id="info">
        <br><div style="font-size: 0.7em;margin-top: 0.6%;font-family: sans-serif;text-transform: uppercase;">{member_id}</div>
        <br><div style="font-size: 0.7em;margin-top: -0.6%;font-family: sans-serif;text-transform: capitalize;">{member_expire_date}</div>
    </div>
    <div id="BARCODE"><img src="./bar.png"  height="20" width="120"/></div>

</body>"""
    f= open(f"{Path().absolute()}/card_gen/res/index.html","w")
    f.write(html)
    f.close()

def bargen(member_id):
    code128.image(member_id).save(f"{Path().absolute()}/card_gen/res/bar.png")

def qrgen(member_id):
    qrcode.make(member_id).save(f"{Path().absolute()}/card_gen/res/qr.png")

#generate costum pdf file using the existing html file // code argument is only to name the file generated
def PDFgen():
    config = pdfkit.configuration()
    options = {'dpi': 365,'margin-top': '0in','margin-bottom': '0in','margin-right': '0in','margin-left': '0in','page-size': 'A8',"orientation": "Landscape",'disable-smart-shrinking': ''}
    pdfkit.from_file(f'{Path().absolute()}/card_gen/res/index.html', f"{Path().absolute()}/card_gen/res/card.pdf", configuration=config , options = options)  