# Contributing to K3Y Open Session Finder

Thank you for your interest in contributing to the **K3Y Open Session Finder** project!

This tool is designed to help SKCC K3Y operators identify available operating sessions during [Straight Key Month](https://www.skccgroup.com/k3y/k3y.php). Your input—whether through code, ideas, or feedback—can make a big difference.

---

## How You Can Help

We welcome all contributions, big or small! You can help by:

- Reporting or fixing bugs
- Suggesting and implementing new features
- Improving UI/UX
- Enhancing documentation or code comments
- Offering feedback or ideas via GitHub Discussions or Issues

---

##  Getting Started

1. **Fork the repository** and clone it locally:
   ```bash
   git clone https://github.com/MarkCruse/k3y-open-sessions.git
   cd k3y-open-sessions
   ```

2. **Create a new branch** for your feature or fix:
   ```bash
   git checkout -b feature/my-cool-feature
   ```

3. **Install dependencies** (preferably in a virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

4. **Make your changes**, test them, and commit:
   ```bash
   git commit -m "Add: a short but clear description of your change"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/my-cool-feature
   ```

6. **Open a Pull Request** to the `main` branch and describe your changes.

---

## Tips

- Be clear and concise in your commit messages and pull request descriptions.
- Feel free to open an issue if you’d like to propose a feature before coding.
- Small contributions are welcome! Even fixing typos or improving formatting helps.

---

## Testing

Currently, the app runs via:
- `streamlit run dashboard.py` (for UI testing)
- `python k3y_open_time_slots.py` (for CLI testing)

If you're introducing logic changes, try to test both where applicable.

---

## File Overview

- `dashboard.py` — Streamlit app UI
- `k3y_open_time_slots.py` — Core scheduling logic and CLI
- `settings.json` — Stores user preferences
- `README.md` — Project overview
- `requirements.txt` — Python dependencies

---

## Code of Conduct

Please be respectful, constructive, and kind. Let’s make contributing a positive experience for everyone.

---

## Thank You

Your interest in improving the K3Y Open Session Finder is truly appreciated.  
Every contribution counts—thank you for helping make this tool better for the SKCC community!
