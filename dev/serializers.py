from rest_framework import serializers
from .models import User, Session, Student, Course, Lecturer, Paper, TeamLeader, Specialization, Module, CatCombination, LecturerModule, Result, AdmissionNumber, ModuleScore
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'sex',
            'role',
            'username',
            'password',
            'is_staff',
        ]
        extra_kwargs = {'password': {'write_only': True}}

class SessionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Session
    fields = ['id', 'period', 'mode']

class StudentSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  class Meta:
    model = Student
    fields = [ 'index', 'user', 'centre', 'session']

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
class StudentViewSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  session = SessionSerializer()
  class Meta:
    model = Student
    fields = [ 'index', 'user', 'centre', 'session']

class CourseSerializer(serializers.ModelSerializer):
  class Meta:
    model = Course
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()

class LecturerSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  department = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
  class Meta:
    model = Lecturer
    fields = '__all__'

  def create(self, validated_data):
    user = validated_data.get('user')
    department = validated_data.get('department')
    lec_role = validated_data.get('role')
    full_name = user.get('full_name').strip().capitalize()
    role = 'lecturer'
    is_staff = False
    password = make_password(full_name)
    user_instance = User.objects.create(full_name=full_name,  role=role, is_staff=is_staff, password=password)
    lecturer = Lecturer.objects.create(user=user_instance, role=lec_role, department=department)
    return lecturer

class PaperSerializer(serializers.ModelSerializer):
  course = CourseSerializer()
  class Meta:
    model = Paper
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()

class TeamLeaderSerializer(serializers.ModelSerializer):
  class Meta:
    model = TeamLeader
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.score = validated_data.get('score', instance.score)
    instance.save()
    return instance

class SpecializationSerializer(serializers.ModelSerializer):
  student = StudentSerializer()
  class Meta:
    model = Specialization
    fields = '__all__'

  def create(self, validated_data):
    try:
      student = validated_data.get('student')
      user = student.get('user')
      course = validated_data.get('course')
      session = student.get('session')
      year = student.get('year')
      admission = student.get('index')
      surname = user.get('surname').strip().capitalize()
      other_names = user.get('other_names').strip().capitalize()
      username = admission
      is_staff = False
      role = 'student'
      password = make_password(admission)
      user_instance = User.objects.create(full_name=surname, other_names=other_names, username=username, is_staff=is_staff, role=role, password=password)
      student_instance = Student.objects.create(index=admission, user=user_instance, session=session, year=year)
      specialization = Specialization.objects.create(student=student_instance, course=course)
      return specialization
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.course = validated_data.get('course', instance.course)
    instance.save()
    return instance

class ModuleSerializer(serializers.ModelSerializer):
  class Meta:
    model = Module
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()

class CatCombinationSerializer(serializers.ModelSerializer):
  class Meta:
    model = CatCombination
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.paper = validated_data.get('paper', instance.paper)
    instance.save()
    return instance

class LecturerModuleSerializer(serializers.ModelSerializer):
  class Meta:
    model = LecturerModule
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()

class ResultCreateSerializer(serializers.ModelSerializer):
  student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
  paper = serializers.PrimaryKeyRelatedField(queryset=Paper.objects.all())
  class Meta:
    model = Result
    fields = ['student', 'paper', 'cat1', 'cat2']

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.cat1 = validated_data.get('cat1', instance.cat1)
    instance.cat2 = validated_data.get('cat2', instance.cat2)
    instance.save()
    return instance
  
class ResultSerializer(serializers.ModelSerializer):
  student = StudentViewSerializer()
  paper = PaperSerializer()
  class Meta:
    model = Result
    fields = ['student', 'paper', 'cat1', 'cat2']

class KnecIndexNumberSerializer(serializers.ModelSerializer):
  student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
  class Meta:
    model = AdmissionNumber
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.index = validated_data.get('index', instance.index)
    instance.save()
    return instance

class ModuleScoreSerializer(serializers.ModelSerializer):
  class Meta:
    model = ModuleScore
    fields = ['student', 'module', 'score']

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
  
  def update(self, instance, validated_data):
    instance.score = validated_data.get('score', instance.score)
    instance.save()
    return instance
