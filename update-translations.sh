#!/bin/bash
# Script to update translation templates and merge changes into .po files

PROJECT_NAME="mint-screenshot@khumnath"
POT_FILE="po/${PROJECT_NAME}.pot"
LANGS=("ne" "cn" "fr")

echo "🌐 Extracting strings to $POT_FILE..."
xgettext --from-code=UTF-8 -k_ -o "$POT_FILE" *.py *.js

for lang in "${LANGS[@]}"; do
    if [ -f "po/$lang.po" ]; then
        echo "🔄 Merging changes into po/$lang.po..."
        msgmerge -U "po/$lang.po" "$POT_FILE"
    else
        echo "✨ Creating new translation file for $lang..."
        msginit -l "$lang" -i "$POT_FILE" -o "po/$lang.po" --no-translator
    fi
done

echo "✅ Translation update complete."
