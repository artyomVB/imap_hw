from mail_collector import MailCleaner

if __name__ == "__main__":
    with MailCleaner(0.9, "login", "password", "server") as cleaner:
        cleaner.collect()
        cleaner.delete()
