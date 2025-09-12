# Complaint Registration System

## Key Features of Complaint Registration System
- **Public Complaint Submission**: Customers can register complaints without logging in, and receive an auto-generated ticket number with SMS/email confirmation.  
- **Role-Based Dashboards**: Separate dashboards for Admin, Manager, Engineer, Accountant, Tally User, and Customer with restricted access.  
- **Complaint Lifecycle Tracking**: Assign complaints to engineers, update status (Open, In Progress, Resolved, Closed), upload service confirmation photos, and record product serial numbers.  
- **Product & Warranty Management**: Store product details, warranty period (years + months), sold info, and installation tracking.  
- **Payment & Service Management**: Service cost entry, payment method (cash/online), payment confirmation photo upload, and payment completion flag.  
- **Reporting & Exports**: Search, filter, pagination, and export filtered data (complaints/products) to Excel.  

---

## Getting Started

### Prerequisites
- Python (>= 3.9)  
- Django (>= 4.0)  
- MySQL (for database management)  
- Virtual Environment (recommended)  
- Twilio / SMTP account (for SMS or email notifications)  

---

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/complaint-registration-system.git
   cd complaint-registration-system
   ```

2. **Create & activate virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   source venv/bin/activate # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**  
   Create a `.env` file in the root directory and add:
   ```env
   SECRET_KEY=your_django_secret_key
   DB_NAME=complaint_db
   DB_USER=root
   DB_PASSWORD=yourpassword
   DB_HOST=localhost
   DB_PORT=3306
   SMS_API_KEY=your_twilio_or_sms_key
   EMAIL_HOST_USER=your_email
   EMAIL_HOST_PASSWORD=your_email_password
   ```

5. **Apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**  
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.  

---
