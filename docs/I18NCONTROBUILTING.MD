
# 国际化贡献

## 说明

欢迎为PyMemDump项目贡献国际化内容！以下是贡献国际化内容的步骤：

## 如何添加新的语言支持

1. **克隆项目到本地**

   ```bash
   git clone https://github.com/Fuxuan-CN/PyMemDump.git
   cd PyMemDump
   ```

2. **打开res/lang.json文件，添加新的语言支持**

   ```json
   {
     "fr_FR": {
        "tool_desc": "Outil de vidage de mémoire pour processus Python.",
        "scan_addr": "Analyse toutes les adresses mémoire du processus cible et les enregistre dans un fichier json.",
        "concurrent": "Vide la mémoire du processus cible de manière concurrente.",
        "workers": "Nombre de travailleurs concurrents à utiliser pour vider la mémoire.",
        "process": "Processus cible à vider la mémoire.",
        "by_addr": "Vide la mémoire du processus cible dans une plage d'adresses spécifiée.",
        "output": "Fichier de sortie pour enregistrer le vidage de la mémoire.",
        "ignore-read-error": "Ignore les erreurs de lecture lors du vidage de la mémoire. Utile lorsque le processus cible écrit dans la mémoire pendant que le vidage se lit.",
        "start-address": "Adresse de début de la plage de mémoire à vider.",
        "end-address": "Adresse de fin de la plage de mémoire à vider.",
        "content-fmt": "Format du contenu à vider. Peut être l'un des suivants : {hex, ascii, bytes}.",
        "encoding": "Encodage à utiliser pour décoder les octets en ASCII. Par défaut : UTF-8."
     }
   }
   ```

3. **再README.md中写入新的语言支持**

   ```markdown
   ## 国际化支持

   PyMemDump 支持以下语言：

   - English (en_US)
   - Français (fr_FR)
   - 简体中文 (zh_CN)
   - 日本語 (ja_JP)
   - 한국어 (ko_KR)

   你可以通过在 `res/lang.json` 文件中添加新的语言支持来添加新的语言。

   你可以通过在 `README.md` 文件中添加新的语言支持来添加新的语言。

   ```

4. **提交修改**

   ```bash
   git add res/lang.json README.md
   git commit -m "Add new language support"
   git push origin main
   ```

---
