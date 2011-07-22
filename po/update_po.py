#!/usr/bin/python

#update all po files in the LANGS

import os

DOMAIN = "blender"
LANGS = (
  "ar",
  "bg",
  "ca",
  "cs",
  "de",
  "el",
  "es",
  "fi",
  "fr",
  "hr",
  "it",
  "ja",
  "ko",
  "nl",
  "pl",
  "pt_BR",
  "ro",
  "ru",
  "sr@Latn",
  "sr",
  "sv",
  "uk",
  "zh_CN",
  "zh_TW"
)
#-o %s.new.po
for lang in LANGS:
    # update po file
    cmd = "msgmerge --update --lang=%s %s.po %s.pot" % (lang, lang, DOMAIN)
    print(cmd)
    os.system( cmd )
    
