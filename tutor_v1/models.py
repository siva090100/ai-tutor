from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import fields
from django.db.models import IntegerField
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey

# Create your models here.

DIAGNOSTIC = 'diagnostic_test'
PRACTICE = 'practice'
TEST = 'custom_test'
EASY = 'easy'
MEDIUM = 'medium'
HARD = 'hard'
VERY_HARD = 'very_hard'
BRAIN_TWISTER = 'brain_twister'
CHOICE = 'multiple_choice'
TEXT = 'text_blank'
CODE = 'code'

ANSWER_TYPE = [
(CHOICE,'mcq'),
(TEXT,'text'),
(CODE,'code'),
]


DIFFICULTY_CHOICES = [

(EASY,'easy'),
(MEDIUM,'medium'),
(HARD,'hard'),
(VERY_HARD,'very_hard'),
(BRAIN_TWISTER,'brain_twister'),

]

PROBLEM_SUBTYPE = (
	
	(DIAGNOSTIC,'Diagnostic Test'),
	(PRACTICE,'practice'),
	(TEST,'custom_test'),

		)
class Student(models.Model):
	user = models.OneToOneField(User, on_delete = models.CASCADE)
	institution_name = models.CharField(max_length = 40)


class Teacher(models.Model):
	user = models.OneToOneField(User,on_delete = models.CASCADE)
	institution_name = models.CharField(max_length = 40)
	students = models.ManyToManyField(Student, verbose_name = 'list of students')


class Skill(models.Model):
	skill_name = models.CharField(max_length = 30)
	skill_desc = models.CharField(max_length = 100)
	skill_order = models.IntegerField(null = True)


class Problem(models.Model):

	answer_type = models.ForeignKey(ContentType,on_delete = 'CASCADE')
	answer_id = models.PositiveIntegerField()
	answer_object = GenericForeignKey('answer_type','answer_id')
	problem_name = models.CharField(max_length = 15,null = True,blank = True)
	problem_text = models.CharField(max_length = 1000)
	skill_id = models.ForeignKey(Skill,on_delete = models.CASCADE)
	pub_date = models.DateTimeField('date published',auto_now_add = True)
	difficulty_level = models.CharField(max_length=10,choices = DIFFICULTY_CHOICES, default = EASY,)
	question_score = models.IntegerField(default=1)
	diagnostic_test = models.BooleanField(default=1)

class AnswerChoice(models.Model):
	question = fields.GenericRelation(Problem)
	choices = ArrayField(ArrayField(models.CharField(max_length=100)))
	correct_choices = ArrayField(ArrayField(models.IntegerField()))


class AnswerText(models.Model):
	question = fields.GenericRelation(Problem)
	correct_answer = models.CharField(max_length=100)



class Code(models.Model):
	question = fields.GenericRelation(Problem)
	code = models.CharField(max_length = 100)


class ProblemStats(models.Model):

	time_spent = models.DateTimeField()
	student_id = models.ForeignKey(Student,on_delete = models.CASCADE)
	attempts = models.IntegerField()
	problem_id = models.ForeignKey(Problem, on_delete = models.CASCADE)



class DiagnosticResult(models.Model):
	student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
	score = models.IntegerField()


class StudentResponse(models.Model):
	student = models.ForeignKey(Student,on_delete = models.CASCADE)
	problem = models.ForeignKey(Problem,on_delete = models.CASCADE)
	skill = models.ForeignKey(Skill,on_delete = models.CASCADE)
	correct_or_wrong = models.BooleanField()
	time_taken = models.DateTimeField(auto_now_add = True)


class DiagnosticTestResponse(models.Model):
	student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
	problem_id = models.ForeignKey(Problem,on_delete = models.CASCADE)
	answer = models.CharField(max_length = 100)
	correct_or_wrong = models.BooleanField()


class StudentResult(models.Model):
	student_id = models.ForeignKey(Student,on_delete = models.CASCADE)
	total_score = models.IntegerField()


class Probability(models.Model):
	student_id = models.ForeignKey(Student, on_delete = models.CASCADE)
	prior_probability = models.FloatField()
	slip_probability = models.FloatField()
	guess_probability = models.FloatField()
	transition_probability = models.FloatField()
	skill_id = models.ForeignKey(Skill, on_delete = models.CASCADE)
	completed = models.BooleanField(default = False)

class Irt(models.Model):
	question = models.ForeignKey(Problem, on_delete = models.CASCADE)
	discrimination = models.FloatField()
	difficulty = models.FloatField()
	pseudo_guess = models.FloatField()
	asymptote = models.FloatField()

class SkillStats(models.Model):
	student = models.ForeignKey(Student, on_delete = models.CASCADE)
	skill  = models.ForeignKey(Skill, on_delete = models.CASCADE)
	theta = models.FloatField()


