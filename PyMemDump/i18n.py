""" the i18n module, useful for any language support """
import json
from pathlib import Path

LANG_PATH = Path(__file__).parent / "res" / "lang.json"

def load_languages() -> dict[str, dict[str, str]]:
    """ Load language data from json file """
    with open(LANG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_language(lang_code: str) -> dict[str, str]:
    """ Get language data by language code """
    languages = load_languages()
    lang_dict = languages["lang"]
    if lang_code not in lang_dict:
        return lang_dict["en_US"]
    return lang_dict[lang_code]

def get_text(lang_code: str, text_key: str) -> str:
    """ Get text by language code and text key """
    lang_dict = get_language(lang_code)
    if text_key not in lang_dict:
        return ""
    return lang_dict[text_key]

if __name__ == "__main__":
    print(get_text("zh_CN", "tool_desc"))