from flask import Flask, render_template, request, redirect, session, url_for, send_file
import mysql.connector
from datetime import date, datetime
import bcrypt
import calendar
import io

app = Flask(__name__)

# Thiết lập session
app.secret_key = 'hong_son'

# Kết nối đến cơ sở dữ liệu
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="clinic management"
)

# Tạo một hàm toàn cục 'enumerate' và thêm nó vào môi trường Jinja2
def _enumerate(iterable, start=0):
    return enumerate(iterable, start=start)

app.jinja_env.globals.update(enumerate=_enumerate)

@app.route('/')
def home_page():
    return render_template('Guess/Home_page.html')

@app.route('/about-us')
def about_us():
    return render_template('Guess/About_us.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        # Tạo con trỏ để thực thi các truy vấn SQL
        mycursor = mydb.cursor()

        # Truy vấn SQL để kiểm tra thông tin đăng nhập
        sql = "SELECT * FROM users WHERE email = %s"
        val = (email, )
        mycursor.execute(sql, val)
        user = mycursor.fetchone()

        # Đóng con trỏ
        mycursor.close()

        # Kiểm tra xem có tìm thấy người dùng không
        if user:
            # Kiểm tra password và role
            check_password = bcrypt.checkpw(password.encode(), user[6])
            check_role = role == user[7]
            
            # Nếu password và role đúng
            if check_password and check_role:
                # Lưu thông tin người dùng vào session
                session['user_id'] = user[0]
                session['fullname'] = user[1]
                session['birthdate'] = user[2]
                session['gender'] = user[3]
                session['phone'] = user[4]            
                session['email'] = user[5]
                session['password'] = user[6]
                session['role'] = user[7]

                # Chuyển hướng đến trang tương ứng với vai trò
                if role == 'patient':
                    return redirect('/patient')
                elif role == 'doctor':
                    return redirect('/doctor')
                elif role == 'admin':
                    return redirect('/admin')
            else:
                # Chuyển hướng đến trang đăng nhập với thông báo lỗi
                return redirect(url_for('login', error='incorrect_login'))
                
        else:
            # Chuyển hướng đến trang đăng nhập với thông báo lỗi
            return redirect(url_for('login', error='no_account'))
    
    # Nếu là phương thức GET, hiển thị trang đăng nhập
    return render_template('Login/Login.html')

@app.route('/patient')
def patient():
    if not session:
        return redirect('/login')
    else:
        return render_template('Patient/Patient.html')

@app.route('/patient/about-us')
def patient_about_us():
    if not session:
        return redirect('/login')
    else:
        return render_template('Patient/Patient_about_us.html')

@app.route('/find-doctors', methods=['GET', 'POST'])
def find_doctors():
    if not session:
        return redirect('/login')
    else:
        user_role = session['role']
        mycursor = mydb.cursor(dictionary=True)
        
        # Tạo câu truy vấn SQL để lấy dữ liệu từ cơ sở dữ liệu
        sql = "SELECT users.user_id, fullname, gender, speciality, medical_expense FROM users INNER JOIN career_detail ON users.user_id = career_detail.user_id"
        
        # Thực thi câu truy vấn
        mycursor.execute(sql)
        
        # Lấy kết quả
        doctors = mycursor.fetchall()
            
        if request.method == 'POST':
            fullname = request.form.get('fullname', '').strip()
            gender = request.form.get('gender')
            speciality = request.form.get('speciality')
            qualification = request.form.get('qualification')
            medical_expense = request.form.get('medical_expense')
            
            params = []
            
            if fullname:
                sql += " AND fullname = %s"
                params.append(fullname)
            if gender:
                sql += " AND gender = %s"
                params.append(gender)
            if speciality:
                sql += " AND speciality = %s"
                params.append(speciality)
            if qualification:
                sql += " AND qualifications = %s"
                params.append(qualification)
            if medical_expense:
                sql += " AND medical_expense <= %s"
                params.append(medical_expense)
                    
            # Thực thi câu truy vấn
            mycursor.execute(sql, params)
            
            # Lấy kết quả
            doctors = mycursor.fetchall()
            mycursor.close()
            
        return render_template('Patient/Find_doctors.html', doctors = doctors, user_role = user_role)

@app.route('/doctor/<int:doctor_id>')
def doctor_detail(doctor_id):
    if not session:
        return redirect('/login')
    else:
        user_role = session['role']
        mycursor = mydb.cursor(dictionary=True)
        
        # Tạo câu truy vấn SQL để lấy thông tin chi tiết của bác sĩ
        sql = "SELECT * FROM users INNER JOIN career_detail ON users.user_id = career_detail.user_id WHERE users.user_id = %s"
        
        # Thực thi câu truy vấn
        mycursor.execute(sql, (doctor_id,))
        
        # Lấy kết quả
        doctor_info = mycursor.fetchone()
        
        # Tính năm bắt đầu làm việc
        current_year = datetime.now().year
        years_of_experience = doctor_info["years_of_experience"]
        start_year = current_year - int(years_of_experience)
        
        # Hiển thị số điện thoại theo dạng 1234-567-890
        phone = doctor_info["phone"]
        formatted_phone = '-'.join([phone[:4], phone[4:7], phone[7:]])
        
         # Lấy tháng và năm hiện tại
        today = date.today()
        year = today.year
        month = today.month
        
        # Kiểm tra nếu có tháng hoặc năm được gửi từ client
        year = request.args.get('year', default=year, type=int)
        month = request.args.get('month', default=month, type=int)
        
        # Tạo lịch tháng
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Hiện thông tin lịch hẹn
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM appointments WHERE user_id = %s"
        val = (doctor_id, )
        mycursor.execute(sql, val)
        appointments = mycursor.fetchall()
        
        appointment_days = {}
        for appointment in appointments:
            appointment_date = appointment['appointment']
            appointment_id = appointment['appointment_id']
            appointment_days[appointment_date.strftime('%Y-%m-%d')] = appointment_id     
        
        return render_template('Patient/Doctor_detail.html', doctor_info = doctor_info, start_year = start_year, 
                            year = year, month = month, month_days=month_days, month_name=month_name, today = today,
                            appointment_days = appointment_days, formatted_phone = formatted_phone, doctor_id = doctor_id, user_role = user_role)

@app.route('/doctor/<int:doctor_id>/<int:appointment_id>')
def appointment_detail(doctor_id, appointment_id):
    if not session:
        return redirect('/login')
    else:
        user_role = session['role']
        user_id = session.get('user_id')
        mycursor = mydb.cursor(dictionary=True)
        
        today = date.today()
        
        # Lấy thông tin bác sĩ
        sql = "SELECT * FROM users INNER JOIN career_detail on users.user_id = career_detail.user_id WHERE users.user_id=%s"
        val = (doctor_id, )
        mycursor.execute(sql, val)
        doctor_info = mycursor.fetchone()
        
        # Lấy số lượng người trong mỗi lịch hẹn
        sql = "SELECT COUNT(*) FROM appointment_detail WHERE appointment_id=%s"
        val = (appointment_id, )
        mycursor.execute(sql, val)
        appointment_quantity = mycursor.fetchone()['COUNT(*)']
        
        # Kiểm tra lịch hẹn đã qua hay chưa
        sql = "SELECT appointment FROM appointments WHERE appointment_id=%s"
        val = (appointment_id, )
        mycursor.execute(sql, val)
        appointment_check = mycursor.fetchone()
        
        # Hiển thị số điện thoại theo dạng 1234-567-890
        phone = doctor_info["phone"]
        formatted_phone = '-'.join([phone[:4], phone[4:7], phone[7:]])
        
        mycursor.close()
        return render_template("Patient/Appointment_detail.html", doctor_info = doctor_info, formatted_phone = formatted_phone, today = today, 
                            appointment_id = appointment_id, appointment_quantity = appointment_quantity, user_id = user_id, appointment_check =appointment_check, user_role = user_role)

@app.route('/patient/book-appointment/<int:doctor_id>/<int:appointment_id>', methods=['GET', 'POST'])
def book_appointment(doctor_id, appointment_id):
    if not session:
        return redirect('/login')
    else:
        mycursor = mydb.cursor(dictionary=True)
        user_id = session.get('user_id')
        if request.method == 'POST':
            # Kiểm tra xem người dùng đã đăng ký lịch hẹn chưa
            sql = "SELECT * FROM appointment_detail WHERE appointment_id=%s AND user_id=%s"
            val = (appointment_id, user_id)
            mycursor.execute(sql, val)
            user_book = mycursor.fetchone()
            
            # Nếu đã tồn tại
            if user_book:
                return(redirect(url_for("doctor_detail", doctor_id = doctor_id, error='book_exists')))
            else:
                sql = "INSERT INTO appointment_detail (appointment_id, user_id) VALUE (%s, %s)"
                val = (appointment_id, user_id)
                mycursor.execute(sql, val)
                mydb.commit()
                return(redirect(url_for('doctor_detail', doctor_id = doctor_id, success="booked_successfully")))

@app.route('/patient/appointments')
def patient_appointment():
    if not session:
        return redirect('/login')
    else:
        today = date.today()
        
        mycursor = mydb.cursor(dictionary=True)
        
        # Lấy thông tin bệnh nhân và danh sách lịch hẹn
        user_id = session.get("user_id")
        sql = """SELECT appointments.appointment, users.fullname, appointment_detail.appointment_detail_id FROM appointment_detail 
        INNER JOIN appointments ON appointment_detail.appointment_id=appointments.appointment_id
        INNER JOIN users ON appointments.user_id=users.user_id
        WHERE appointment_detail.user_id=%s ORDER BY appointment ASC"""
        val = (user_id, )
        mycursor.execute(sql, val)
        appointment_list = mycursor.fetchall()
        return render_template('Patient/Appointment.html', appointment_list = appointment_list, today = today)

@app.route('/patient/delete_appointment', methods=['POST'])
def patient_delete_appointment():
    if not session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            appointment_detail_id = request.form['appointment_detail_id']
            mycursor = mydb.cursor()
            sql = "DELETE FROM appointment_detail WHERE appointment_detail_id = %s"
            val = (appointment_detail_id,)
            mycursor.execute(sql, val)
            mydb.commit()
            mycursor.close()
            return redirect('/patient/appointments')

@app.route('/patient/appointments/past-appointment/<int:appointment_detail_id>')
def patient_past_appointment(appointment_detail_id):
    if not session:
        return redirect('/login')
    else:
        today = date.today()
        
        mycursor = mydb.cursor(dictionary=True)
        sql = """SELECT * FROM appointment_detail
        INNER JOIN appointments ON appointment_detail.appointment_id=appointments.appointment_id
        INNER JOIN users ON appointments.user_id=users.user_id
        INNER JOIN career_detail ON users.user_id=career_detail.user_id
        WHERE appointment_detail_id=%s"""
        val = (appointment_detail_id, )
        mycursor.execute(sql, val)
        past_appointment = mycursor.fetchone()
        return render_template("Patient/Past_appointment.html", past_appointment = past_appointment, today = today)

@app.route('/doctor')
def doctor():    
    if not session:
        return redirect('/login')
    else:
        return render_template('Doctor/Doctor.html')

@app.route('/doctor/appointments', methods=['GET', 'POST'])
def doctor_upload_appointment():
    if not session:
        return redirect('/login')
    else:    
        # Lấy id người dùng từ session
        user_id = session.get('user_id')
        
        today = date.today()
        # Lưu thông tin về lịch hẹn
        if request.method == 'POST':
            appointment_date = request.form['appointment_date']        
                
            # Tạo con trỏ để thực thi các truy vấn SQL
            mycursor = mydb.cursor()
            
            # Kiểm tra xem ngày được nhập đã có trong cơ sở dữ liệu hay chưa
            sql = "SELECT * FROM appointments WHERE user_id = %s AND appointment = %s"
            val = (user_id, appointment_date)
            mycursor.execute(sql, val)
            appointment = mycursor.fetchone()
            if appointment:            
                return redirect(url_for('doctor_upload_appointment', error='appointment_exists'))
            else:
                sql = "INSERT INTO appointments (user_id, appointment) VALUES (%s, %s)"
                val = (user_id, appointment_date)
                mycursor.execute(sql, val)
                mydb.commit()
                mycursor.close()
                return redirect(url_for('doctor_upload_appointment', success='uploaded_successfully'))

        # Lấy tháng và năm hiện tại
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Kiểm tra nếu có tháng hoặc năm được gửi từ client
        year = request.args.get('year', default=year, type=int)
        month = request.args.get('month', default=month, type=int)
        
        # Tạo lịch tháng
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Hiện thông tin lịch hẹn
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT * FROM appointments WHERE user_id = %s"
        val = (user_id, )
        mycursor.execute(sql, val)
        appointments = mycursor.fetchall()
        
        appointment_days = {}
        for appointment in appointments:
            appointment_date = appointment['appointment']
            appointment_id = appointment['appointment_id']
            appointment_days[appointment_date.strftime('%Y-%m-%d')] = appointment_id
        return render_template('Doctor/Appointments.html', today=today, year=year, month=month, month_days=month_days, month_name=month_name, appointment_days=appointment_days)

@app.route("/doctor/appointments/list-of-patients/<int:appointment_id>")
def list_of_patients(appointment_id):
    if not session:
        return redirect('/login')
    else:
        today = date.today()
        mycursor = mydb.cursor(dictionary=True)
        
        # Lấy thông tin người bệnh
        sql = """SELECT * FROM appointment_detail
        INNER JOIN users ON appointment_detail.user_id = users.user_id
        WHERE appointment_detail.appointment_id = %s"""
        val = (appointment_id,)
        mycursor.execute(sql, val)
        patients_info = mycursor.fetchall()
        
        # Lấy thông tin ngày hẹn
        sql = "SELECT appointment FROM appointments WHERE appointment_id=%s"
        val = (appointment_id,)
        mycursor.execute(sql, val)
        appointment = mycursor.fetchone()
        mycursor.close()
        return render_template("Doctor/List_of_patients.html", patients_info = patients_info, today = today, appointment = appointment, appointment_id = appointment_id)

@app.route('/doctor/appointments/patient-detail/<int:user_id>')
def patient_detail(user_id):
    if not session:
        return redirect('/login')
    else:
        today = date.today()
        
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id, ))
        user = mycursor.fetchone()
        
        mycursor.execute("SELECT medical_history, symptoms FROM medical_record WHERE user_id=%s", (user_id, ))
        medical_record = mycursor.fetchone()
        if not medical_record:
            medical_record = {
                'medical_history': "No description",
                'symptoms': "No description"
            }

        sql = """SELECT users.fullname, appointments.appointment, appointment_detail.doctor_prescription, appointment_detail.doctor_note
        FROM users
        INNER JOIN appointments ON users.user_id = appointments.user_id
        INNER JOIN appointment_detail ON appointment_detail.appointment_id = appointments.appointment_id
        WHERE appointment_detail.user_id = %s ORDER BY appointment ASC"""
        val = (user_id, )
        mycursor.execute(sql, val)
        past_appointments = mycursor.fetchall()
        
        mycursor.close()
        return render_template("Doctor/Patient_detail.html", user = user, medical_record = medical_record, past_appointments = past_appointments, today = today)

@app.route('/doctor/appointments/prescription/<int:appointment_id>/<int:user_id>', methods=['GET', 'POST'])
def patient_prescription(appointment_id, user_id):
    if not session:
        return redirect('/login')
    else:
        # Lấy thông tin
        mycursor = mydb.cursor(dictionary=True)
        sql = "SELECT doctor_prescription, doctor_note FROM appointment_detail WHERE appointment_id=%s AND user_id=%s"
        val = (appointment_id, user_id)
        mycursor.execute(sql, val)
        prescription = mycursor.fetchone()

        if request.method == 'POST':
            prescription = request.form['prescription']
            note = request.form['note']  or 'No description'
            
            # Lưu thông tin
            sql = "UPDATE appointment_detail SET doctor_prescription=%s, doctor_note=%s WHERE appointment_id=%s AND user_id=%s"
            val = (prescription, note, appointment_id, user_id)
            mycursor.execute(sql, val)
            mydb.commit()
            return redirect(url_for('list_of_patients', appointment_id=appointment_id))
        
        mycursor.close()
        return(render_template("Doctor/Patient_prescription.html", appointment_id = appointment_id, user_id = user_id, prescription = prescription))

@app.route('/doctor/delete_appointment', methods=['POST'])
def doctor_delete_appointment():
    if not session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            appointment_id = request.form['appointment_id']
            mycursor = mydb.cursor()
            sql = "DELETE FROM appointments WHERE appointment_id = %s"
            val = (appointment_id,)
            mycursor.execute(sql, val)
            mydb.commit()
            mycursor.close()
            return redirect('/doctor/appointments')

@app.route('/doctor/about-us')
def doctor_about_us():
    if not session:
        return redirect('/login')
    else:
        return render_template('Doctor/Doctor_about_us.html')

@app.route('/admin')
def admin():
    if not session:
        return redirect('/login')
    else:
        return render_template('Admin/Admin.html')

@app.route('/admin/about-us')
def admin_about_us():
    if not session:
        return redirect('/login')
    else:
        return render_template('Admin/Admin_about_us.html')

@app.route('/admin/create-account', methods=['GET', 'POST'])
def create_account():
    if not session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            fullname = request.form['fullname']
            birthdate = request.form['birthdate']
            gender = request.form['gender']
            phone = request.form['phone']
            email = request.form['email']
            password = request.form['password']
            role = request.form['role']

            # Tạo con trỏ để thực thi các truy vấn SQL
            mycursor = mydb.cursor()
            
            # Truy vấn SQL để kiểm tra xem địa chỉ email đã tồn tại trong cơ sở dữ liệu hay chưa
            sql = "SELECT * FROM users WHERE email = %s"
            val = (email,)
            mycursor.execute(sql, val)
            user = mycursor.fetchone()
            
            # Kiểm tra xem email đã tồn tại hay chưa
            if user:
                # Hiển thị thông báo lỗi và yêu cầu người dùng sử dụng một địa chỉ email khác
                return redirect(url_for('create_account', error='email_exists'))
            else:
                password = password
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(password.encode(), salt)
                # Nếu email chưa tồn tại, bạn có thể tiếp tục xử lý thông tin như bình thường
                # Thực thi truy vấn SQL để chèn dữ liệu vào cơ sở dữ liệu
                sql = "INSERT INTO users (fullname, birthdate, gender, phone, email, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                val = (fullname, birthdate, gender, phone, email, hashed_password, role)
                mycursor.execute(sql, val)

                # Lưu các thay đổi vào cơ sở dữ liệu
                mydb.commit()

                # Đóng con trỏ và kết nối với cơ sở dữ liệu
                mycursor.close()

                # Sau khi tài khoản đã được tạo thành công, chuyển hướng về trang đăng ký với thông báo thành công
                return redirect(url_for('create_account', success='created_successfully'))      
        return render_template('Admin/Create_account.html')

@app.route('/admin/delete-account', methods=['GET', 'POST'])
def delete_account():
    if not session:
        return redirect('/login')
    else:
        if request.method == 'POST':
            fullname = request.form['fullname']
            
            # Tạo con trỏ để thực thi các truy vấn SQL
            mycursor = mydb.cursor()
            
            # Xóa dữ liệu
            sql = "DELETE FROM users WHERE fullname = %s"
            val = (fullname,)
            mycursor.execute(sql, val)
            mydb.commit()
            
            # Đóng con trỏ và kết nối với cơ sở dữ liệu
            mycursor.close()
            
            # Sau khi tài khoản đã được tạo thành công, chuyển hướng về trang đăng ký với thông báo thành công
            return redirect(url_for('delete_account', success='deleted_successfully'))  
        return render_template('Admin/Delete_account.html')

@app.route('/profile')
def profile():
    # Lấy thông tin người dùng từ session hoặc từ đường dẫn
    user_id = session.get('user_id')

    # Truy vấn thông tin hồ sơ từ cơ sở dữ liệu
    mycursor = mydb.cursor(dictionary=True)
    mycursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = mycursor.fetchone()
    mycursor.close()

    if user:
         # Kiểm tra vai trò của người dùng
        if user['role'] == 'doctor':
            # Nếu vai trò là 'Doctor', lấy thông tin từ bảng 'career_detail'
            mycursor = mydb.cursor(dictionary=True)
            mycursor.execute("SELECT * FROM career_detail WHERE user_id = %s", (user_id,))
            career_detail = mycursor.fetchone()
            mycursor.close()
            
            if not career_detail:
                # Nếu không có thông tin career_detail, tạo một giá trị mặc định
                career_detail = {
                    'location': 'No description',
                    'speciality': 'No description', 
                    'qualifications': 'No description',
                    'years_of_experience': 'No',
                    'medical_expense': '0',
                    'medical_awards': 'No description',
                    'publications': 'No description',
                    'image': None
                }
            
            image_data = career_detail['image']
            show_profile_pic = url_for('profile_picture', user_id=user_id) if image_data else None
    
            #Hiển thị thông tin ở cả 2 bảng
            return render_template('All/Profile.html', user=user, career_detail=career_detail, show_profile_pic=show_profile_pic)
        
        elif user['role'] == 'patient':
            mycursor = mydb.cursor(dictionary=True)
            mycursor.execute("SELECT * FROM medical_record WHERE user_id = %s", (user_id,))
            medical_record = mycursor.fetchone()
            mycursor.close()
            
            if not medical_record:
                medical_record = {
                    'medical_history': 'No description',
                    'symptoms': 'No description'
                }
            return render_template('All/Profile.html', user=user, medical_record=medical_record)
        
        else:
            # Nếu vai trò không phải 'Doctor' hoặc 'Patient', chỉ hiển thị thông tin cơ bản
            return render_template('All/Profile.html', user=user)
    else:
        # Xử lý trường hợp không tìm thấy thông tin hồ sơ
        return "Không tìm thấy thông tin hồ sơ"

@app.route('/profile-picture/<int:user_id>')
def profile_picture(user_id):
    mycursor = mydb.cursor()
    mycursor.execute("SELECT image FROM career_detail WHERE user_id=%s", (user_id,))
    result = mycursor.fetchone()
    mycursor.close()
    
    if result and result[0]:
        image_data = result[0]
        return send_file(io.BytesIO(image_data), mimetype='image/jpeg')
    else:
        return "No image found", 404

@app.route('/back')
def back():
    user_role = session.get('role')
    if user_role == 'doctor':
        # Redirect to the doctor page
        return redirect(url_for('doctor'))
    elif user_role == 'patient':
        # Redirect to the patient page
        return redirect(url_for('patient'))
    else:
        return redirect(url_for('admin'))
    

@app.route('/edit-profile', methods=['GET', 'POST'])
def edit_profile():
    if not session:
        return redirect('/login')
    else:
        # Lấy id người dùng từ session
        user_id = session.get('user_id')
        user_role = session.get('role')

        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        user = mycursor.fetchone()

        # Tìm thông tin career_detail
        mycursor.execute("SELECT * FROM career_detail WHERE user_id = %s", (user_id,))
        career_detail = mycursor.fetchone()
        
        # Tìm thông tin medical_record
        mycursor.execute("SELECT * FROM medical_record WHERE user_id = %s", (user_id,))
        medical_record = mycursor.fetchone()
        
        # Nhận thông tin từ form chỉnh sửa hồ sơ
        if request.method == 'POST':
            fullname = request.form['fullname']
            email = request.form['email']
            birthdate = request.form['birthdate']
            gender = request.form['gender']
            phone = request.form['phone']
            
            # Kiểm tra xem email đã tồn tại hay chưa
            if email != user['email']:
                mycursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                existing_user = mycursor.fetchone()
                if existing_user:
                    return redirect(url_for('edit_profile', error='email_exists'))
            # Thực hiện cập nhật thông tin hồ sơ vào cơ sở dữ liệu
            else:
                mycursor.execute(
                    """
                    UPDATE users SET 
                    fullname=%s, email=%s, birthdate=%s, gender=%s, phone=%s WHERE user_id=%s
                    """,
                    (fullname, email, birthdate, gender, phone, user_id))
                
                # Lưu thông tin career_detail nếu có
                if user_role == 'doctor':
                    location = request.form['location']
                    speciality = request.form['speciality']
                    qualifications = request.form['qualifications']
                    years_of_experience = request.form['years_of_experience']
                    medical_expense = request.form['medical_expense']
                    medical_awards = request.form['medical_awards'] or 'No description'
                    publications = request.form['publications'] or 'No description'
                    
                    # Kiểm tra và lưu file ảnh nếu có
                    profile_picture = request.files.get('profile_picture')
                    image_data = profile_picture.read() if profile_picture else None
                    
                    # Nếu không có thì thêm vào
                    if not career_detail:
                        mycursor.execute(
                        """
                        INSERT INTO career_detail 
                        (user_id, location, speciality, qualifications, years_of_experience, medical_expense, publications, medical_awards, image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, 
                        (user_id, location, speciality, qualifications, years_of_experience, medical_expense, publications, medical_awards, image_data))
                        
                    # Nếu có thì cập nhật
                    else:
                        if image_data:
                            mycursor.execute(
                            """
                            UPDATE career_detail SET
                            location=%s, speciality=%s, qualifications=%s, years_of_experience=%s, publications=%s, medical_expense=%s, medical_awards=%s, image=%s WHERE user_id=%s
                            """, 
                            (location, speciality, qualifications, years_of_experience, publications, medical_expense, medical_awards, image_data, user_id))
                        else:
                            mycursor.execute(
                            """
                            UPDATE career_detail SET
                            location=%s, speciality=%s, qualifications=%s, years_of_experience=%s, publications=%s, medical_expense=%s, medical_awards=%s WHERE user_id=%s
                            """, 
                            (location, speciality, qualifications, years_of_experience, publications, medical_expense, medical_awards, user_id))
                # Lưu thông tin medical_record nếu có
                elif user_role == 'patient':
                    medical_history = request.form['medical_history'] or 'No description'
                    symptoms = request.form['symptoms'] or 'No description'
                    
                    # Nếu không có thì thêm vào
                    if not medical_record:
                        mycursor.execute(
                        """
                        INSERT INTO medical_record
                        (user_id, medical_history, symptoms) VALUES (%s, %s, %s)
                        """,
                        (user_id, medical_history, symptoms))
                    
                    # Nếu có thì cập nhật
                    else:
                        mycursor.execute(
                        """
                        UPDATE medical_record SET 
                        medical_history=%s, symptoms=%s WHERE user_id=%s
                        """,
                        (medical_history, symptoms, user_id))
                mydb.commit()
                mycursor.close()
                return redirect('/profile')

        mycursor.close()
        return render_template('All/Edit_profile.html', user=user, career_detail = career_detail, medical_record = medical_record)

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if not session:
        return redirect('/login')
    else:
        user_id = session.get('user_id')
        
        # Lấy thông tin mật khẩu của người dùng
        mycursor = mydb.cursor(dictionary=True)
        mycursor.execute("SELECT password, role FROM users WHERE user_id=%s", (user_id, ))
        user = mycursor.fetchone()
        
        # Xử lý thông tin từ form
        if request.method == 'POST':
            current_pass = request.form['current_pass']
            new_pass = request.form['new_pass']
            confirm_pass = request.form['confirm_pass']
            
            if not bcrypt.checkpw(current_pass.encode(), user['password']):
                mycursor.close()
                return redirect(url_for('change_password', error="different_current_pass"))
            elif new_pass != confirm_pass:
                mycursor.close()
                return redirect(url_for('change_password', error="different_confirm_pass"))
            else:
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(confirm_pass.encode(), salt)
                mycursor.execute("UPDATE users SET password=%s WHERE user_id=%s", (hashed_password, user_id))
                mydb.commit()   
                mycursor.close()
                return redirect(url_for('profile', success="password_changed_successfully"))
        else:
            mycursor.close()
            return render_template("All/Change_password.html", user=user)

@app.route('/logout')
def log_out():
    # Xóa toàn bộ session
    session.clear()
    return redirect('/')    

if __name__ == '__main__':
    app.run(debug=True)