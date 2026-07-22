#!/data/data/com.termux/files/usr/bin/bash

PROJECTS="$HOME/Projects"

echo "========================================"
echo " NEXUS Guardian v0.1.0"
echo "========================================"
echo

find "$PROJECTS" -maxdepth 2 -type d | while read repo; do
    if git -C "$repo" rev-parse --is-inside-work-tree >/dev/null 2>&1; then

        echo "Scanning: $(basename "$repo")"

        # Check .env tracking
        if git -C "$repo" ls-files | grep -qx ".env"; then
            echo "  [WARNING] .env is tracked by Git"
        else
            echo "  [OK] .env not tracked"
        fi

        # Check .gitignore
        if [ -f "$repo/.gitignore" ]; then
            echo "  [OK] .gitignore exists"
        else
            echo "  [WARNING] Missing .gitignore"
        fi

        # Search for possible secrets
        hits=$(grep -RniE \
"(API[_-]?KEY|SECRET|TOKEN|PASSWORD|PRIVATE[_-]?KEY|SUPABASE|OPENAI|GROQ|GEMINI|JWT|AWS|FIREBASE|MONGODB)" \
"$repo" \
--exclude-dir=node_modules \
--exclude-dir=.git 2>/dev/null | wc -l)

        if [ "$hits" -gt 0 ]; then
            echo "  [WARNING] Possible secrets found ($hits)"
        else
            echo "  [OK] No obvious secrets"
        fi

        echo
    fi
done
