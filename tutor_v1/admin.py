from django.contrib import admin
from django.apps import apps
from .models import Student,Teacher,Problem,Skill,AnswerChoice,AnswerText,Code,ProblemStats,DiagnosticResult,StudentResponse,DiagnosticTestResponse,StudentResult,Probability,Irt,SkillStats

admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Problem)
admin.site.register(Skill)
admin.site.register(AnswerChoice)
admin.site.register(AnswerText)
admin.site.register(Code)
admin.site.register(ProblemStats)
admin.site.register(DiagnosticResult)
admin.site.register(StudentResponse)
admin.site.register(DiagnosticTestResponse)
admin.site.register(StudentResult)
admin.site.register(Probability)
admin.site.register(Irt)
admin.site.register(SkillStats)


# Register your models here.
