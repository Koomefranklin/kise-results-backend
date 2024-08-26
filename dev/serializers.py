from rest_framework import serializers
from .models import User, Mode, Student, Course, Lecturer, Paper, TeamLeader, Module, CatCombination, Result, IndexNumber, ModuleScore, SittingCat, Centre
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

class ModeSerializer(serializers.ModelSerializer):
  class Meta:
    model = Mode
    fields = ['id', 'mode']

class CentreSerializer(serializers.ModelSerializer):
  class Meta:
    model = Centre
    fields = ['name', 'id']

class CourseSerializer(serializers.ModelSerializer):
  class Meta:
    model = Course
    fields = '__all__'

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()

class StudentSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  class Meta:
    model = Student
    fields = ['id', 'admission', 'user', 'centre', 'mode', 'course', 'year', 'added_by', 'updated_by']

  def create(self, validated_data):
    try:
      student = validated_data
      added_by= self.context['request'].user
      user = student.get('user')
      course = student.get('course')
      mode = student.get('mode')
      year = student.get('year')
      admission = student.get('admission')
      full_name = user.get('full_name').strip().capitalize()
      centre = student.get('centre')
      username = user.get('username')
      is_staff = False
      role = 'student'
      password = make_password(admission)
      user_instance = User.objects.create(full_name=full_name, username=username, is_staff=is_staff, role=role, password=password)
      student_instance = Student.objects.create(admission=admission, user=user_instance, centre=centre, mode=mode, year=year, course=course, added_by=added_by)
      return student_instance
    except IntegrityError:
      raise serializers.ValidationError()
    except Exception as e:
      print(e)
    
  def update(self, instance, validated_data):
    instance.updated_by = self.context['request'].user
    instance.save()
    return instance
    
class StudentViewSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  mode = ModeSerializer()
  centre = CentreSerializer()
  course = CourseSerializer()
  class Meta:
    model = Student
    fields = ['id', 'admission', 'user', 'centre', 'mode', 'course', 'year']

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
    lecturer = Lecturer.objects.create(user=user_instance, role=lec_role, courses=department)
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
      instance = super().create(validated_data)
      instance.added_by = self.context['request'].user
      return instance
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.paper = validated_data.get('paper', instance.paper)
    instance.save()
    return instance

class KnecIndexNumberSerializer(serializers.ModelSerializer):
  class Meta:
    model = IndexNumber
    fields = ['id', 'student', 'index']
    

  def create(self, validated_data):
    try:
      return super().create(validated_data)
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.index = validated_data.get('index', instance.index)
    instance.save()
    return instance

class ResultCreateSerializer(serializers.ModelSerializer):
  student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
  paper = serializers.PrimaryKeyRelatedField(queryset=Paper.objects.all())
  class Meta:
    model = Result
    fields = ['student', 'paper', 'cat1', 'cat2', 'added_by', 'update_by', 'created_at', 'updated_at']

  def create(self, validated_data):
    try:
      instance = super().create(validated_data)
      instance.added_by = self.context['request'].user
      return instance
    except IntegrityError:
      raise serializers.ValidationError()
    
  def update(self, instance, validated_data):
    instance.cat1 = validated_data.get('cat1', instance.cat1)
    instance.cat2 = validated_data.get('cat2', instance.cat2)
    instance.save()
    return instance
  
class ResultViewSerializer(serializers.ModelSerializer):
  paper = PaperSerializer()
  class Meta:
    model = Result
    fields = ['paper', 'cat1', 'cat2', 'added_by', 'update_by', 'created_at', 'updated_at']
  
class StudentResultSerializer(serializers.ModelSerializer):
  student_results = ResultViewSerializer(many=True, read_only=True)
  student_index = KnecIndexNumberSerializer(many=True, read_only=True)
  user = UserSerializer()
  class Meta:
    model = Student
    fields = ['id', 'admission', 'user', 'centre', 'mode', 'student_results', 'student_index']

class ModuleScoreSerializer(serializers.ModelSerializer):
  class Meta:
    model = ModuleScore
    fields = ['id', 'student', 'module', 'discussion', 'take_away', 'added_by', 'updated_by', 'created_at', 'updated_at']

  def create(self, validated_data):
    try:
      instance = super().create(validated_data)
      instance.added_by = self.context['request'].user
      return instance
    except IntegrityError:
      raise serializers.ValidationError()
  
  def update(self, instance, validated_data):
    instance.discussion = validated_data.get('discussion', instance.discussion)
    instance.take_away = validated_data.get('take_away', instance.take_away)
    instance.save()
    return instance
  
class SittingCatSerializer(serializers.ModelSerializer):
  class Meta:
    model = SittingCat
    fields = ['id', 'student', 'paper', 'cat1', 'cat2', 'added_by', 'updated_by', 'created_at', 'updated_at']

  def create(self, validated_data):
    try:
      instance = super().create(validated_data)
      instance.added_by = self.context['request'].user
      return instance
    except IntegrityError:
      raise serializers.ValidationError()
  
  def update(self, instance, validated_data):
    instance.discussion = validated_data.get('discussion', instance.discussion)
    instance.take_away = validated_data.get('take_away', instance.take_away)
    instance.save()
    return instance
