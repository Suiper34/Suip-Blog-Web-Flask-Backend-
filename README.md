# SuipBlog 📝✨

SuipBlog is a small, secure Flask-based blogging platform focused on best practices:

- Flask-Login for auth
- Flask-CKEditor for rich text
- SQLAlchemy ORM with relationships
- Robust logging and test-suite

Repository maintained for learning and production-ready patterns.

---

## Features ✅

- User registration & login
- Create, edit, delete posts (admin-only)
- Commenting system
- Gravatar integration
- CSRF protection & input sanitization

---

## 🚀 Quick Start — Local Development

1. Clone repo:

   ```bash
   git clone <repo-url>
   ```

2. Create virtual env & install:

   ```bash
   python -m venv .venv
   ```

   ```bash
   .venv\Scripts\activate # Windows
   ```

   ```bash
   pip install -r requirements.txt
   ```

3. Environment variables: create a `.env` with:

   ```env
   DB_URI=sqlite:///posts.db
   MAIL=youremail@example.com
   PASSWORD=yourmailpassword
   WHATSAPP=...
   GITHUB=...
   PORTFOLIO=...
   API_TOKEN=...
   ```

4. Initialize DB (once):
   python
   > > > from app import app, db
   > > > with app.app_context():
   > > > ... db.create_all()
   > > > ... exit()

5. Run app:

   ```bash
   python app.py
   ```

6. Open <http://127.0.0.1:5000/>

---

## Project Structure 📁

```
suip-blog-web/
├─ app.py
├─ forms.py
├─ models.py
├─ instance/               # Blog app db
├─ templates/              # Jinja2 templates
├─ static/                 # static assets (css, img, js)
├─ tests/                  # pytest tests (conftest + unit tests)
├─ requirements.txt
├─ README.md
├─ .env
├─ Procfile
└─ LICENSE
```

---

## Running Tests 🧪

Ensure dev dependencies installed (pytest). Run:

```bash
pytest -q
```

The tests use an in-memory SQLite DB and disable CSRF for form-testing.

---

## Logging & Debugging 🐞

- Logs saved to `suip-blog-web.log` (rotating)
- Set environment `FLASK_ENV=development` for debug info.

---

## Contributing 🤝

1. Fork
2. Create feature branch
3. Open PR with tests

---

## License 📜

This project is released under the JhapTech Permissive License [`see LICENSE`](./LICENSE). TL;DR: you may use, modify, and redistribute with attribution.

---

Made with ❤️ by Jhaptech. Illuminate and iterate✨
