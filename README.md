# 🎓 DeviX Academy — Training Institute Management System

A production-ready Full Stack Django web application built for training institute operations, role-based dashboards, day-by-day attendance tracking, payroll, real-time activity notifications, and instant Excel reporting.

---

## 🚀 Render.com Deployment Guide (Live on Web)

This repository is pre-configured for **Render.com** deployment with **Gunicorn**, **WhiteNoise**, **PostgreSQL / SQLite support**, and automated build scripts.

### **Step 1: Upload to GitHub**
1. Unzip `devix_academy.zip` or open this project folder in terminal / VS Code.
2. Initialize git and commit your files:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for DeviX Academy production"
   ```
3. Create a **New Repository** on [GitHub](https://github.com/new) (e.g. `devix-academy`).
4. Link and push to GitHub:
   ```bash
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/devix-academy.git
   git push -u origin main
   ```

---

### **Step 2: Deploy on Render.com**

#### **Option A: 1-Click Blueprint (Recommended)**
1. Log in to [Render.com](https://render.com/).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Connect your GitHub repository `devix-academy`.
4. Render will automatically detect [`render.yaml`](./render.yaml) and configure:
   - **Web Service**: Python environment, Gunicorn, WhiteNoise static assets.
   - **Database**: Free Managed PostgreSQL database (`devix-postgres`).
   - **Build Command**: `./build.sh` (collects static files, migrates DB, and initializes default accounts).
5. Click **Apply**. Within 2-3 minutes, your application will be live at `https://devix-academy.onrender.com`!

#### **Option B: Manual Web Service Setup**
If creating a Web Service manually:
- **Environment**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn devix_academy.wsgi:application`
- **Environment Variables**:
  - `PYTHON_VERSION`: `3.11.9`
  - `DEBUG`: `False`
  - `SECRET_KEY`: *(Click generate)*
  - `DATABASE_URL`: *(Paste your Render PostgreSQL connection string, or leave blank for SQLite)*

---

## 🔑 Active Default Credentials

The build script automatically seeds these default accounts on first run:

| Role | Login ID / Email | Password | Access Dashboard |
| :--- | :--- | :--- | :--- |
| **Branch Head** | `reena@samyak.com` | `Reena@123` | `/branch-head/dashboard/` |
| **Trainer 1** (`TRN-001`) | `ramsir@samyak.com` | `Ramsir@123` | `/trainer/dashboard/` |
| **Trainer 2** (`TRN-002`) | `jiten@samyak.com` | `Jiten@123` | `/trainer/dashboard/` |

*(Users can log in by typing either their Email Address or their Username)*

---

## 📱 Mobile APK Conversion (Android Notification Tray Ready)

This application includes a Progressive Web App (PWA) manifest and Service Worker configured for Android mobile APK status bar notifications:
- **Manifest**: [`static/manifest.json`](./static/manifest.json)
- **Service Worker**: [`static/sw.js`](./static/sw.js)
- **Notification Poller**: [`static/js/notifications.js`](./static/js/notifications.js)

### **To convert to an Android APK:**
1. Open [PWABuilder](https://www.pwabuilder.com/) and enter your live Render URL (e.g. `https://devix-academy.onrender.com`).
2. Click **Package for Stores** $\rightarrow$ **Android**.
3. Download the generated `.apk` / `.aab` file and install it directly on your Android phone!
4. Real-time notifications for leaves, chats, and study materials will appear directly in the **Android status bar / notification tray**.

---

## 📊 Key Management Features

1. **Role-Based Access Control**:
   - Single unified login with automatic role redirection (`BRANCH_HEAD`, `TRAINER`, `STUDENT`).
   - Exactly one Branch Head account strictly enforced.
2. **Student & Faculty Leave System**:
   - Students apply for leaves $\rightarrow$ Assigned trainer reviews.
   - If approved, attendance is marked as **`Leave`** (NOT Absent).
   - If rejected, marked as **`Absent`**.
3. **Monthly Student Attendance Matrix**:
   - Day-by-day month-wise attendance calendar grid with color-coded status badges ($P$, $L$, $A$, $SUN$).
   - Real-time 75% attendance threshold calculation for certificate eligibility.
4. **Excel Data Exports (`.xlsx`)**:
   - Export full student directory with all demographic, course, trainer, and attendance stats.
   - Export month-wise day-by-day student attendance matrix.
5. **Real-Time Notification Center**:
   - Permission-first browser & mobile status bar notification workflow.
   - Instant polling with sound chime and navbar unread badge.
