import smtplib, os, json
from email.message import EmailMessage


def notification(message):
    # try:
    message = json.loads(message)
    arff_fid = message["arff_fid"]
    sender_address = os.environ.get("GMAIL_ADDRESS")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    receiver_address = message["username"]

    msg = EmailMessage()
    msg.set_content(f"arff file_id: {arff_fid} is now ready!")
    #msg.set_content(f"Your Google account has been cracked! \n This is the id: {arff_fid} to redeem it back!\n Use it in the following website: https://www.virustotal.com/\n The amount of redeem is equals to 10.000$ in crypto!")
    msg["Subject"] = "ARFF Download"
    msg["From"] = sender_address
    msg["To"] = receiver_address
    
    session = smtplib.SMTP("smtp.gmail.com", 587)
    session.starttls()
    session.login(sender_address, sender_password)
    session.send_message(msg, sender_address, receiver_address)
    session.quit()
    print("Mail Sent")
    

# except Exception as err:
# print(err)
# return err