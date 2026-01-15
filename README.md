hi


ADB is way too slow for real-time gameplay!

It captures a screenshot on the phone, compresses it, sends to computer, then awaits processing before returning an input onto the phone



Future Ideas:

- Hand tracker

- Elixir tracker (vision)

- Alternative card vision approaches for optimization (e.g., use of AI, pixel colour (BGR) targeting)


HOW TO COMMIT WORK TO GITHUB:
# 1. Use GitHub Desktop
On GitHub Desktop, commit changes, and push to origin (to your branch).
# 2. Open a terminal in VSCode
Run the command in terminal: git push origin "your-branch-name"
------------------------------------------_
HOW TO **CLEANLY** UPDATE MAIN WITH YOUR BRANCH:
# 1. Push your latest work
git push origin your-branch-name

# 2. Go to GitHub.com
You will usually see a yellow bar at the top saying "Branch-Name had recent pushes..." 
with a button that says "Compare & pull request".

# 3. Create the PR
Set the base to main and compare to Branch-Name
Write a brief description of changes
Click "Create pull request"

# 4. Merge
Click the green "Merge pull request"
-------------------------------------------
HOW TO **FORCE** UPDATE MAIN WITH YOUR BRANCH:
# 1. Switch to Main branch
git checkout main

# 2. Update main
git pull origin main

# 3. Merge your branch into Main
git merge your-branch-name

# 4. Push the updated main back to GitHub
git push origin main
-------------------------------------------
HOW TO RETRIEVE FROM MAIN TO YOUR BRANCH:
# 1. Ensure you are on your branch
git checkout your-branch-name

# 2. Pull changes from main directly into your branch
git pull origin main

# 3. Resolve any conflicts if prompted, then:
git add .
git commit -m "Sync with main"

-------------------------------------------

-------------------------------------------
HOW TO UPDATE A FILE IN YOUR BRANCH FROM ANOTHER ONE:
# 1. Fetch the latest data
git fetch origin

# 2. Overwrite the file with the other branch's version
git checkout other-branch-name -- path/to/your/file.ext
-------------------------------------------
COMPARE YOUR VERSION OF A FILE WITH ANOTHER ONE:
# 1. Enter the following in terminal
git diff head other-branch-name -- path/to/your/file.ext
