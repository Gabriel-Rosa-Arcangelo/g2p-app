from django.shortcuts import render, redirect
from django.conf import settings
import os
import shutil
import sys
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from allauth.account.models import EmailAddress
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from allauth.account.views import SignupView
from django.urls import reverse_lazy
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import JsonResponse
from django.utils.translation import gettext as _
import zipfile
from django.shortcuts import reverse, HttpResponseRedirect
from os.path import join, getmtime
from datetime import datetime
from .models import UserActivity, Sample, UserSettings
from django.utils import timezone
from subprocess import Popen, PIPE, CalledProcessError


class CustomSignupView(SignupView):
    def get_success_url(self):
        return reverse_lazy('picture') 
    
@login_required
def profile(request):
    # Busca as atividades do usuário e as ordene por data e hora (timestamp)
    user_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:5]  # Busca as últimas 5 atividades do usuário
    # Busca os samples do usuário e os ordene por data de criação
    samples = Sample.objects.filter(user=request.user).order_by('-created_at')[:5]  # Busca os últimos 5 samples do usuário

    return render(request, 'account/home.html', {
        'user_activities': user_activities,
        'samples': samples
    })
    
from allauth.account.views import LoginView as AllauthLoginView
from .forms import CustomLoginForm
from .forms import UserSettingsForm

class CustomLoginView(AllauthLoginView):
    form_class = CustomLoginForm
    
@login_required
def picture(request):
    if request.method == 'POST' and request.FILES.get('picture'):
        picture = request.FILES['picture']
        user_id = request.user.id
        photo = os.path.join(settings.MEDIA_ROOT, 'photo')
        # Diretório do usuário
        user_directory = os.path.join(photo, str(user_id))
        print("Diretório do usuário:", user_directory)
        if not os.path.exists(user_directory):
            os.makedirs(user_directory)
        # Salvar a imagem no diretório do usuário
        picture_path = os.path.join(user_directory, picture.name)
        with open(picture_path, 'wb+') as destination:
            for chunk in picture.chunks():
                destination.write(chunk)

        # Saída de impressão para verificar o caminho da imagem salva
        print("Caminho da imagem salva:", picture_path)
    
    return render(request, 'account/profile_picture.html')

@login_required
def loading(request):
    return redirect('home')

def view_file(request, file_type, filename):
    user_id = request.user.id
    base_path = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(user_id), filename)
    
    if os.path.isfile(base_path):
        with open(base_path, 'rb') as f:
            response = HttpResponse(f.read())
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    return HttpResponse('File not found', status=404)

@login_required
def results(request, folder_path=''):
    base_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
    user_dir = os.path.join(base_dir, str(request.user.id))
    current_dir = os.path.join(user_dir, folder_path)

    if not os.path.exists(current_dir):
        os.makedirs(current_dir)

    search_query = request.GET.get('search', '')

    subfolders = [f for f in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, f))]
    if search_query:
        subfolders = [folder for folder in subfolders if search_query.lower() in folder.lower()]

    files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
    if search_query:
        files = [file for file in files if search_query.lower() in file.lower()]

    return render(request, 'account/results.html', {
        'subfolders': subfolders,
        'files': files,
        'folder_path': folder_path,
        'search_query': search_query
    })


@login_required
def download_file(request):
    if request.method == 'POST':
        file_name = request.POST.get('file_name')
        folder_path = request.POST.get('folder_path', '')

        user_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(request.user.id))
        file_path = os.path.join(user_dir, folder_path, file_name)

        with open(file_path, 'rb') as file:
            response = HttpResponse(file.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response

    return HttpResponse('Error downloading the file.')
            
            
def remove_empty_dirs(path):
    # Remove empty directories recursively
    if os.path.isdir(path):
        # Start with the deepest directories and work upwards
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            if not dirnames and not filenames:
                os.rmdir(dirpath)
        
        # Check if the root directory itself is empty
        if not os.listdir(path):
            os.rmdir(path)

@login_required
def delete_file(request):
    if request.method == 'POST':
        try:
            file_name = request.POST.get('file_name')
            folder_path = request.POST.get('folder_path', '')

            user_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(request.user.id))
            file_path = os.path.join(user_dir, folder_path, file_name)

            if os.path.exists(file_path):
                backup_dir = os.path.join(settings.MEDIA_ROOT, 'backup', str(request.user.id), folder_path)
                if not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                shutil.move(file_path, os.path.join(backup_dir, file_name))
                
                # Check if the folder is empty and delete it if so
                remove_empty_dirs(os.path.join(user_dir, folder_path))
                
                return redirect(request.META.get('HTTP_REFERER', 'results'))
            else:
                return HttpResponse('The file does not exist.')
        except Exception as e:
            return HttpResponse(f'Error deleting the file: {e}')
    return HttpResponse('Invalid request.')

@login_required
def batch_action_results(request):
    error_message = None

    if request.method == 'POST':
        action = request.POST.get('batch_action')
        selected_files = request.POST.getlist('selected_files[]')
        selected_folders = request.POST.getlist('selected_folders[]')
        folder_path = request.POST.get('folder_path', '')

        user_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs', str(request.user.id))
        current_dir = os.path.join(user_dir, folder_path)

        if action == 'download':
            response = HttpResponse(content_type='application/zip')
            zip_file = zipfile.ZipFile(response, 'w')

            for file_name in selected_files:
                file_path = os.path.join(current_dir, file_name)
                if os.path.exists(file_path):
                    zip_file.write(file_path, os.path.basename(file_path))

            for folder_name in selected_folders:
                folder_path = os.path.join(current_dir, folder_name)
                if os.path.exists(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zip_file.write(file_path, os.path.relpath(file_path, current_dir))

            zip_file.close()
            response['Content-Disposition'] = 'attachment; filename="download.zip"'
            return response

        elif action == 'delete':
            backup_dir = os.path.join(settings.MEDIA_ROOT, 'backup', str(request.user.id), folder_path)
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            for file_name in selected_files:
                file_path = os.path.join(current_dir, file_name)
                if os.path.exists(file_path):
                    shutil.move(file_path, os.path.join(backup_dir, file_name))
                else:
                    error_message = f'File not found: {file_name}'
                    break

            for folder_name in selected_folders:
                folder_full_path = os.path.join(current_dir, folder_name)
                backup_folder_path = os.path.join(backup_dir, folder_name)
                if os.path.exists(folder_full_path):
                    shutil.move(folder_full_path, backup_folder_path)
                else:
                    error_message = f'Folder not found: {folder_name}'
                    break

            if not error_message:
                # Remove empty directories and handle the case where the main folder is gone
                try:
                    remove_empty_dirs(current_dir)
                    remove_empty_dirs(user_dir)  # Ensure to also remove empty folders in the user's root directory
                except Exception as e:
                    error_message = f'Error removing empty directories: {e}'
                
                # Redirect to the main results page if the current directory was removed
                if not os.path.exists(current_dir):
                    return redirect('results')

                return redirect(request.META.get('HTTP_REFERER', 'results'))

        else:
            error_message = 'Invalid action. Please select a valid action.'

    return render(request, 'account/results.html', {'error_message': error_message})

@login_required
def change_password(request):
    return render(request, 'account/account_reset_password')

import logging

from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.http import JsonResponse

@csrf_exempt
@login_required
def user_settings(request):
    user_id = request.user.id
    photo_directory = os.path.join(settings.MEDIA_ROOT, 'photo', str(user_id))

    profile_picture = None
    if os.path.exists(photo_directory):
        user_files = os.listdir(photo_directory)
        for file in user_files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                profile_picture = os.path.join(settings.MEDIA_URL, 'photo', str(user_id), file)
                break

    user_settings_instance, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        if request.POST.get('issue_type') and request.POST.get('description'):
            # Lógica para salvar o feedback
            issue_type = request.POST.get('issue_type')
            description = request.POST.get('description')

            # Define o caminho da pasta com base no tipo de problema
            base_path = os.path.join(settings.MEDIA_ROOT, 'report', issue_type)

            # Cria a pasta se não existir
            os.makedirs(base_path, exist_ok=True)

            # Conta o número de arquivos existentes para definir o nome do próximo arquivo
            file_count = len([name for name in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, name))])
            next_file_number = file_count + 1

            # Define o nome do arquivo
            file_name = f"{issue_type}#{next_file_number:02d}.txt"
            file_path = os.path.join(base_path, file_name)

            # Salva a descrição no arquivo
            with open(file_path, 'w') as file:
                file.write(description)

            return JsonResponse({'message': 'Feedback enviado com sucesso!'}, status=200)

        elif request.FILES.get('profile_picture'):
            # Lógica para salvar a foto de perfil
            picture = request.FILES['profile_picture']
            user_directory = photo_directory

            if not os.path.exists(user_directory):
                os.makedirs(user_directory)

            # Remove a foto antiga, se existir
            for file in os.listdir(user_directory):
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    os.remove(os.path.join(user_directory, file))

            # Salva a nova imagem
            picture_path = os.path.join(user_directory, picture.name)
            with open(picture_path, 'wb+') as destination:
                for chunk in picture.chunks():
                    destination.write(chunk)

            return redirect(reverse('settings'))  # Usar reverse para gerar a URL

        else:
            # Lógica para salvar as configurações do usuário
            form = UserSettingsForm(request.POST, instance=user_settings_instance)
            if form.is_valid():
                form.save()
                logger.info('User settings saved successfully.')
                return redirect(reverse('settings'))  # Usar reverse para gerar a URL
            else:
                logger.error('Form is not valid: %s', form.errors)

    else:
        form = UserSettingsForm(instance=user_settings_instance)

    context = {
        'profile_picture': profile_picture,
        'form': form,
    }

    return render(request, 'account/settings.html', context)

# Configuração do logger
logger = logging.getLogger(__name__)

@login_required
def submit_reads(request):
    logs = ""  

    if request.method == 'POST':
        if 'arquivo' in request.FILES:
            arquivos = request.FILES.getlist('arquivo')
            tipos_permitidos = ('.fas', '.fa', '.fna', '.fasta')
            arquivos_invalidos = [arquivo for arquivo in arquivos if not arquivo.name.endswith(tipos_permitidos)]

            if arquivos_invalidos:
                return JsonResponse({'erro': 'Please upload a file in .fas, .fa, .fna or .fasta format.'})

            num_arquivos = len(arquivos)
            description = f"{num_arquivos} file(s) were uploaded."
            
            UserActivity.objects.create(
                user=request.user,
                activity_type='Submit',
                description=description,
                timestamp=timezone.now()  
            )
            
            arquivo_paths = []
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'uploads'))

            for arquivo in arquivos:
                if arquivo.name.endswith('.fasta'):
                    arquivo_salvo = fs.save(arquivo.name, arquivo)
                else:
                    conteudo = arquivo.read().decode('utf-8')
                    novo_nome = f"{arquivo.name.split('.')[0]}.fasta"
                    novo_arquivo = SimpleUploadedFile(novo_nome, conteudo.encode('utf-8'), 'text/plain')
                    arquivo_salvo = fs.save(novo_arquivo.name, novo_arquivo)

                arquivo_path = fs.path(arquivo_salvo)
                arquivo_paths.append(arquivo_path)

            folder = os.path.dirname(arquivo_paths[0])
            script_python_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts', 'hiv.py')
            comando = [sys.executable, script_python_path, folder, *arquivo_paths, str(request.user.id)]
            
            try:
                process = Popen(comando, stdout=PIPE, stderr=PIPE)
                out, err = process.communicate()
                
                logs = out.decode('utf-8') + err.decode('utf-8')

                if process.returncode == 0:
                    UserActivity.objects.create(
                        user=request.user,
                        activity_type='Submit Processed',
                        description='Submit process completed',
                        timestamp=timezone.now()  
                    )
                    for arquivo_path in arquivo_paths:
                        os.remove(arquivo_path)

                    # Save Sample information
                    for arquivo in arquivos:
                        Sample.objects.create(
                            user=request.user,
                            fasta_file_name=arquivo.name,
                            fasta_file_size=arquivo.size,
                        )

                    return JsonResponse({'mensagem': 'Files uploaded successfully!', 'logs': logs})
                else:
                    logs += f"\nPython script execution failed with return code: {process.returncode}"
                    UserActivity.objects.create(
                        user=request.user,
                        activity_type='Submit Processed',
                        description='Submit process was incomplete',
                        timestamp=timezone.now()  
                    )
                    for arquivo_path in arquivo_paths:
                        os.remove(arquivo_path)
                    return JsonResponse({'erro': 'Submission failed.','logs': logs})
                
            except CalledProcessError as e:
                logs = f"Error executing Python script: {e}"
                logger.error(logs)
                return JsonResponse({'erro': 'Submission failed.', 'logs': logs})
        else:
            return JsonResponse({'erro': 'Please select a file to upload.'})

    return render(request, 'account/submit.html')
