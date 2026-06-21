"""
课程应用 - 视图
包含课程列表、详情、我的课程、课程创建/编辑、课时创建/详情、选课等视图。
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DetailView, ListView, UpdateView, View,
)

from .forms import CourseForm, LessonForm
from .models import Category, Course, Enrollment, Lesson


class TeacherRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """教师/管理员权限混入类"""

    def test_func(self):
        """仅教师或管理员(staff)可访问"""
        return (
            self.request.user.is_authenticated
            and (self.request.user.is_teacher or self.request.user.is_staff)
        )


def course_list(request):
    """课程列表：支持分类筛选与标题搜索"""
    courses = Course.objects.filter(is_published=True)

    # 分类筛选
    category_id = request.GET.get('category')
    if category_id:
        courses = courses.filter(category_id=category_id)

    # 标题搜索
    q = request.GET.get('q')
    if q:
        courses = courses.filter(title__icontains=q)

    categories = Category.objects.all()
    return render(request, 'courses/course_list.html', {
        'courses': courses,
        'categories': categories,
        'current_category': category_id,
        'q': q or '',
    })


class CourseDetailView(DetailView):
    """课程详情：显示课程信息、课时列表，以及选课按钮"""
    model = Course
    template_name = 'courses/course_detail.html'
    context_object_name = 'course'

    def get_queryset(self):
        # 已发布的课程或教师本人查看未发布的课程
        queryset = Course.objects.all()
        if self.request.user.is_authenticated and self.request.user.is_teacher:
            return queryset
        return queryset.filter(is_published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        context['lessons'] = course.lessons.all()

        # 判断当前用户是否已选课
        is_enrolled = False
        if self.request.user.is_authenticated:
            is_enrolled = Enrollment.objects.filter(
                course=course, student=self.request.user
            ).exists()
        context['is_enrolled'] = is_enrolled
        return context


class MyCoursesView(LoginRequiredMixin, View):
    """我的课程：学员查看已选课程，教师查看所授课程"""

    def get(self, request):
        enrolled_courses = []
        taught_courses = []

        if request.user.is_student:
            enrollments = Enrollment.objects.filter(student=request.user)
            enrolled_courses = [e.course for e in enrollments]

        if request.user.is_teacher or request.user.is_staff:
            taught_courses = Course.objects.filter(teacher=request.user)

        return render(request, 'courses/my_courses.html', {
            'enrolled_courses': enrolled_courses,
            'taught_courses': taught_courses,
        })


class CourseCreateView(TeacherRequiredMixin, CreateView):
    """创建课程（仅教师/管理员）"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:my_courses')

    def form_valid(self, form):
        # 自动设置教师为当前用户
        form.instance.teacher = self.request.user
        messages.success(self.request, '课程创建成功！')
        return super().form_valid(form)


class CourseEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """编辑课程（仅课程教师本人或管理员）"""
    model = Course
    form_class = CourseForm
    template_name = 'courses/course_form.html'
    success_url = reverse_lazy('courses:my_courses')

    def test_func(self):
        course = self.get_object()
        return (
            self.request.user.is_authenticated
            and (
                course.teacher == self.request.user
                or self.request.user.is_staff
            )
        )

    def form_valid(self, form):
        messages.success(self.request, '课程更新成功！')
        return super().form_valid(form)


class LessonCreateView(TeacherRequiredMixin, View):
    """添加课时（仅该课程的教师或管理员）"""

    def get(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        # 权限校验：必须是该课程的教师或管理员
        if course.teacher != request.user and not request.user.is_staff:
            messages.error(request, '您无权为该课程添加课时。')
            return redirect('courses:course_detail', pk=course.pk)
        form = LessonForm()
        return render(request, 'courses/lesson_form.html', {
            'form': form,
            'course': course,
        })

    def post(self, request, course_pk):
        course = get_object_or_404(Course, pk=course_pk)
        if course.teacher != request.user and not request.user.is_staff:
            messages.error(request, '您无权为该课程添加课时。')
            return redirect('courses:course_detail', pk=course.pk)
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, '课时添加成功！')
            return redirect('courses:course_detail', pk=course.pk)
        return render(request, 'courses/lesson_form.html', {
            'form': form,
            'course': course,
        })


class LessonDetailView(LoginRequiredMixin, DetailView):
    """课时详情：需选课或为该课程教师才能查看"""
    model = Lesson
    template_name = 'courses/lesson_detail.html'
    context_object_name = 'lesson'

    def get_object(self, queryset=None):
        course_pk = self.kwargs.get('course_pk')
        pk = self.kwargs.get('pk')
        lesson = get_object_or_404(Lesson, pk=pk, course_id=course_pk)
        return lesson

    def dispatch(self, request, *args, **kwargs):
        lesson = self.get_object()
        course = lesson.course
        user = request.user

        # 教师本人或管理员可直接访问
        if course.teacher == user or user.is_staff:
            return super().dispatch(request, *args, **kwargs)

        # 学员需已选课
        if not Enrollment.objects.filter(course=course, student=user).exists():
            messages.error(request, '请先选课后再查看课时内容。')
            return redirect('courses:course_detail', pk=course.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = self.object.course
        return context


class EnrollView(LoginRequiredMixin, View):
    """选课视图（仅 POST）"""

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)
        # 幂等：已选课则提示
        enrollment, created = Enrollment.objects.get_or_create(
            course=course,
            student=request.user,
        )
        if created:
            messages.success(request, f'成功选课：{course.title}')
        else:
            messages.info(request, '您已选过该课程。')
        return redirect('courses:course_detail', pk=course.pk)
