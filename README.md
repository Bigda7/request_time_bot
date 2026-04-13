# 🤖 Website Monitoring Telegram Bot

![Python](https://img.shields.io/badge/Python-3.13-blue)
![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

A Telegram bot designed to monitor the uptime and status of your websites.  
It performs background checks and notifies you instantly if a website goes down or comes back online.

---

## ✨ Features

- 🔄 Background Monitoring — Checks websites every 5 minutes 
- 🚨 Instant Alerts — Notifies when a site goes down or recovers 
- 📊 Live Status Check — Manual check with response time 
- 🔐 Admin Protected — Only authorized user can manage the bot 
- 💾 Database Storage — Stores URLs using SQLAlchemy 
- ⚡ Asynchronous Requests — Blazing fast checks using `aiohttp` and `asyncio`

---

## 🛠️ Technologies Used

- Python 3.13 
- Aiogram 3.x 
- SQLAlchemy 
- aiohttp 
- python-dotenv 
- PostgreSQL

---

## 📁 Project Structure

```text
project/
│
├── tg_bot.py
├── requirements.txt
├── .env.example      # Template for environment variables
├── .gitignore
└── README.md
```

---

## 🚀 Installation & Setup

### 1. Clone the repository
```
git clone https://github.com/Bigda7/request_time_bot.git
cd request_time_bot
```

### 2. Create virtual environment
```
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```
pip install -r requirements.txt
```

### 4. Create `.env` file
```
API_TOKEN=your_telegram_bot_token_here
YOUR_CHAT_ID=123456789

# --- DATABASE SETTINGS ---
# Option 1: For a local SQLite database (for testing purposes)
# DB_URL=sqlite:///websites.db

# Option 2: For PostgreSQL (Production variant)
# Format: postgresql://user:password@host:port/database_name
DB_URL=postgresql://postgres:your_password@localhost:5432/monitor_db
```

### 5. Run the bot
```
python tg_bot.py
```

---

## 📜 Bot Commands

- /start — Show info  
- /add <url> — Add website  
- /remove <id> — Remove website  
- /list — Show all websites  
- /status — Live check  
- /pause — Pause monitoring  
- /resume — Resume monitoring  

---

## 🔐 Security Note

Never share your `.env` file or API token publicly.  
Make sure `.env` is added to `.gitignore`.

---

## 🚧 Future Improvements

- Web dashboard (Flask / FastAPI)  
- Docker support  
- Multi-user support  
- Custom check intervals  
- Monitoring statistics  

---

## 📄 License

This project is licensed under the MIT License.

---

## 💡 Author

Developed by Bigda7 as a learning and portfolio project 🚀
