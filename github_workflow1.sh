# Start new feature
git checkout main
git pull
git checkout -b feature/ocr-integration

# Work on feature...
git add .
git commit -m "Add Mistral OCR service class #6"
git push -u origin feature/ocr-integration

# Create PR via GitHub or CLI
gh pr create --title "OCR Integration" --body "Closes #6, #7"

# After approval, merge
gh pr merge --squash

# Clean up
git checkout main
git pull
git branch -d feature/ocr-integration
