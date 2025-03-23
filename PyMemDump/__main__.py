""" module for command line interface """
from PyMemDump import MemoryDumper
import locale

def normalize_language(lang: str) -> str:
    """
    Normalize the language string to a standard format (e.g., zh_CN, en_US).
    """
    lang_map = {
        "Chinese (Simplified)_China": "zh_CN",
        "Chinese (Traditional)_Taiwan": "zh_TW",
        "English_United States": "en_US",
        "French_France": "fr_FR",
        "Japanese_Japan": "ja_JP",
        "Korean_Korea": "ko_KR",
        "Russian_Russia": "ru_RU",
        "Spanish_Spain": "es_ES",
        "German_Germany": "de_DE",
        "Italian_Italy": "it_IT",
        "Portuguese_Brazil": "pt_BR",
        "Turkish_Turkey": "tr_TR"
    }
    return lang_map.get(lang, "zh_CN")

def auto_language() -> str:
    """
    Auto detect the system language and return the corresponding language code.
    """
    lang , enc = locale.getlocale()
    lang = normalize_language(lang)
    return lang
    
if __name__ == "__main__":
    MemoryDumper.dump_with_args(language=auto_language())