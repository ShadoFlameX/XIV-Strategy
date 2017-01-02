import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = "quantobot@gmail.com"
GMAIL_PASS = "g4v7Vi.,dai4M#"

def sendSummaryEmail(date=None, openPositions=None, closedPositions=None):
    openPositions.sort(key=lambda p: p.purchaseDate, reverse=True)
    closedPositions.sort(key=lambda p: p.purchaseDate, reverse=True)

    messageBody = date.strftime("%B %d, %Y") + "\n\n"

    messageBody += "===== Open Positions =====" + "\n"
    if len(openPositions) > 0:
        for p in openPositions:
            if p.purchaseDate.date() == date.date():
                messageBody += "NEW! "
            messageBody += p.description()
            messageBody += "\n"
    else:
        messageBody += "None" + "\n"

    messageBody += "\n"

    messageBody += "===== Closed Positions =====" + "\n"
    if len(closedPositions) > 0:
        for p in closedPositions:
            if p.sellDate is not None and p.sellDate.date() == date.date():
                messageBody += "NEW! "
            messageBody += p.description()
            messageBody += "\n"
    else:
        messageBody += "None" + "\n"
    replacements = {"DATE_TITLE": date.strftime("%B %d, %Y"),
                    "OPEN_POSITIONS": "Position 1"}
    htmlString = html_string_from_template(template="daily_summary.html", replacements=replacements)
    print(htmlString)
    #send_email(recipient="bryguy1300@gmail.com", subject="XIV Strategy Daily Summary", htmlBody=messageBody)


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