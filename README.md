# Student Exam System 
  
A Flask-based online examination system that allows students to take multiple-choice quizzes and administrators to manage questions and track results. 
  
## Features  
  
- User Authentication: Secure login and registration with role-based access  
- Online Examinations: Take multiple-choice exams with instant scoring  
- Admin Dashboard: Manage questions, view all student results  
- Result Tracking: View individual and aggregate performance statistics  
- Responsive Design: Works on desktop and mobile devices 
  
## Tech Stack  
  
- Backend: Flask (Python)  
- Database: SQLite  
- Frontend: HTML, CSS, JavaScript  
  
## Installation  
  
1. Clone the repository  
   git clone REPOSITORY_URL  
   cd student-ex  
  
2. Create virtual environment  
   python -m venv venv  
   venv\Scripts\activate  
  
3. Install dependencies  
   pip install -r requirements.txt 
  
4. Run the application  
   python app.py  
  
5. Open browser and navigate to  
   http://localhost:5000  
  
## Default Login Credentials  
  
Role     Username   Password  
-----   --------   --------  
Admin   admin     admin123  
Student student1  pass123 
  
## Project Structure  
  
student-ex/  
  app.py              - Main Flask application  
  requirements.txt  - Python dependencies  
  exam.db            - SQLite database  
  models/db.py       - Database initialization  
  static/style.css   - CSS stylesheets  
  templates/  
    admin.html       - Admin dashboard  
    base.html        - Base template  
    dashboard.html   - Student dashboard  
    exam.html        - Exam page  
    index.html       - Home page  
    login.html       - Login page  
    register.html   - Registration page  
    result.html     - Result page  
    results.html    - All results 
  
## Usage  
  
### For Students  
1. Register a new account or login with default credentials  
2. Take available exams from dashboard  
3. View your results after submission  
  
### For Admin  
1. Login with admin credentials  
2. Add, edit, or delete questions  
3. View all student results and performance stats  
  
## License  
  
MIT License 
