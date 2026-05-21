# Contributing to Yield-Wise-Product

---

## One-Time Setup (Both Collaborators)

### 1. Get Access

Josh (repo owner) must add your partner as a collaborator:

> GitHub repo → **Settings** → **Collaborators** → **Add people**

Your partner accepts the invite from their email or GitHub notifications.

### 2. Clone the Repo

```bash
git clone https://github.com/joshuatochinwachi/Yield-Wise-Product.git
cd Yield-Wise-Product
```

### 3. Install Dependencies

```bash
npm install
# or
pip install -r requirements.txt
```

---

## Daily Workflow

### Before Starting Any Work — Sync First

```bash
git checkout main
git pull origin main
```

### Create a Branch for Your Task

```bash
git checkout -b tobeonchain/yieldfirstbranch
```

### Make Changes, Then Commit

```bash
git add .
git commit -m "brief description of what you did"
```

### Push Your Branch

```bash
git push origin tobeonchain/yieldfirstbranch
```

### Open a Pull Request

1. Go to [github.com/joshuatochinwachi/Yield-Wise-Product](https://github.com/joshuatochinwachi/Yield-Wise-Product)
2. Click **"Compare & pull request"**
3. Add a short description of your changes
4. The other person reviews and merges

---

## Rules

- Never commit directly to `main`
- Always pull `main` before creating a new branch
- One task per branch — keep PRs small and focused
- Write commit messages that mean something: `"fix login redirect"` not `"update"`