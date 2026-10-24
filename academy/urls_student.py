from django.urls import path
from . import views_student as views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),

    # Leave & Holiday Notices from assigned Trainer
    path('notices/', views.notices_list, name='notices'),

    # Direct Individual Messages from Trainer (PDFs, materials, links)
    path('messages/', views.messages_list, name='messages'),

    # Course Learning Resources Tab (filtered by student course)
    path('resources/', views.resources_list, name='resources'),

    # Student Leave Application & History
    path('leave/apply/', views.leave_apply, name='leave_apply'),
]
