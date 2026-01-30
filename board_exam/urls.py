from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import Add_Question, signup
from . import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
# Register any viewsets with router here if needed
# Example: router.register(r'questions', QuestionViewSet)

urlpatterns = [
    # Root goes to home
    path('', views.home, name='home'),

    # Authentication / user
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Student / teacher home
    path('home/', views.home, name='home'),
    path('home_student/', views.home_student, name='home_student'),

    # Question / test management
    path('add_question/', Add_Question.as_view(), name='add_question'),
    path('question-bank/', views.question_bank, name='question_bank'),
    path('generate-test/', views.generate_test, name='generate_test'),
    path('download-test-pdf/', views.download_test_pdf, name='download_test_pdf'),
    path('upload-file/', views.upload_file, name='upload_file'),
    path('upload_answer/', views.upload_answer, name='upload_answer'),
    path('download_answer_key/', views.download_answer_key, name='download_answer_key'),
    path('download_exam_results/', views.download_exam_results, name='download_exam_results'),

    # Exams / forms / results
    path('exam_form/<str:set_id>/', views.exam_form, name='exam_form'),
    path('result/<int:result_id>/', views.result_page, name='result_page'),
    path('warning/', views.warning_page, name='warning_page'),

    # APIs / AJAX endpoints
    path('get_exam_id_suggestions', views.get_exam_id_suggestions, name='get_exam_id_suggestions'),
    path('get_subjects/', views.get_subjects, name='get_subjects'),
    path('get_testkeys_by_subject/', views.get_testkeys_by_subject, name='get_testkeys_by_subject'),
    path('get_board_exams/', views.get_board_exams, name='get_board_exams'),
    path('get_subjects_by_board_exam/', views.get_subjects_by_board_exam, name='get_subjects_by_board_exam'),
    path('get_topics_by_subject/', views.get_topics_by_subject, name='get_topics_by_subject'),
    path('get_testkeys_by_topic/', views.get_testkeys_by_topic, name='get_testkeys_by_topic'),
    path('get_exam_dates_by_board_exam/', views.get_exam_dates_by_board_exam, name='get_exam_dates_by_board_exam'),
    path('get_get_subjects_by_board_exam_and_date/', views.get_subjects_by_board_exam_and_date, name='get_subjects_by_board_exam_and_date'),

    # Practice exams
    path('practice/start/', views.practice_start, name='practice_start'),
    path('practice/take/<uuid:session_id>/', views.practice_take, name='practice_take'),
    path('practice/submit/<uuid:session_id>/', views.practice_submit, name='practice_submit'),
    path('practice/result/<uuid:session_id>/', views.practice_result_page, name='practice_result_page'),

    # Answer sheets / online tests
    path('answer_sheet/', views.answer_sheet_view, name='answer_sheet'),
    path('online-answer-test/', views.online_answer_test, name='online_answer_test'),
    path('answer_online_exam/', views.answer_online_exam, name='answer_online_exam'),
    path('answer-test-preview/<subject>/<board_exam>/<set_a_id>/<set_b_id>/', views.answer_test_preview, name='answer_test_preview'),

    # Analytics
    path('qanalytics/', views.question_analytics, name='question_analytics'),
    path('tanalytics/', views.test_analytics, name='test_analytics'),
    path('analytics/', views.analytics_dashboard, name='analytics_dashboard'),

    # Downloads
    path('download-answer/', views.download_answer_page, name='download_answer_page'),
    path('download_exam_results_page/', views.download_exam_results_page, name='download_exam_results_page'),
    path('download_test_interface/', views.download_test_interface, name='download_test_interface'),
    path('download_existing_test_pdf/', views.download_existing_test_pdf, name='download_existing_test_pdf'),

    # DRF API root moved to /api/
    path('api/', include(router.urls)),
]

# Serve static files
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
