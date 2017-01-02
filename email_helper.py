import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER = "quantobot@gmail.com"
GMAIL_PASS = "g4v7Vi.,dai4M#"

def sendSummaryEmail(date=None, openPositions=None, closedPositions=None):
    openPositions.sort(key=lambda p: p.purchaseDate, reverse=True)
    closedPositions.sort(key=lambda p: p.purchaseDate, reverse=True)

    # todaysOpenPositions = [p for p in openPositions if p.purchaseDate.date() == date.date()]
    # todaysClosedPositions = [p for p in closedPositions if p.sellDate is not None and p.sellDate.date() == date.date()]

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

    send_email(recipient="bryguy1300@gmail.com", subject="XIV Strategy Daily Summary", body=messageBody)


def send_email(recipient=None, subject=None, body=None):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = recipient
    msg['Subject'] = subject

    body = body
    msg.attach(MIMEText(body, 'plain'))

    try:
        print("Sending email to " + recipient + "…")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        text = msg.as_string()
        server.sendmail(GMAIL_USER, recipient, text)
        server.quit()
    except:
        print("Email failed to send")
