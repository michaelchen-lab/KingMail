import smtplib, ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email_mod(sender_email='', sender_password='', receiver_emails=[], email_type='', subject='', body='', attachment=None):
    """
    Function: Sends an email as requested by user
    Parameters:
        1. sender_email (string)
        2. sender_password (string) --- Password of sender's email
        3. receiver_emails (list)
        4. email_type (string) --- either 'Gmail' or 'Outlook' is accepted
        5. subject (string) --- title of email
        6. body (string) --- body of email
    """

    ## Setup email content
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_emails)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    message = msg.as_string()

    ## Send email through Gmail or Outlook
    if email_type == 'Gmail':

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
           server.login(sender_email, sender_password)
           server.sendmail(sender_email, receiver_emails, message)
           server.quit()

    elif email_type == 'Outlook':

        context = ssl.create_default_context()

        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()

            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_emails, message)
            server.quit()

    else:

        print('Error: Invalid email type. Only Gmail and Outlook are supported')
