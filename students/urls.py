from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentViewSet, TransactionCreateView, TransactionListView, ResetPasswordView, UserLoginView, LogoutView, student_login_view, student_logout_view, student_change_password_view, check_history_view, export_to_excel, StaffCreateView, StaffListView, UpdateStaffStatusView, ImportStudentView, SessionListByStudentID, StaffLogsView, log_activity, ActivityLogView, StudentUpdateView, ChangePasswordView, SemesterUpsertView, SessionHoursView, CountLoggedInView, ActiveUsersCountView, PaymentIncomeView, CoursesCountView, PreviousCoursesCountView, PreviousSessionHoursView, PreviousPaymentIncomeView

router = DefaultRouter()
router.register(r'students', StudentViewSet, basename='student')

urlpatterns = [
    path('', include(router.urls)),
    path('login-admin/', UserLoginView.as_view(), name='login-admin'),
    path('login-student/', student_login_view, name='login-student'),
    path('logout-student/', student_logout_view, name='logout-student'),
    path('change-password-student/', student_change_password_view, name='change-password-student'),
    path('check-history-student/', check_history_view, name='check-history-student'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('transactions/create/', TransactionCreateView.as_view(), name='transaction-create'),
    path('students/<str:studentID>/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('create-user/', StaffCreateView.as_view(), name='create_user'),
    path('staffview/', StaffListView.as_view(), name='staff-list'),
    path('update-status/<str:username>/', UpdateStaffStatusView.as_view(), name='update-status'),
    path('import-student/', ImportStudentView.as_view(), name='import-student'),
    path('sessions/<str:studentID>/', SessionListByStudentID.as_view(), name='sessions_by_student'),
    path('students/<str:studentID>/', StudentUpdateView.as_view(), name='student-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('semesters/', SemesterUpsertView.as_view(), name='semester-create'),
    path('session-hours/', SessionHoursView.as_view(), name='session-hours'),
    path('count_loggedin/', CountLoggedInView.as_view(), name='count_loggedin'),
    path('active_users/', ActiveUsersCountView.as_view(), name='active_users_count'), 
    path('transaction-income/', PaymentIncomeView.as_view(), name='transaction-income'), 
    path('courses-count/', CoursesCountView.as_view(), name='courses-count'), 
    path('previous-count/', PreviousCoursesCountView.as_view(), name='previous-count'),
    path('logs/<str:username>/', ActivityLogView.as_view(), name='activity_logs'),
    path('activity-logs/', log_activity, name='log_activity'),
    path('previous-session/', PreviousSessionHoursView.as_view(), name='previous-session'),
    path('previous-income/', PreviousPaymentIncomeView.as_view(), name='previous-income'),
    path('export/', export_to_excel, name='export-to-excel'),

    
]
