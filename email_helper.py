import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = "quantobot@gmail.com"
GMAIL_PASS = "g4v7Vi.,dai4M#"

def sendSummaryEmail(date=None, openPositions=None, closedPositions=None):
    openPositions.sort(key=lambda p: p.purchaseDate, reverse=True)
    closedPositions.sort(key=lambda p: p.purchaseDate, reverse=True)

    openPositionsHTML = ""
    if len(openPositions) > 0:
        for p in openPositions:
            if p.purchaseDate.date() == date.date():
                openPositionsHTML += "<p><strong><font color=\"#009900\">" + p.description() + "</font></strong></p>"
            else:
                openPositionsHTML += "<p>" + p.description() + "</p>"
    else:
        openPositionsHTML += "<p>None</p>"

    closedPositionsHTML = ""
    if len(closedPositions) > 0:
        for p in closedPositions:
            if p.sellDate is not None and p.sellDate.date() == date.date():
                closedPositionsHTML += "<p><strong><font color=\"#990000\">" + p.description() + "</font></strong></p>"
            else:
                closedPositionsHTML += "<p>" + p.description() + "</p>"
    else:
        closedPositionsHTML += "<p>None</p>"

    replacements = {"DATE_TITLE": date.strftime("%B %d, %Y"),
                    "OPEN_POSITIONS": openPositionsHTML,
                    "CLOSED_POSITIONS": closedPositionsHTML}
    htmlString = html_string_from_template(template="daily_summary.html", replacements=replacements)
    # print(htmlString)
    send_email(recipient="bryguy1300@gmail.com", subject="XIV Strategy Daily Summary", htmlBody=htmlString)


def send_email(recipient=None, subject=None, htmlBody=None):
    msg = MIMEMultipart('alternative')
    msg['From'] = GMAIL_USER
    msg['To'] = recipient
    msg['Subject'] = subject

    # msg.attach(MIMEText(body, 'plain'))
    msg.attach(MIMEText(htmlBody, 'html'))

    try:
        print("Sending email to " + recipient + "…")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.sendmail(GMAIL_USER, recipient, msg.as_string())
        server.quit()
    except:
        print("Email failed to send")

def html_string_from_template(template=None, replacements=None):
    with open('email_templates/' + template, 'r') as myfile:
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