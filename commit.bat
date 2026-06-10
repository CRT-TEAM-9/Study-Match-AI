@echo off
echo ===================================================
echo  Nexus - Committing Changes to GitHub
echo ===================================================
echo.

echo 1. Adding all changes...
git add .

echo 2. Committing changes...
git commit -m "Implement Scheduler, Live Chat, Help Request Board, and rewrite README"

echo 3. Pushing changes to GitHub...
git push

echo.
echo ===================================================
echo  Git operations complete!
echo ===================================================
pause
