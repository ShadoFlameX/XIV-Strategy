import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import locale
import urllib, base64
import StringIO

logger = logging.getLogger("xivstrategy.email_helper")

WRITE_EMAIL_TO_DISK = False

GMAIL_USER = "quantobot@gmail.com"
GMAIL_PASS = "g4v7Vi.,dai4M#"

def sendSummaryEmail(date=None, currentPrice=0.0, openPositions=None, closedPositions=None, chartImage=None):
    openPositions.sort(key=lambda p: p.purchaseDate, reverse=True)
    closedPositions.sort(key=lambda p: p.purchaseDate, reverse=True)

    openPositionsHTML = ""
    if len(openPositions) > 0:
        for p in openPositions:
            openPositionsHTML += positionRowHTML(p, date)
    else:
        openPositionsHTML += '<tr><td colspan="5" align="center">None</td></tr>'

    closedPositionsHTML = ""
    if len(closedPositions) > 0:
        for p in closedPositions:
            closedPositionsHTML += positionRowHTML(p, date)
    else:
        closedPositionsHTML += '<tr><td colspan="5" align="center">None</td></tr>'

    imgData = StringIO.StringIO()
    chartImage.save(imgData, "PNG")
    imgData.seek(0)
    imageBase64 = 'data:image/png;base64,' + urllib.quote(base64.b64encode(imgData.buf))
    imgData.close()

    replacements = {"DATE_TITLE": date.strftime("%B %-d, %Y %-I:%M %p"),
                    "CHART_IMAGE_BASE64": imageBase64,
                    "XIV_PRICE": locale.currency(currentPrice),
                    "OPEN_POSITIONS": openPositionsHTML,
                    "CLOSED_POSITIONS": closedPositionsHTML}
    htmlString = html_string_from_template(template="daily_summary.html", replacements=replacements)

    if WRITE_EMAIL_TO_DISK:
        logger.info("Writing email to disk...")
        text_file = open("temp/test.html", "w")
        text_file.write(htmlString)
        text_file.close()
        result = True
    else:
        result = send_email(recipient="bryguy1300@gmail.com", subject="XIV Strategy Daily Summary", htmlBody=htmlString)

    return result


def positionRowHTML(position, date):
    sellDateStr = position.sellDate.strftime("%b %-d, %Y") if position.sellDate is not None else "N/A"
    sellPriceStr = locale.currency(position.sellPrice) if position.sellPrice is not None else "N/A"

    html = ""
    if position.sellDate is not None and position.sellDate.date() == date.date():
        html += '<tr class="sell-highlight">'
    elif position.purchaseDate.date() == date.date():
        html += '<tr class="purchase-highlight">'
    else:
        html += '<tr>'

    html += "<td align=\"center\">" + position.purchaseDate.strftime("%b %-d, %Y") + "</td>" + \
            "<td align=\"right\">" + locale.currency(position.purchasePrice) + "</td>" + \
            "<td align=\"right\">" + '{0:g}'.format(float(position.shareCount)) + "</td>" + \
            "<td align=\"center\">" + sellDateStr + "</td>" + \
            "<td align=\"right\">" + sellPriceStr + "</td>" + \
            "</tr>"

    return html


def send_email(recipient=None, subject=None, htmlBody=None):
    result = False

    if recipient and len(recipient) and\
        subject and len(subject) and\
        htmlBody and len(htmlBody):

        msg = MIMEMultipart('alternative')
        msg['From'] = GMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = subject

        # msg.attach(MIMEText(body, 'plain'))
        msg.attach(MIMEText(htmlBody, 'html'))

        try:
            logger.info("Sending email to " + recipient + "...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, recipient, msg.as_string())
            server.quit()
            result = True

        except:
            logger.exception("Email failed to send")

    return result

def html_string_from_template(template=None, replacements=None):
    templatePath = os.path.dirname(os.path.realpath(__file__)) + "/" + "email_templates/" + template
    with open(templatePath, 'r') as myfile:
        htmlString = myfile.read()

        p = re.compile('\{%([A-Za-z0-9_]+)%\}')
        iterator = p.finditer(htmlString)
        matches = [e for e in iterator]

        for match in reversed(matches):
            key = match.group(1)
            if key in replacements:
                location = match.span()[0]
                length = match.span()[1] - match.span()[0]
                value = replacements[key]
                htmlString = htmlString[0:location] + value + htmlString[location + length:]

        return htmlString