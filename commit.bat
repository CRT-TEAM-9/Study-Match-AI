@echo off
echo ===================================================
echo  Nexus - Committing Changes to GitHub
echo ===================================================
echo.

echo 1. Adding all changes...
git add .

echo 2. Committing changes...
git commit -m "Fix Firebase config: use static firebase-config.js, add BACKEND_URL for Render, replace document.write loaders"

echo 3. Pulling remote updates...
git pull origin main --no-edit

echo 4. Pushing changes to GitHub...
git push

echo.
echo ===================================================
echo  Git operations complete!
echo ===================================================
pause
