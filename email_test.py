import smtplib, ssl

##port = 465  # For SSL
##password = "finalproject"
##
### Create a secure SSL context
##context = ssl.create_default_context()
##
##with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
##    server.login("cep.final.project@gmail.com", password)
##    # TODO: Send email here

port = 587
smtp_server = "smtp.office365.com"
sender_email = "22YMICH136A@student.ri.edu.sg"
password = 'e6vtayej'

message = """\
Subject: Hi there

This message is sent from Python."""

receiver_email = 'michaelchenkaijie2004@gmail.com'

context = ssl.create_default_context()

with smtplib.SMTP(smtp_server, port) as server:
    server.starttls()
    server.login(sender_email, password)

    server.sendmail(sender_email, receiver_email, message)

    server.quit()
