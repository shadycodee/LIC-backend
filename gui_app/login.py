import tkinter as tk
from tkinter import messagebox
import MySQLdb
from datetime import datetime, timedelta
import time
from tkinter import PhotoImage
import os
from PIL import Image, ImageTk
import django
import sys
from django.conf import settings
from pathlib import Path
from tkinter import ttk
from tkinter import Toplevel

# Determine the Django project directory
# Adjust this path to point to your Django project directory
DJANGO_PROJECT_PATH = str(Path(__file__).resolve().parent.parent)
sys.path.append(DJANGO_PROJECT_PATH)

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LIC_Connect.settings')  # Replace with your actual settings module
django.setup()

# Django setup test code - ADD THIS HERE
# try:
#     print(f"Django Version: {django.get_version()}")
#     print(f"Settings module: {os.environ['DJANGO_SETTINGS_MODULE']}")
#     print(f"Database name: {settings.DATABASES['default']['NAME']}")
#     print("Django configured successfully!")
# except Exception as e:
#     print(f"Django configuration error: {e}")
#     sys.exit(1)

# Now you can safely import Django models and utilities
from students.models import Student, Session  # Adjust import based on your actual model names

class StudentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Login System")
        
        # Fullscreen for login
        self.root.attributes('-fullscreen', True)
        
        self.logged_in_student = None
        self.login_time = None
        self.elapsed_time = timedelta(0)
        
        
        # Create login screen
        self.create_login_screen()

        
    def create_login_screen(self):
        self.clear_screen()
        
        self.root.deiconify()
        self.root.focus_force()
        self.root.wm_attributes("-topmost", 1)

        
        
         #Disable closing application
        # self.root.protocol("WM_DELETE_WINDOW", lambda: messagebox.showinfo("Information", "Request denied"))
        container = tk.Frame(self.root)
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        login_frame = tk.Frame(container)
        login_frame.grid(row=0, column=0)

        # Load and display the image
        image_path = r"backend/gui_app/gui_logo.png"
        if os.path.exists(image_path):
            img = Image.open(image_path)
            img.thumbnail((100, 100))
            image = ImageTk.PhotoImage(img)
            image_label = tk.Label(login_frame, image=image)
            image_label.grid(row=0, column=0, padx=10, pady=10, sticky='w')  # Place the image label in the leftmost column and spanning 4 rows
            image_label.image = image  # Keep a reference to avoid garbage collection

         # Add additional text
        self.additional_text = tk.Label(login_frame, text="LIC CONNECT", fg="maroon", font=("Helvetica", 25, "bold"), justify='center')
        self.additional_text.grid(row=0, column=1, columnspan=2, pady=10)

        self.label1 = tk.Label(login_frame, text="Student ID")
        self.label1.grid(row=1, column=0, padx=10, pady=10, sticky='e')  # Align label to the right
        
        self.entry1 = tk.Entry(login_frame, width= 35)
        self.entry1.grid(row=1, column=1, padx=10, pady=10)
        
        self.label2 = tk.Label(login_frame, text="Password",)
        self.label2.grid(row=2, column=0, padx=10, pady=10, sticky='e')  # Align label to the right
        
        self.entry2 = tk.Entry(login_frame, show="*", width= 35)
        self.entry2.grid(row=2, column=1, padx=10, pady=10)
        
        self.login_button = tk.Button(login_frame, text="Login", command=self.login, width= 45)
        self.login_button.grid(row=3, column=0, columnspan=2, pady=10)
        self.login_button.bind("<Enter>", self.on_enter)
        self.login_button.bind("<Leave>", self.on_leave)
        # # Add an image
        # image = PhotoImage(file="gui_logo.png")  # Change "path_to_your_image.png" to the actual path
        # image_label = tk.Label(login_frame, image=image)
        # image_label.grid(row=3, column=0, columnspan=2, pady=10)
        # image_label.image = image  # Keep a reference to avoid garbage collection
    # Function to change button color on hover

    def on_enter(self, event):
        event.widget.config(bg='lightblue')  # Change the color on hover

    def on_leave(self, event):
        event.widget.config(bg='SystemButtonFace')  # Reset to default color
    def on_menu_screen_close(self):
        self.logout()
    def create_change_password_screen(self, student_id):
        # Open a new window for changing password
        change_password_window = tk.Toplevel(self.root)
        change_password_window.transient(self.root)
        change_password_window.grab_set()
        change_password_window.title("Change Password")
            
        # Set dimensions for the child window
        window_width = 300
        window_height = 200

        # Calculate position to center the window
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()

        pos_x = root_x + (root_width // 2) - (window_width // 2)
        pos_y = root_y + (root_height // 2) - (window_height // 2)

        change_password_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")

        # Override Configure event to revert to the fixed position
        def prevent_dragging(event):
            change_password_window.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        
        change_password_window.bind("<Configure>", prevent_dragging)

        tk.Label(change_password_window, text="New Password:").grid(row=1, column=0, padx=10, pady=10)
        new_password_entry = tk.Entry(change_password_window, show="*")
        new_password_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(change_password_window, text="Confirm New Password:").grid(row=2, column=0, padx=10, pady=10)
        confirm_password_entry = tk.Entry(change_password_window, show="*")
        confirm_password_entry.grid(row=2, column=1, padx=10, pady=10)

        message_label = tk.Label(change_password_window, text="", fg="red")
        message_label.grid(row=3, column=1, pady=5)

        tk.Button(change_password_window, text="Change Password", 
                  command=lambda: self.change_password(student_id,
                                                       message_label,
                                                         new_password_entry.get(), 
                                                         confirm_password_entry.get(),
                                                         change_password_window)).grid(row=4, columnspan=2, pady=10)
        
    def change_password(self, student_id, message_label, new_password, confirm_password, change_password_window):
        if new_password != confirm_password:
            message_label.config(text="Password do not match.")
            return

        try:
            # get student ID
            student = Student.objects.get(studentID=student_id)
            # Update the password
            from django.contrib.auth.hashers import make_password
            student.password = make_password(new_password)
            student.save()

            messagebox.showinfo("Success", "Password changed successfully!")
            # Destroy the pop-up window
            change_password_window.destroy()
             # Clear login input fields
            self.entry1.delete(0, tk.END)  # Assuming entry1 is the Student ID field
            self.entry2.delete(0, tk.END)  # Assuming entry2 is the Password field

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def create_menu_screen(self):
        self.clear_screen()

        self.root.attributes('-fullscreen', False)
        self.root.geometry('250x200')
        self.root.protocol("WM_DELETE_WINDOW", self.on_menu_screen_close)
        
        self.elapsed_time = timedelta(0)
        self.login_time = datetime.now()
        
        # Create a container frame
        container = tk.Frame(self.root)
        container.grid(row=0, column=0, sticky='nsew')
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # Create the menu frame
        menu_frame = tk.Frame(container)
        menu_frame.grid(row=0, column=0, padx=10, pady=10)

        # Timer label centered
        self.timer_label = tk.Label(menu_frame, text="Time Elapsed: 00:00:00", font=("Helvetica", 16))
        self.timer_label.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')  # Center label with columnspan

        # Create a frame for buttons to manage their layout
        button_frame = tk.Frame(menu_frame)
        button_frame.grid(row=1, column=0, sticky='nsew')

        # Check History button on the left
        self.check_history_button = tk.Button(button_frame, text="Check History", command=self.check_history)
        self.check_history_button.grid(row=0, column=0, padx=10, pady=10)

        # Logout button on the right
        self.logout_button = tk.Button(button_frame, text="Logout", command=self.logout)
        self.logout_button.grid(row=0, column=1, padx=10, pady=10)

        # Configure button frame to expand
        button_frame.grid_columnconfigure(0, weight=1)  # Allow Check History button to expand
        button_frame.grid_columnconfigure(1, weight=1)  # Allow Logout button to expand
        
        
        
        self.update_timer()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
    def debug_password_verification(self):
        student_id = self.entry1.get()
        password = self.entry2.get()
        
        
        try:

            student = Student.objects.get(studentID=student_id)
            stored_password = student.password

            # print(f"Debugging password verification:")
            # print(f"1. Entered password: {password}")
            # print(f"2. Stored hashed password: {stored_password}")

           
            from django.contrib.auth.hashers import check_password
            is_valid = check_password(password, stored_password)
        
            
            return is_valid
        except Student.DoesNotExist:
            # print(f"No student found with ID: {student_id}")
            return False
        except Exception as e:
            # print(f"Error during password verification: {e}")
            return False

    def login(self):
        student_id = self.entry1.get()
        password = self.entry2.get()

        try:
            student = Student.objects.get(studentID=student_id)
            is_valid = self.debug_password_verification()

            if not is_valid:
                messagebox.showerror("Error", "Invalid StudentID or Password")
                return
            
            # Check if the user is already logged in
            if student.is_logged_in:
                messagebox.showinfo("Info", "This student is already logged in.")
                return

            # Check for default password and force change
            if password == '123456':
                self.create_change_password_screen(student_id)
                return

            # Check if student has time left
            if student.time_left == 0:
                messagebox.showerror("Error", "No time left. Login not allowed.")
                return

            # Update is_logged_in to True
            student.is_logged_in = True
            student.save()

            self.logged_in_student = student
            self.time_left = timedelta(minutes=student.time_left)
            self.login_time = datetime.now()

            Session.objects.create(
                date=self.login_time.date(),
                loginTime=self.login_time.time(),
                parent=student,
                course=student.course
            )

            
            self.create_menu_screen()
            self.start_timer()

        except Student.DoesNotExist:
            messagebox.showerror("Error", "Invalid StudentID or Password")
        except Exception as e:
            # print(f"Login error: {e}")
            messagebox.showerror("Error", f"An error occurred during login: {e}")

        

    def logout(self):
        if self.logged_in_student:
            if self.login_time:  # Ensure login_time is not None
                logout_time = datetime.now()
                time_logged_in = (logout_time - self.login_time).total_seconds() // 60

                # Update session using Django model
                session = Session.objects.filter(
                    parent=self.logged_in_student,
                    logoutTime__isnull=True
                ).latest('loginTime')
                
                session.logoutTime = logout_time
                session.consumedTime = time_logged_in
                session.save()

                # Update student's time left
                self.logged_in_student.time_left -= time_logged_in
                self.logged_in_student.save()

                # Set is_logged_in to False
                self.logged_in_student.is_logged_in = False
                self.logged_in_student.save()

                self.logged_in_student = None
                self.login_time = None
                self.elapsed_time = timedelta(0)
                self.root.deiconify()
                self.root.focus_force()
                self.root.attributes('-fullscreen', True)
                self.create_login_screen()
                
            else:
                messagebox.showerror("Error", "Login time is not set. Please log in again.")
        else:
            messagebox.showerror("Error", "No student is logged in")

    def check_history(self):
        if self.logged_in_student:
            try:
                # Use Django ORM to retrieve sessions for the logged-in student
                sessions = Session.objects.filter(parent=self.logged_in_student)

                if sessions.exists():
                    # Create a new window to display session history
                    history_window = tk.Toplevel(self.root)
                    history_window.title("Session History")
                    history_window.geometry("500x300")

                    # Create a Treeview widget to display the history in tabular form
                    tree = ttk.Treeview(history_window, columns=("Date", "Login Time", "Logout Time", "Time Consumed"), show="headings", height=10)
                    tree.pack(expand=True, fill='both')

                    # Define column headings
                    tree.heading("Date", text="Date")
                    tree.heading("Login Time", text="Login")
                    tree.heading("Logout Time", text="Logout")
                    tree.heading("Time Consumed", text="Time Consumed(minutes)")

                    # Define column widths
                    tree.column("Date", width=100)
                    tree.column("Login Time", width=100)
                    tree.column("Logout Time", width=100)
                    tree.column("Time Consumed", width=100)

                    # Iterate through sessions and insert into the Treeview
                    for session in sessions:
                        date = session.date
                        # Format loginTime and logoutTime to display only HH:MM:SS
                        logintime = session.loginTime.strftime("%H:%M:%S")

                        if session.logoutTime:
                            logouttime = session.logoutTime.strftime("%H:%M:%S")
                        else:
                            logouttime = 'Still logged in'

                        # Time consumed (assuming it is in minutes)
                        timeconsumed = session.consumedTime

                        # Insert session details as a new row in the tree
                        tree.insert("", "end", values=(date, logintime, logouttime, timeconsumed))
                else:
                    messagebox.showerror("Error", "No session history found for this student")
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred: {e}")
        else:
            messagebox.showerror("Error", "No student is logged in")


    def start_timer(self):
        self.update_timer()

    def update_timer(self):
        # Check if the user is logged in and login_time is set
        if self.logged_in_student and self.login_time:
            now = datetime.now()
            elapsed = now - self.login_time
            remaining_time = self.time_left - elapsed

            if remaining_time <= timedelta(seconds=0):
                self.timer_label.config(text="Time Left: 00:00:00")
                self.logout()
                return

            remaining_seconds = int(remaining_time.total_seconds())
            formatted_time = time.strftime("%H:%M:%S", time.gmtime(remaining_seconds))
            self.timer_label.config(text=f"Time Left: {formatted_time}")

            # Show warning messages at specific time intervals
            if remaining_seconds == 600:  # 10 minutes
                self.show_topmost_message("Warning", "Only 10 minutes left!")
            elif remaining_seconds == 300:  # 5 minutes
                self.show_topmost_message("Warning", "Only 5 minutes left!")
            elif remaining_seconds == 60:  # 1 minute
                self.show_topmost_message("Warning", "Only 1 minute left!")

            # Update every second
            self.root.after(1000, self.update_timer)
        else:
            # Handle the case where the user is not logged in
            self.timer_label.config(text="Time Left: 00:00:00")
            messagebox.showerror("Error", "User is not logged in. Please log in.")
    
    def show_topmost_message(self, title, message):
        # Create a custom top-level window that behaves like a message box but stays on top
        topmost_window = Toplevel(self.root)
        topmost_window.title(title)
        topmost_window.geometry("300x100")
        topmost_window.attributes("-topmost", True)
        topmost_window.grab_set()

        # Configure the message label and OK button
        message_label = tk.Label(topmost_window, text=message, padx=20, pady=10, wraplength=250)
        message_label.pack()
        
        ok_button = tk.Button(topmost_window, text="OK", command=topmost_window.destroy)
        ok_button.pack(pady=5)

def main():
    root = tk.Tk()
    app = StudentApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
