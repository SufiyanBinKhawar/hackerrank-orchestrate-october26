import re
import unicodedata
from .models import normalize


def authorizes_deletion(text):
    text = normalize(text).replace('’', "'")
    plain = ''.join(c for c in unicodedata.normalize('NFKD', text) if not unicodedata.combining(c))
    negatives = [r"(?:do not|don't|not a request to)\s+(?:delete|erase|remove|close)",
                 r'not asking for (?:deletion|erasure)',
                 r'marketing lists only', r'no (?:quiero|solicito).*(?:elimin|borr)',
                 r'ne .*supprim.*pas', r'nao .*exclu', r'削除しない', r'삭제하지']
    if any(re.search(p, plain) or re.search(p, text) for p in negatives):
        return False
    if re.search(r'\b(delet\w*|eras\w*|elimin\w*|exclus\w*|suppression)\b', plain) or re.search(r'削除|삭제', text):
        return True
    if re.search(r'\b(close|closed|remove|removed)\b', plain) and re.search(r'account|profile|personal|records|search result', plain):
        return True
    return bool(re.search(r'(?:verify|confirm|check|inspect).*?(?:profile is gone|account.*removed|profile.*gone|personal details.*remove)', plain))
