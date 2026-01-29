from django.contrib import admin
from .models import (
    Question, AnswerKey, TestKey, CustomUser, Teacher, Student, Result,
    Choice, QuestionImage, Subject, Topic, DifficultyLevel, BoardExam, PracticeResult
)

# -------------------------
# Inline for Choices
# -------------------------
class ChoiceInline(admin.TabularInline):  # or StackedInline for vertical layout
    model = Choice
    extra = 0  # No extra empty fields
    can_delete = True

# -------------------------
# Question Admin
# -------------------------
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'question_text', 'difficulty', 'get_subjects', 'topic', 'get_board_exams')
    inlines = [ChoiceInline]  # Group choices per question
    search_fields = ('question_text',)
    list_filter = ('difficulty', 'subjects', 'topic', 'board_exams')  # updated ManyToMany fields

    # Methods to show ManyToMany fields in list_display
    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    get_subjects.short_description = "Subjects"

    def get_board_exams(self, obj):
        return ", ".join([b.name for b in obj.board_exams.all()])
    get_board_exams.short_description = "Board Exams"


# -------------------------
# Register other models
# -------------------------
admin.site.register(CustomUser)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(QuestionImage)
admin.site.register(Topic)
admin.site.register(Subject)
admin.site.register(DifficultyLevel)
admin.site.register(Result)
admin.site.register(AnswerKey)
admin.site.register(TestKey)
admin.site.register(BoardExam)
admin.site.register(PracticeResult)
