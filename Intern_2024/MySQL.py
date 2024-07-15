import mysql.connector
import bcrypt

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="clinic management"
)

mycursor = mydb.cursor()

# mycursor.execute("CREATE DATABASE `clinic management`")

mycursor.execute("""
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(255) NOT NULL,
    birthdate DATE NOT NULL,
    gender ENUM('Male', 'Female') NOT NULL,
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password BLOB NOT NULL,
    role ENUM('patient', 'doctor', 'admin') NOT NULL
)
""")

# Tạo account cho super_admin
password = '123'
salt = bcrypt.gensalt()
hashed_password = bcrypt.hashpw(password.encode(), salt)
sql = "INSERT INTO users (fullname, birthdate, gender, phone, email, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)"
val = ("Bùi Hồng Sơn", "2002/12/14", "Male", "0934575841", "son@gmail.com", hashed_password, "Admin")
mycursor.execute(sql, val)
mydb.commit()

mycursor.execute("""
CREATE TABLE career_detail (
    career_detail_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    location TEXT NOT NULL,
    speciality ENUM('Cardiology', 'Neurology', 'Orthopedics', 'Dermatology', 'Ophthalmology', 'Psychiatry', 'Oncology', 'Pediatrics', 'Obstetrics', 'Endocrinology') NOT NULL,
    qualifications ENUM('Bachelor''s degree', 'Master''s degree', 'Doctoral degree', 'Associate''s degree') NOT NULL,
    years_of_experience INT NOT NULL,
    medical_expense INT NOT NULL,
    medical_awards TEXT,
    publications TEXT,
    image LONGBLOB,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

mycursor.execute("""
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    appointment DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
""")

mycursor.execute("""
CREATE TABLE appointment_detail (
    appointment_detail_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT,
    user_id INT,
    doctor_prescription TEXT,
    doctor_note TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE CASCADE
)
""")

mycursor.execute("""
CREATE TABLE medical_record (
    medical_record_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    medical_history TEXT,
    symptoms TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
)
""")

mycursor.close()