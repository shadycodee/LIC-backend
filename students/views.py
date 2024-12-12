from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Student, Transaction, Staff, Session, Semester, StaffActivityLog, ActivityLog, log_staff_activity
from .serializers import StudentSerializer, TransactionSerializer, StaffSerializer, UserLoginSerializer, StaffLoginSerializer, StaffUserSerializer, StaffStatusSerializer, SessionSerializer, StaffActivityLogSerializer, ActivityLogSerializer, StudentTypeSerializer, ChangePasswordSerializer, SemesterSerializer, SessionHoursSerializer, PaymentIncomeSerializer
from rest_framework.views import APIView
from rest_framework import generics, viewsets
from django.conf import settings 
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.permissions import AllowAny 
from django.contrib.auth.models import User
import json
from rest_framework.decorators import api_view
import logging
from django.utils import timezone
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, date, time, timedelta
from datetime import datetime
from django.db.models import Sum
from django.db.models.functions import ExtractMonth
from django.db.models import Count
import openpyxl
from django.http import HttpResponse

logger = logging.getLogger(__name__)

class StudentViewSet(ModelViewSet):
    
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = 'studentID'  # Use studentID as the lookup field instead of pk

    def get_object(self):
        student_id = self.kwargs['studentID']
        # Try to find the student by formatted studentID first
        try:
            return Student.objects.get(studentID=student_id)
        except Student.DoesNotExist:
            # If studentID format fails, try without the format (or handle case)
            return Student.objects.get(studentID=student_id.replace('-', ''))  
        

class ResetPasswordView(APIView):

    def post(self, request, studentID):
        try:
            # Fetch the student by studentID
            student = Student.objects.get(studentID=studentID)
            default_password = '123456'

            # Check if the current password is already the default
            if check_password(default_password, student.password):
                return Response({"message": "Current password is already the default."}, status=status.HTTP_400_BAD_REQUEST)

            # Reset the password
            student.password = make_password(default_password)
            student.is_logged_in = False
            student.save()

            # Log the password reset action
            staff_username = request.user.username  # The username of the staff performing the reset
            
            # Log activity
            log_data = {
                "username": staff_username,
                "action": f"Reset password for student {studentID}",
                "timestamp": timezone.now()  # Auto-generate the timestamp here
            }
            log_activity(request._request)  # Pass the raw Django request object

            return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)

        except Student.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")
            return Response({"error": "An internal error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

class TransactionCreateView(APIView):
    
    def post(self, request, *args, **kwargs):
        # Retrieve data from the request
        reference_number = request.data.get('reference_number')
        student_id = request.data.get('student_id')
        hours_to_add = request.data.get('hours')
        receipt_image = request.FILES.get('receipt')  # Retrieve the uploaded receipt image

        # Validate required fields
        if not reference_number or not student_id or not hours_to_add:
            return Response({"error": "Reference number, hours, and student ID are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the student exists
        try:
            student = Student.objects.get(studentID=student_id)
        except Student.DoesNotExist:
            return Response({"error": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the reference number has already been used
        if Transaction.objects.filter(reference_number=reference_number).exists():
            return Response({"error": "This reference number has already been used"}, status=status.HTTP_400_BAD_REQUEST)

         # Calculate amount based on hours_to_add
        amount = int(hours_to_add) * 15  # 15 for each hour (1 hour -> 15, 2 hours -> 30, etc.)

        # Create a new transaction
        transaction = Transaction.objects.create(
            student=student,
            reference_number=reference_number,
            receipt_image=receipt_image,  # Save the image file in the transaction
            amount = amount
        )

        # Update student's time_left (convert hours to minutes and add)
        student.time_left += int(hours_to_add) * 60  # Adding hours in minutes
        student.save()

        # Serialize and return the created transaction
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        # Retrieve the active semester (or filter based on your needs)
        sem = Semester.objects.first()  # Or use a filter to get the active semester
        
        # Filter transactions by semester name and year
        return Transaction.objects.filter(semester_name=sem.semester_name, year=sem.year)

@csrf_exempt
def student_login_view(request):
    if request.method == "POST":
        studentID = request.POST.get('studentID')
        password = request.POST.get('password')


        try:
            student = Student.objects.get(studentID=studentID)
            if not check_password(password, student.password):
                return JsonResponse({"error": "Invalid credentials"}, status=400)
            
            if password == '123456':
                return JsonResponse({"error": "Password reset required. Please change your password."}, status=401)
            if student.is_logged_in:
                return JsonResponse({"error": "Already logged in"}, status=400)
            if student.time_left == 0:
                return JsonResponse({"error": "No time left. Login not allowed."}, status=400)
            

            student.is_logged_in = True
            student.save()
            time_left = student.time_left

            Session.objects.create(
                date=date.today(),
                loginTime=datetime.now().time(),
                parent=student,
                course=student.course
            )

            response_data = {
                "message": "Login successful",
                "time_left": time_left,  # Return time left as number of seconds
            }
            return JsonResponse(response_data)
        except Student.DoesNotExist:
            return JsonResponse({"error": "Invalid StudentID or Password"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def student_logout_view(request):
    if request.method == "POST":
        studentID = request.POST.get('studentID')

        try:
            student = Student.objects.get(studentID=studentID)

            if not student.is_logged_in:
                return JsonResponse({"error": "User is not logged in"}, status=400)

            # Get the active session
            session = Session.objects.filter(parent=student, logoutTime__isnull=True).first()

            if not session:
                return JsonResponse({"error": "No active session found"}, status=400)

            # Set logoutTime
            logout_time = datetime.now().time()
            session.logoutTime = logout_time

            # Calculate consumedTime (difference between loginTime and logoutTime)
            logout_time = datetime.now()
            login_time = session.loginTime
            login_time = datetime.combine(datetime.today(), login_time)
            consumed_time = logout_time - login_time
            print("Consumed Time: ", consumed_time)

            # Calculate hours, minutes, and seconds from the timedelta
            hours = consumed_time.seconds // 3600
            minutes = (consumed_time.seconds % 3600) // 60

            hours *= 60
            consumed_time_as_time = hours + minutes
            session.consumedTime = consumed_time_as_time
            session.save()

            # Mark the student as logged out
            student.is_logged_in = False
            student.time_left -= consumed_time_as_time
            student.save()

            return JsonResponse({"message": "Logout successful"})

        except Student.DoesNotExist:
            return JsonResponse({"error": "Invalid StudentID"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def student_change_password_view(request):
    if request.method == "POST":
        studentID = request.POST.get('studentID')
        new_password = request.POST.get('new_password')

        try:
            student = Student.objects.get(studentID=studentID)
            student.password = make_password(new_password)
            student.save()

            return JsonResponse({"message": "Password Changed successfully"})

        except Exception as e:
           return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt    
def check_history_view(request):
    if request.method == "POST":
        studentID = request.POST.get('studentID')
        semester = Semester.objects.first()
        year = semester.year
        sem = semester.semester_name
        sessions = Session.objects.filter(parent_id=studentID, semester_name=sem, year=year)
        session_data = []

        for session in sessions:
            try:
                session_data.append({
                    "date": session.date,  # Assuming date stored as expire_date
                    "loginTime": session.loginTime,
                    "logoutTime": session.logoutTime or "N/A",
                    "consumedTime": session.consumedTime,
                })
            except AttributeError as e:
                # Handle missing fields or model errors gracefully.
                session_data.append({"error": f"Session data error: {e}"})

        return JsonResponse({"sessions": session_data})

    return JsonResponse({"error": "Invalid request method"}, status=405)


    
class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'status': 'success',
            'token': token.key,
            'user_id': user.id,
            'username': user.username
        }, status=status.HTTP_200_OK) 
    
class LogoutView(APIView):
    # Remove or comment this out to allow unauthenticated access
    # permission_classes = [IsAuthenticated]  

    def post(self, request):
        try:
            token = request.auth  # Get the user's token
            print(token)
            if token is None:
                # If there is no token, just return a success message
                return Response({"message": "No token found. Successfully logged out."}, status=status.HTTP_200_OK)

            # Delete the token to log out
            token.delete()  
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class StaffCreateView(APIView):
    permission_classes = [AllowAny]  # Allow access to anyone

    def post(self, request, *args, **kwargs):
        serializer = StaffUserSerializer(data=request.data)

        # Check if the serializer is valid
        if serializer.is_valid():
            # Create the user with the default values for is_staff and is_superuser
            password = '123456'
            staff = User.objects.create(
                username=serializer.validated_data['username'],
                first_name=serializer.validated_data['first_name'],
                last_name=serializer.validated_data['last_name'],
                is_staff=True,  # Default to staff
                is_superuser=False  # Default to non-superuser
            )
            staff.set_password(password)  # Hash the password
            staff.save()

            return Response({
                "message": "User created successfully",
                "data": StaffUserSerializer(staff).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StaffListView(generics.ListAPIView):
    queryset = User.objects.filter(is_staff=True)  # Filter for staff users
    serializer_class = StaffUserSerializer
   
class UpdateStaffStatusView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = StaffStatusSerializer

    def get_object(self):
        username = self.kwargs.get("username")
        return generics.get_object_or_404(User, username=username)

    def patch(self, request, *args, **kwargs):
        # Retrieve the user instance based on the username
        user = self.get_object()
        return self.update(request, *args, **kwargs)

class ImportStudentView(APIView):
    def post(self, request, *args, **kwargs):
        student_data = request.data  # Expecting JSON data (list of students)

        # Check if the data is a list (multiple student records)
        if not isinstance(student_data, list):
            return Response({"error": "Invalid data format. Expected a list."}, status=status.HTTP_400_BAD_REQUEST)

        inserted_students = []
        duplicate_students = []

        for student_info in student_data:
            # Check if the student already exists based on studentID
            if Student.objects.filter(studentID=student_info.get('studentID')).exists():
                duplicate_students.append(student_info)  # Track duplicate records
            else:
                serializer = StudentSerializer(data=student_info)
                if serializer.is_valid():
                    serializer.save()
                    inserted_students.append(serializer.data)  # Track inserted records
                else:
                    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Construct response messages
        response_message = {
            "message": "Students imported successfully",
            "inserted": inserted_students,
            "duplicates": duplicate_students,
        }

        # Return a message that indicates success but also lists duplicates
        return Response(response_message, status=status.HTTP_201_CREATED)

class SessionListByStudentID(generics.ListAPIView):
    serializer_class = SessionSerializer

    def get_queryset(self):
        studentID = self.kwargs['studentID']
        sem = Semester.objects.first()
        
        # Filter sessions based on the foreign key's studentID
        return Session.objects.filter(parent_id=studentID semester_name=sem.semester_name, year=sem.year)
    
class StudentUpdateView(generics.UpdateAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentTypeSerializer
    
    def partial_update(self, request, *args, **kwargs):
        # Get the student instance
        student = self.get_object()
        
         # Perform the partial update
        serializer = self.get_serializer(student, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user  # Ensures the authenticated user is updated

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        # Validate serializer
        if serializer.is_valid():
            current_password = serializer.validated_data.get("current_password")
            new_password = serializer.validated_data.get("new_password")

            # Check if the current password is correct
            if not user.check_password(current_password):
                return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

            # Update the password
            user.set_password(new_password)
            user.save()
            return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SemesterUpsertView(APIView):
    def put(self, request, *args, **kwargs):
        # Check if a semester entry exists
        semester = Semester.objects.first()
        
        # If no semester exists, create a new one
        if not semester:
            serializer = SemesterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # If semester exists, update the existing record
        serializer = SemesterSerializer(semester, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            students = Student.objects.all()
            for student in students:
                if student.status == 'Alumnus':
                    student.time_left = 0
                elif student.status == 'Student':
                    student.time_left = 600
                student.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        # Get the first semester record
        semester = Semester.objects.first()
        if semester:
            # Mapping semester_name to a formatted string
            semester_name_mapping = {
                'firstsem': 'First Semester',
                'secondsem': 'Second Semester',
                'midyear': 'Midyear',
            }
            
            # Get the formatted semester name, default to original if not found
            formatted_semester_name = semester_name_mapping.get(semester.semester_name, semester.semester_name)
            
            # Prepare the response data
            data = {
                'year': semester.year,
                'semester_name': formatted_semester_name
            }
            return Response(data)
        else:
            return Response({'error': 'No semester found'}, status=404)
    
class SessionHoursView(APIView):
    def get(self, request):
        # Get the current semester and year
        current_semester = Semester.objects.first()
        if not current_semester:
            return Response({"error": "Semester data not found"}, status=404)

        # Aggregate the consumedTime by month and convert to hours
        session_data = (
            Session.objects
            .filter(year=current_semester.year, semester_name=current_semester.semester_name)
            .annotate(month=ExtractMonth('date'))
            .values('month')
            .annotate(total_minutes=Sum('consumedTime'))
            .order_by('month')
        )

        # Convert minutes to hours and prepare data for serialization
        data = [
            {"month": datetime(2023, item['month'], 1).strftime('%B'), "total_hours": item['total_minutes'] / 60}
            for item in session_data
        ]

        serializer = SessionHoursSerializer(data, many=True)
        return Response(serializer.data)
class PreviousSessionHoursView(APIView):
    def get(self, request):
        # Get the current semester and year
        year = request.query_params.get('year')
        semester_name = request.query_params.get('semester_name')

        if not year or not semester_name:
            return Response(
                {"error": "Both 'year' and 'semester_name' are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Aggregate the consumedTime by month and convert to hours
        session_data = (
            Session.objects
            .filter(year=year, semester_name=semester_name)
            .annotate(month=ExtractMonth('date'))
            .values('month')
            .annotate(total_minutes=Sum('consumedTime'))
            .order_by('month')
        )

        # Convert minutes to hours and prepare data for serialization
        data = [
            {"month": datetime(2023, item['month'], 1).strftime('%B'), "total_hours": item['total_minutes'] / 60}
            for item in session_data
        ]

        serializer = SessionHoursSerializer(data, many=True)
        return Response(serializer.data)


class PaymentIncomeView(APIView):
    def get(self, request):
        current_sem = Semester.objects.first()
        if not current_sem:
            return Response({"error": "Semester data not found"}, status=404)
        
        session_data = (
            Transaction.objects
            .filter(year=current_sem.year, semester_name=current_sem.semester_name)
            .annotate(month=ExtractMonth('timestamp'))
            .values('month')
            .annotate(total_income=Sum('amount'))
            .order_by('month')
        )
         # Convert minutes to hours and prepare data for serialization
        data = [
            {
             "month": datetime(2023, item['month'], 1).strftime('%B'), 
             "total_income": item['total_income'],
             }
            for item in session_data
        ]
        serializer = PaymentIncomeSerializer(data, many=True)
        return Response(serializer.data)
    

class PreviousPaymentIncomeView(APIView):
    def get(self, request):
        
        year = request.query_params.get('year')
        semester_name = request.query_params.get('semester_name')

        if not year or not semester_name:
            return Response(
                {"error": "Both 'year' and 'semester_name' are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session_data = (
            Transaction.objects
            .filter(year=year, semester_name=semester_name)
            .annotate(month=ExtractMonth('timestamp'))
            .values('month')
            .annotate(total_income=Sum('amount'))
            .order_by('month')
        )
         # Convert minutes to hours and prepare data for serialization
        data = [
            {
             "month": datetime(2023, item['month'], 1).strftime('%B'), 
             "total_income": item['total_income'],
             }
            for item in session_data
        ]
        serializer = PaymentIncomeSerializer(data, many=True)
        return Response(serializer.data)
    
class CountLoggedInView(APIView):
    def get(self, request):
        # Count the number of records where is_loggedin is True
        logged_in_count = Student.objects.filter(is_logged_in=True).count()

        # Send the count as a response
        return Response({"logged_in_count": logged_in_count}, status=status.HTTP_200_OK)
    
class ActiveUsersCountView(APIView):
    def get(self, request):
        # Get the current semester details
        current_semester = Semester.objects.first()
        
        if current_semester:
            current_year = current_semester.year
            current_semester_name = current_semester.semester_name
            
            # Filter sessions by the current year and semester, only where is_loggedin=True
            active_users_count = Session.objects.filter(
                year=current_year, 
                semester_name=current_semester_name,
            ).values('parent_id').distinct().count()
            
            return Response({"active_users_count": active_users_count}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No current semester found"}, status=status.HTTP_404_NOT_FOUND)
        
class CoursesCountView(APIView):
    def get(self, request):
        current_semester = Semester.objects.first()

        if not current_semester:
            return Response({"error": "Semester data not found"}, status=404)

        courses = Session.objects.filter(
            year=current_semester.year,
            semester_name=current_semester.semester_name
        ).values_list('course', flat=True).distinct()

        session_data = {}
        for course in courses:
            course_data = (
                Session.objects
                .filter(year=current_semester.year, semester_name=current_semester.semester_name, course=course)
                .annotate(month=ExtractMonth('date'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')
            )
            # Format course data by month
            session_data[course] = [
                {
                    "month": datetime(2023, item['month'], 1).strftime('%B'), 
                    "count": item['count']
                }
                for item in course_data
            ]

        return Response({"data": session_data})

class PreviousCoursesCountView(APIView):
    def get(self, request):
        year = request.query_params.get('year')
        semester_name = request.query_params.get('semester_name')

        if not year or not semester_name:
            return Response(
                {"error": "Both 'year' and 'semester_name' are required query parameters."},
                status=status.HTTP_400_BAD_REQUEST
            )

        courses = Session.objects.filter(
            year=year,
            semester_name=semester_name
        ).values_list('course', flat=True).distinct()

        session_data = {}
        for course in courses:
            course_data = (
                Session.objects
                .filter(year=year, semester_name=semester_name, course=course)
                .annotate(month=ExtractMonth('date'))
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')
            )
            # Format course data by month
            session_data[course] = [
                {
                    "month": datetime(2023, item['month'], 1).strftime('%B'), 
                    "count": item['count']
                }
                for item in course_data
            ]

        return Response({"data": session_data})
    

class ActivityLogView(APIView):
    def get(self, request, username):
        try:
            logs = ActivityLog.objects.filter(username=username).order_by('-timestamp')

            if not logs.exists():
                return Response({'message': 'No logs found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            serializer = ActivityLogSerializer(logs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching logs for {username}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class StaffLogsView(APIView):
    def get(self, request, username=None):
        logs = ActivityLog.objects.filter(user__username=username).order_by('-timestamp')
        serializer = ActivityLogSerializer(logs, many=True)
        return Response(serializer.data)




class StaffLoginView(generics.GenericAPIView):
    serializer_class = StaffLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        staff = serializer.validated_data['staff']
        
        # Log the login action
        StaffActivityLog.objects.create(staff=staff, action="Logged in")

        return Response({
            'status': 'success',
            'user_id': staff.id,
            'username': staff.username
        }, status=status.HTTP_200_OK)

    

@api_view(['POST'])
def log_activity(request):
    username = request.data.get('username')
    action = request.data.get('action')

    if not username or not action:
        return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Save the log entry to the database with current timestamp
        ActivityLog.objects.create(
            username=username, 
            action=action, 
            timestamp=timezone.now()  # Ensure correct timestamp assignment
        )
        return Response({"message": "Activity logged"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['POST'])
def reset_password(request, studentID):
    try:
        student = Student.objects.get(id=studentID)
        
        # Check if the password is already the default
        if student.is_default_password():
            logger.info(f"Password reset attempted for {studentID}, but password is already default.")
            ActivityLog.objects.create(username=student.username, action="Attempted password reset (already default)", timestamp=timezone.now())
            return Response({"message": "Current password is already the default."}, status=400)
        
        # Reset password logic
        student.reset_password()  # Assuming this method exists
        logger.info(f"Password reset successful for {studentID}")
        
        # Log the activity
        try:
            ActivityLog.objects.create(username=student.username, action="Password reset", timestamp=timezone.now())
        except Exception as e:
            logger.error(f"Failed to log activity for {student.username}: {e}")

        return Response({"message": "Password reset successful"}, status=200)
    except Student.DoesNotExist:
        return Response({"error": "Student not found"}, status=404)


def log_staff_activity(staff, action):
    StaffActivityLog.objects.create(
        staff=staff, 
        action=action, 
        timestamp=timezone.now()  # Explicitly pass the current timestamp
    )

def export_to_excel(request):
    current_sem = Semester.objects.first()
    records = Session.objects.filter(
        semester_name=current_sem.semester_name, 
        year=current_sem.year
    )
    transactions = Transaction.objects.filter(
        semester_name=current_sem.semester_name, 
        year=current_sem.year
    )
    

    if not records.exists():
        return HttpResponse("No data to export.", status=404)
    

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = 'Sessions'

    # Headers
    headers = ['Date', 'StudentID', 'Course','Login Time', 'Logout Time', 'Time Consumed (minutes)', 'Semester', 'School Year']
    sheet.append(headers)

    # Add data rows
    for record in records:
        sheet.append([record.date, record.parent_id, record.course, record.loginTime, record.logoutTime, record.consumedTime, record.semester_name, record.year])

    transaction_sheet = workbook.create_sheet(title='Transactions')
    transaction_header = ['Reference Number', 'Date and Time', 'Payment(PHP)', 'Semester', 'School Year']
    transaction_sheet.append(transaction_header)

    for t in transactions:
        transaction_sheet.append([t.reference_number, t.timestamp, t.amount, t.semester_name, t.year])

    # Prepare response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    filename = f"{current_sem.semester_name}_{current_sem.year}_records.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Save workbook to response
    workbook.save(response)
    return response