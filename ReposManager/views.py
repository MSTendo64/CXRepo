from rest_framework import generics, viewsets, permissions, filters  
from django.shortcuts import render, get_object_or_404, redirect
from ReposManager.models import Package
from django.http import FileResponse, HttpResponseForbidden
from django.views import View
from django_filters.rest_framework import DjangoFilterBackend  
from rest_framework.decorators import action  
from rest_framework.response import Response  
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .serializers import PackageSerializer 
from .permissions import IsOwnerOrReadOnly
from rest_framework.views import APIView
from rest_framework import status
from django.http import FileResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, CreateView, UpdateView, ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from datetime import date
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from .forms import RegisterForm, PackageUpdateForm
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.
def repo(response):
   return render(response, "status.html")

class PackageDownloadAPIView(APIView):
    """
    API для скачивания пакета по имени и версии
    """
    def get(self, request, pkg_name, pkg_version):
        try:
            package = Package.objects.get(
                pkg_name=pkg_name, 
                pkg_version=pkg_version
            )
            package.save()
            
            return FileResponse(
                package.pkg_file.open('rb'),
                filename=package.pkg_file.name.split('/')[-1],
                as_attachment=True,
                content_type='application/octet-stream'
            )
            
        except Package.DoesNotExist:
            return Response(
                {"error": "Package not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class PackageListAPIView(generics.ListAPIView):
    serializer_class = PackageSerializer
    filter_fields = ['pkg_version']
    search_fields = ['pkg_name']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Package.objects.all()
        return Package.objects.filter(verification_status='verified')

class PackageVersionDetailAPIView(generics.RetrieveAPIView):
    serializer_class = PackageSerializer
    lookup_field = 'pkg_version'

    def get_queryset(self):
        return Package.objects.filter(pkg_name=self.kwargs['pkg_name'])

class PackageDetailAPIView(generics.RetrieveAPIView):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    lookup_field = 'pkg_name'

def package_list(request):
    search_query = request.GET.get('search', '')
    
    # Для администраторов показываем все пакеты
    if request.user.is_staff:
        packages = Package.objects.all().order_by('-pkg_publish_date')
    else:
        packages = Package.objects.filter(verification_status='verified').order_by('-pkg_publish_date')
    
    if search_query:
        packages = packages.filter(
            Q(pkg_name__icontains=search_query) |
            Q(pkg_description__icontains=search_query)
        )
    
    return render(request, 'packages/package_list.html', {
        'packages': packages,
        'search_query': search_query,
        'is_staff': request.user.is_staff
    })

class PackageDetailView(DetailView):
    model = Package
    template_name = 'packages/package_detail.html'
    context_object_name = 'package'
    slug_field = 'pkg_name'
    slug_url_kwarg = 'pkg_name'

    def get_object(self):
        queryset = Package.objects.filter(pkg_name=self.kwargs['pkg_name'])
        # Получаем последнюю версию пакета
        return queryset.order_by('-pkg_publish_date', '-pkg_version').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем все версии пакета, кроме текущей
        context['other_versions'] = Package.objects.filter(
            pkg_name=self.object.pkg_name
        ).exclude(pk=self.object.pk).order_by('-pkg_publish_date', '-pkg_version')
        context['is_staff'] = self.request.user.is_staff
        return context

class PackageDownloadView(View):
    def get(self, request, pkg_name, pkg_version):
        try:
            package = Package.objects.get(
                pkg_name=pkg_name,
                pkg_version=pkg_version
            )
            if package.verification_status == 'verified' or request.user.is_staff:
                response = FileResponse(
                    package.pkg_file.open('rb'),
                    filename=package.pkg_file.name.split('/')[-1],
                    as_attachment=True
                )
                response['Content-Type'] = 'application/zip'
                return response
            else:
                messages.error(request, 'Этот пакет ещё не прошел проверку')
                return redirect('package-detail-view', pkg_name=pkg_name)
        except Package.DoesNotExist:
            return HttpResponseForbidden("Пакет не найден")

class MyPackagesView(LoginRequiredMixin, ListView):
    template_name = 'packages/my_packages.html'
    context_object_name = 'packages'

    def get_queryset(self):
        return Package.objects.filter(owner=self.request.user).order_by('pkg_name', '-pkg_publish_date')

class PackageDeleteView(LoginRequiredMixin, DeleteView):
    model = Package
    success_url = reverse_lazy('my-packages')
    
    def get_queryset(self):
        return Package.objects.filter(owner=self.request.user)

    def delete(self, request, *args, **kwargs):
        package = self.get_object()
        messages.success(request, f'Пакет {package.pkg_name} успешно удален')
        return super().delete(request, *args, **kwargs)

class PackageVerificationView(View):
    @method_decorator(staff_member_required)
    def post(self, request, pkg_name, pkg_version):
        package = get_object_or_404(Package, pkg_name=pkg_name, pkg_version=pkg_version)
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if status in ['verified', 'rejected']:
            package.verification_status = status
            package.admin_comment = comment
            package.save()
            messages.success(
                request,
                'Пакет подтвержден' if status == 'verified' else 'Пакет отклонен'
            )
        
        return redirect('package-detail-view', pkg_name=pkg_name)

class PackageUploadView(LoginRequiredMixin, CreateView):
    model = Package
    template_name = 'packages/upload_package.html'
    fields = ['pkg_name', 'pkg_version', 'pkg_description', 'pkg_file']
    success_url = reverse_lazy('my-packages')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.pkg_publish_date = date.today()
        messages.success(self.request, 'Пакет успешно загружен и отправлен на проверку!')
        return super().form_valid(form)

class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Регистрация успешна! Теперь вы можете войти.')
        return response
    
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        return reverse_lazy('main')

class PackageUpdateView(LoginRequiredMixin, UpdateView):
    model = Package
    form_class = PackageUpdateForm
    template_name = 'packages/update_package.html'
    slug_field = 'pkg_name'
    slug_url_kwarg = 'pkg_name'

    def get_queryset(self):
        return Package.objects.filter(owner=self.request.user, pkg_name=self.kwargs['pkg_name'])

    def get_success_url(self):
        return reverse_lazy('package-detail-view', kwargs={'pkg_name': self.object.pkg_name})

    def form_valid(self, form):
        form.instance.verification_status = 'pending'
        form.instance.pkg_publish_date = date.today()
        messages.success(self.request, 'Пакет успешно обновлен и отправлен на проверку')
        return super().form_valid(form)