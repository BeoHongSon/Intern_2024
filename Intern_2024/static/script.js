// Tạo một hàm riêng biệt để xử lý các thông báo
function handleMessages() {
    // Kiểm tra nếu URL chứa thông báo "success"
    const urlParams = new URLSearchParams(window.location.search);
    const successMessage = urlParams.get('success');
    if (successMessage === 'created_successfully') {
        alert('Account created successfully!');
    }if (successMessage === 'deleted_successfully') {
        alert('Account deleted successfully!');
    } else if (successMessage === 'booked_successfully') {
        alert('Appointment booked successfully!');
    } else if (successMessage === 'uploaded_successfully') {
        alert('Appointment uploaded successfully!');
    } else if (successMessage === 'password_changed_successfully') {
        alert('Password changed successfully!');
    }
    
    // Kiểm tra xem URL có chứa thông báo lỗi không
    const errorMessage = urlParams.get('error');
    if (errorMessage === 'incorrect_login') {
        alert('Login information (password or role) is incorrect. Please try again!');
    } else if (errorMessage === 'no_account') {
        alert("Account doesn't exists. Please check email again!");
    } else if (errorMessage === 'email_exists') {
        alert('Email already exists in the system. Please use a different email address.');
    } else if (errorMessage === 'appointment_exists') {
        alert('You have already uploaded an appointment on this day! Please choose another day!');
    } else if (errorMessage === 'book_exists') {
        alert('You have already booked an appointment on this day! Please choose another day!');
    } else if (errorMessage === 'different_current_pass') {
        alert('The current password is incorrect! Please enter again!');
    } else if (errorMessage === 'different_confirm_pass') {
        alert('Your new password and confirm password are not the same! Please enter again!');
    }
}

// Gọi hàm handleMessages khi trang được tải
window.onload = handleMessages;
