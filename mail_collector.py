import email
import imaplib


class MailCleaner:
    def __init__(self, threshold: float, login: str, password: str, server: str):
        self.password = password
        self.server = server
        self.login = login
        self.threshold = threshold
        self.mailing_lists = {}
        self.msg_ids = {}

    def __enter__(self):
        self.mail = imaplib.IMAP4_SSL(self.server)
        self.mail.login(self.login, self.password)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mail.close()
        self.mail.logout()

    def collect(self):
        self.mail.select('INBOX')

        _, data = self.mail.search(None, 'ALL')
        message_ids = data[0].split()[-100:]
        message_ids.reverse()

        for message_id in message_ids:
            typ, data = self.mail.fetch(message_id, '(BODY.PEEK[HEADER])')
            data = email.message_from_bytes(data[0][1])
            if data["List-Id"] or data["List-Unsubscribe"] or data["Mailing-List"]:
                sender = email.utils.parseaddr(data["From"])[1]
                if sender not in self.mailing_lists:
                    self.mailing_lists[sender] = {'total': 0, 'unread': 0}
                    self.msg_ids[sender] = []
                self.mailing_lists[sender]['total'] += 1
                self.msg_ids[sender].append(message_id)
                typ, data = self.mail.fetch(message_id, '(FLAGS)')
                flags = data[0].decode('utf-8').split()[-2:]
                if '(\\Seen))' not in flags:
                    self.mailing_lists[sender]['unread'] += 1

    def delete(self):
        for sender, counts in self.mailing_lists.items():
            if counts['unread'] / counts['total'] > self.threshold:
                print(f"You have {counts['unread']} unread messages out of {counts['total']} from {sender}.")
                answer = input("Would you like to delete all messages? [y/n]: ")
                if answer.lower() == 'y':
                    for message_id in self.msg_ids[sender]:
                        self.mail.store(message_id, '+FLAGS', '\\Deleted')
                    self.mail.expunge()
                    print("Done")
