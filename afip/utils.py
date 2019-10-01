import datetime


def parse_date(text):
    if text is None or text.upper() == 'NULL':
        return None
    if '-' in text:
        text = text.replace('-', '')
    if '/' in text:
        text = [p.zfill(2) for p in text.split('/')]
        text = [text[2], text[0], text[1]]
        text = ''.join(text)
    return datetime.date(year=int(text[0:4]), month=int(text[4:6]), day=int(text[6:8]))


def unparse_date(date):
    return date.strftime('%Y%m%d')
