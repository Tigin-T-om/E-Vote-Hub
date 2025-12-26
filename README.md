# E-Vote-Hub

E-Vote-Hub is a secure and user friendly college-level online voting system developed as an academic project.
The system enables students to participate in elections digitally while maintaining transparency, accuracy, and role-based access control

---

## Project Overview

E-Vote-Hub is deligned to digitize the traditional college election process.
It allows administrators to manage elections, officers to monitor voting activites, and students to securely cast their votes online.

The project is built using Django and follows a clean backend-driven architeture suitable for a real-world applications.

---

## Features

- Role-based authentication (Admin, Officer, Student)
- Secure login and session handling
- Student nomination and voting system
- Election result calculation and display
- Admin dashboard for election management
- Responsive UI using HTML, CSS, and JavaScript
- REST API support for scalable backend communication

---

## Tech Stack

- **Backend:** Python, Django, Django REST Framework  
- **Frontend:** HTML, CSS, JavaScript, HTMX  
- **Database:** PostgreSQL / SQLite (for development)  
- **Tools:** Git, GitHub, VS Code  

---

## Project Structure

E-Vote-Hub/
│── core/ # Django project settings  
│── voting/ # Main voting application  
│── templates/ # HTML templates  
│── static/ # CSS, JS, images  
│── manage.py    
│── core/ # Django project settings  
│── voting/ # Main voting application  
│── templates/ # HTML templates  
│── static/ # CSS, JS, images  
│── manage.py  

---

## Installation & Setup

1. Clone the repository
   ```bash
   git clone https://github.com/your-username/E-Vote-Hub.git
   ```

2. Create and activate virtual environment
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
4. Run migrations
   ```bash
   python manage.py migrate

5. Start the development server   
   ```bash
   python manage.py runserver

---

## Usage

- Admin can create elections and manage users

- Students can log in, nominate candidates, and vote

- Officers can review nominations and monitor voting progress

- Results are generated automatically after voting ends

---

## Future Enhancements

- OTP / Email verification

- Real-time voting status

- Blockchain-based vote verification (research scope)

- Deployment on cloud platforms

- Enhanced UI with modern frontend frameworks

---

## Author

Project Name: E-Vote-Hub  
Developed by: Your Name  
Course: MCA / BCA / B.Tech  
Institution: Your College Name  
Academic Year: 2024–2025  

---

## ✅ Why This README Is PERFECT for College

✔ Clear explanation for evaluators  
✔ Looks professional on GitHub  
✔ Not too complex  
✔ Shows real-world understanding  
✔ Recruiter-friendly (if someone views your GitHub)

---