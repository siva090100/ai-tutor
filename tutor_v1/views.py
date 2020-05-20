from django.shortcuts import render
from django.contrib.auth.models import User
import pandas as pd
from django import forms
from django.http import HttpResponse
from django.shortcuts import render
from .forms import UploadQuestions
from .models import Skill,AnswerText,AnswerChoice,Problem, Probability, Student, DiagnosticResult, Irt, SkillStats, StudentResponse
import string
import subprocess
import os
import numpy as np
import random
from catsim.initialization import RandomInitializer
from catsim.selection import MaxInfoSelector
from catsim.estimation import DifferentialEvolutionEstimator

# Create your views here.



def insert_questions(questions_file, mapping_file):
	qf = pd.read_csv(questions_file)
	mf = pd.read_csv(mapping_file)
	existing_skills = Skill.objects.all()
	if not existing_skills:
		for id,row in mf.iterrows():
			new_skill = Skill(skill_name = row['skill'],skill_desc = row['skill_description'])
			new_skill.save()
	else:
		existing_skills_list = [skill.skill_name for skill in existing_skills]
		for id,row in mf.iterrows():
			if row['skill'] not in existing_skills_list:
				new_skill = Skill(skill_name = row['skill'],skill_desc = row['skill_description'])
				new_skill.save()

	if 'problem_name' not in qf.columns:
		qf['problem_name'] = ''
	qf.dropna(subset=qf.columns,inplace=True)
	for id,row in qf.iterrows():
		question = None
		choice_begins = list(string.ascii_lowercase)
		list1 = []
		list2 = []
		for char in choice_begins:
			list1.append(char+')')
			list2.append(char+'.')
		choice_begins = list1+list2
		print(row['skill'])
		skill = Skill.objects.get(skill_name = row['skill'])
		answer_type = row['answer_type']
		if answer_type == 'Choice':
			choices = row['answers_list']
			choices = choices.split('\n')
			cleansed_choices = []
			for choice in choices:
				if choice != '':
					if choice[0:2] in choice_begins:
						choice = choice[2:]
					cleansed_choices.append(choice)

			correct_choices = row['correct_answer']
			correct_choices  = correct_choices.split('\n')
			new_correct_choices = []
			for choice in correct_choices:
				new_correct_choices.append(ord(choice)-97)
			new_choice = AnswerChoice(choices = cleansed_choices,correct_choices =new_correct_choices)
			new_choice.save()
			question  = Problem(answer_object = new_choice,problem_name = row['problem_name'],problem_text =row['questions'],skill_id = skill,diagnostic_test = row['diagnostic'])

		elif answer_type == 'Text' or answer_type == 'text':
			answer = row['answers_list']
			answer = answer.strip()
			answer = answer.tolower()
			answer_obj = AnswerText(correct_answer = answer)
			answer_obj.save()
			question = Problem(answer_object = answer, problem_name = row['problem_name'],problem_text = row['questions'], skill_id = skill,diagnostic_test = row['diagnostic'])
		question.save()


def upload_questions(request):
	form = None
	if request.method == 'POST':
		form = UploadQuestions(request.POST, request.FILES)

		if form.is_valid():
			insert_questions(request.FILES['question_file'],request.FILES['mapping_file'])
			return HttpResponse("File Uploaded Successfully")

		else:
			form = UploadQuestions()
	return render(request, 'upload_questions.html', {'form': form})


def compute_knowledge_graph(data_dict,update = False):

	current_user = Student.objects.get(pk = 1)
	evaluation = {}
	
	score = 0
	if update:
		file = open("tutor_v1/datasets/hmmdata.txt","a+")
	else:
		file = open("tutor_v1/datasets/hmmdata.txt","w+")
	for key,value in data_dict.items():
		correct_or_wrong = 2
		hmm_data = []
		question = Problem.objects.get(pk = key)
		value_array = []
		for v in value:
			value_array.append(int(v)-1)
		if question.answer_type.name == 'answer choice':
			#print("Trigger 1")
			correct_answer = question.answer_object.correct_choices
			print("Correct Answer",correct_answer)
			print("Value Array",value_array)
			if value_array == correct_answer:
				#print("Trigger 2")
				correct_or_wrong = 1
				score = score + 1

		elif question.answer_type.name == 'answer text':
			correct_answer = question.answer_object.correct_answer
			if correct_answer == value:
				correct_or_wrong = 1
				score = score+1
		evaluation[key] = correct_or_wrong
		hmm_data.append(str(correct_or_wrong))
		hmm_data.append(current_user.user.username)
		hmm_data.append(str(question.id))
		hmm_data.append(question.skill_id.skill_name.replace(' ','-'))
		hmm_data.append('\n')
		data_string = '\t'.join(hmm_data)
		file.write(data_string)

	result = DiagnosticResult(student_id = current_user, score = score)
	result.save()
	file.close()
	os.system("hmm-scalable/./trainhmm tutor_v1/datasets/hmmdata.txt tutor_v1/datasets/knowledgegraph.txt")
	file = open("tutor_v1/datasets/knowledgegraph.txt","r")
	data_array = file.readlines()
	data_array = data_array[7:]
	final_data_array = []
	probability_dict = {}
	if '' in data_array:
		data_array.remove('')
	for i in range(0,len(data_array),4):
		final_data_array.append(data_array[i:i+4])
	print(final_data_array)
	for item in final_data_array:
		skill = str(item[0].split('\t')[1])
		prior_probability = float(item[1].split('\t')[1])
		transition_probability = float(item[2].split('\t')[3])
		slip = float(item[3].split('\t')[1])
		guess = float(item[3].split('\t')[2])
		probability_dict[skill] = {'prior_probability':prior_probability,'transition_probability':transition_probability,
		 'slip':slip,'guess':guess}

	if Probability.objects.all() is not None:
		Probability.objects.all().delete()
	for key,value in probability_dict.items():
		print(key)
		skill_obj = Skill.objects.get(skill_name = key.strip())
		if probability_dict[key]['transition_probability'] > 0.95:
			probability_dict[key]['completed'] = 1
		else:
			probability_dict[key]['completed'] = 0
		prob_obj = Probability(skill_id = skill_obj, student_id = current_user,prior_probability = probability_dict[key]['prior_probability'],
			transition_probability = probability_dict[key]['transition_probability'], slip_probability = probability_dict[key]['slip'],
			guess_probability = probability_dict[key]['guess'],completed = probability_dict[key]['completed'])
		prob_obj.save()

	return evaluation



def create_diagnostic_test(request):

	if request.method == 'POST':
		data_dict = dict(request.POST)
		print(data_dict)
		if 'csrfmiddlewaretoken' in data_dict:
			del data_dict['csrfmiddlewaretoken']

		compute_knowledge_graph(data_dict)
		return HttpResponse("Knowledge graph updated Successfully")

	else:
		diagnostic_test = Problem.objects.filter(diagnostic_test=1)
		return render(request,'diagnostic_test.html',{'Questions': diagnostic_test})



def update_hmm(data_dict,eval = False):

	for key,value in data_dict.items():
		question_id = key
	
	evaluation = compute_knowledge_graph(data_dict,update=True)
	prob_obj = Probability.objects.filter(completed = 0)
	current_skill = Problem.objects.get(id = question_id).skill_id
	questions = Problem.objects.filter(skill_id = current_skill.id)
	test_file = open('tutor_v1/datasets/hmmtest.txt','w+')
	current_user = Student.objects.get(pk = 1)
	for question in questions:
		write_array = []
		write_array.append('.')
		write_array.append(current_user.user.username)
		write_array.append(str(question.id))
		write_array.append(question.skill_id.skill_name)
		data_string = '\t'.join(write_array)
		test_file.write(data_string)
		test_file.write('\n')
	test_file.close()
	os.system("hmm-scalable/./predicthmm -p 1 tutor_v1/datasets/hmmtest.txt tutor_v1/datasets/knowledgegraph.txt tutor_v1/datasets/predictions.txt")
	pred_file = open("tutor_v1/datasets/predictions.txt","r")
	diff_array = []
	for line in pred_file.readlines():
		diff = line.split('\t')
		diff_array.append(float(diff[0]))

	min_index = np.argmax(np.array(diff_array))
	pred_file.close()
	test_file = open('tutor_v1/datasets/hmmtest.txt')
	test_array = test_file.readlines()
	next_question = test_array[min_index].split('\t')[2]
	if eval:
		return evaluation




def random_irt(request):

	questions = Problem.objects.all()
	for question in questions:
		discrimination = random.uniform(0.8,2.5)
		difficulty = random.randint(-4,4)
		pseudo_guess  =random.uniform(0.1,0.3)
		asymptote = random.uniform(0.9,1)
		irt = Irt(question = question,discrimination = discrimination, difficulty = difficulty, pseudo_guess = pseudo_guess, asymptote = asymptote )
		irt.save()

	return HttpResponse("Initialized questions with random IRT parameters Successfully")



def random_theta(request):
	skills = Skill.objects.all()
	student = Student.objects.get(pk=1)
	for skill in skills:
		theta = RandomInitializer().initialize()
		obj = SkillStats(student = student, skill = skill, theta = theta)
		obj.save()
	return HttpResponse("Initialized theta randomly for all the skills")


def render_homepage(request):
	skills = Skill.objects.all()
	return render(request,'homepage.html',{'skills':skills})


def initialize_skill(request,id):
	current_user = Student.objects.get(pk = 1)
	if request.method == 'GET':
		skill_id = id
		skill = Skill.objects.get(id = skill_id)
		random_theta = random.uniform(-4,-4)
		SkillStats.objects.filter(skill = skill).update(theta = random_theta)
		theta = SkillStats.objects.get(skill = skill).theta
		problems = Problem.objects.filter(skill_id = skill)
		irt_params = []
		index_problem = {}
		for id,problem in enumerate(problems):
			param = []
			index_problem[id] = problem.id
			irt = Irt.objects.get(question = problem)
			param.append(irt.discrimination)
			param.append(irt.difficulty)
			param.append(irt.pseudo_guess)
			param.append(irt.asymptote)
			irt_params.append(param)

		irt_params = np.array(irt_params)
		selector = MaxInfoSelector().select(items= irt_params,administered_items=[],est_theta= theta)
		print(selector)
		next_question = Problem.objects.get(id = index_problem[selector])
		print(next_question)
		response_dict = {'question':next_question}
		return render(request,'problem.html',response_dict)

	elif request.method == 'POST':
		data_dict = dict(request.POST)
		print("Data dict is",data_dict)
		if 'csrfmiddlewaretoken' in data_dict:
			del data_dict['csrfmiddlewaretoken']
		evaluation = update_hmm(data_dict,eval = True)
		print(evaluation)
		question_id = None
		for key,value in evaluation.items():
			question_id = key
			if value == 2:
				evaluation[key] = 0


		problem  = Problem.objects.get(id = question_id)
		skill = problem.skill_id
		answer_sequence = []
		new_response = StudentResponse(student = current_user, problem = problem, correct_or_wrong = evaluation[question_id],skill = skill)
		new_response.save()
		responses = StudentResponse.objects.filter(student = current_user,skill = skill)
		administered_items = {response.problem.id:response.correct_or_wrong for response in responses }
		print("Administered Items:",administered_items)
		irt_params = []
		estimator_params = []
		current_theta = SkillStats.objects.get(skill = skill).theta

		all_problems = Problem.objects.filter(skill_id = skill)
		index_problem = {}
		index_list = []
		for id,problem in enumerate(all_problems):
			irt_param = []
			estimator_param = []
			index_problem[id] = problem.id
			irt = Irt.objects.get(question = problem)
			irt_param.append(irt.discrimination)
			irt_param.append(irt.difficulty)
			irt_param.append(irt.pseudo_guess)
			irt_param.append(irt.asymptote)
			irt_params.append(irt_param)
			if problem.id in administered_items:
				index_list.append(id)
				estimator_param.append(irt.discrimination)
				estimator_param.append(irt.difficulty)
				estimator_param.append(irt.pseudo_guess)
				estimator_param.append(irt.asymptote)
				answer_sequence.append(int(administered_items[problem.id]))
				estimator_params.append(estimator_param)


		
		irt_params = np.array(irt_params)
		estimator_params = np.array(estimator_params)
		estimator = DifferentialEvolutionEstimator(bounds = (-4,4))
		print(answer_sequence)
		print(estimator_params)
		print(current_theta)
		new_theta = estimator.estimate(response_vector = answer_sequence, administered_items = estimator_params, current_theta = current_theta)
		print("New Theta",new_theta)
		selector = MaxInfoSelector().select(items= irt_params,administered_items=index_list,est_theta= new_theta)
		print(selector)
		next_question = Problem.objects.get(id = index_problem[selector])
		print(next_question)
		response_dict = {'question':next_question,'theta':new_theta}
		SkillStats.objects.filter(skill = skill).update(theta = new_theta)
		pred_file = open("tutor_v1/datasets/predictions.txt","r")
		diff_array = []
		for line in pred_file.readlines():
			diff = line.split('\t')
			diff_array.append(float(diff[0]))

		mastery = max(diff_array)

		response_dict['mastery'] = str(mastery*100)+'%'
		return render(request,'problem.html',response_dict)



