from datetime import datetime
import time
from kivy.network.urlrequest import UrlRequest
import json
import threading
import requests
from kivy.utils import platform
from kivy.properties import StringProperty, NumericProperty, DictProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import MDSnackbar
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDRectangleFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.storage.jsonstore import JsonStore
from kivy.lang import Builder
from kivy.factory import Factory
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivymd.app import MDApp
import kivy
import uuid
import os
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
import urllib.parse
import shutil
from plyer import notification
from plyer import filechooser
from kivy.cache import Cache
shutil.copytree = lambda src, dst, *args, **kwargs: dst

# Настройка окружения Kivy
if 'ANDROID_PRIVATE' in os.environ:
    os.environ['KIVY_HOME'] = os.path.join(
        os.environ['ANDROID_PRIVATE'], 'kivy_home')
    os.makedirs(os.environ['KIVY_HOME'], exist_ok=True)

kivy.require('2.3.1')


def ask_permissions():
    if platform == 'android':
        from android.permissions import request_permissions, Permission # type: ignore
        request_permissions([
            Permission.INTERNET, 
            Permission.POST_NOTIFICATIONS, 
            Permission.VIBRATE
        ])

class BaseScreen(MDScreen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.app = MDApp.get_running_app()

class IpConnectionScreen(BaseScreen):
    status_text = StringProperty("Введите адрес сервера")

    def start_check(self, url=None):
        # Если url передан (из авто-проверки), используем его.
        # Если url не передан (нажата кнопка), собираем из полей.
        if not url:
            ip = self.ids.ip_field.text.strip()
            port = self.ids.port_field.text.strip() or "8000"
            url = f"{ip}:{port}"

        if not url.startswith("http"):
            url = f"http://{url}"

        self.status_text = f"Проверка {url}..."
        
        UrlRequest(
            url,
            on_success=self._on_success,
            on_error=self._on_error,
            on_failure=self._on_failure,
            timeout=5
        )


    def _on_success(self, request, result):
        self.status_text = "Успешно! Сохранено."
        # Сохраняем проверенный URL (включая порт)
        self.app.save_settings(request.url)
        self.manager.current = "Registration"

    def _on_failure(self, request, result):
        # Вызывается, если сервер ответил, но с ошибкой (например 404)
        self.status_text = f"Сервер ответил ошибкой: {request.resp_status}"

    def _on_error(self, request, error):
        # Вызывается при ошибках сети (таймаут, неверный IP)
        self.status_text = "Ошибка сети. Проверьте IP и порт."
        print(f"Network error: {error}")


class RegistrationScreen(BaseScreen):
    
    def check_username(self, text):
        field = self.ids.username_field
        # Более чистая логика условий
        if text and not (3 <= len(text) <= 20):
            field.error = True
            field.helper_text = "Имя должно быть от 3 до 20 символов"
        else:
            field.error = False
            field.helper_text = ""

    def check_password(self, text):
        field = self.ids.password_field
        if text and not (8 <= len(text) <= 50):
            field.error = True
            field.helper_text = "Пароль должен быть от 8 до 50 символов"
        else:
            field.error = False
            field.helper_text = ""

    def request_code(self):
        app = MDApp.get_running_app()
        
        # 1. Сначала получаем email
        email = self.ids.mail_field.text.strip()
        if not email:
            print("Ошибка: Поле email пустое")
            return

        # 2. Получаем базовый URL и очищаем его
        base = app.base_url if app.base_url else "127.0.0.1:8000"
        if not base.startswith("http"):
            base = f"http://{base}"
        
        # Убираем лишний слеш в конце, если он есть, чтобы не было //api
        base = base.rstrip('/')
        
        # 3. Формируем полный URL (теперь это будет работать всегда)
        self.full_url = f"{base}/api/v1/auth/send-code?email={email}"
        
        print(f"DEBUG: ОТПРАВКА НА {self.full_url}")

        UrlRequest(
            self.full_url,
            on_success=self._on_code_sent,
            on_failure=self._on_error,
            on_error=self._on_error,
            method='POST'
        )

    def _on_code_sent(self, request, result):
        # Получаем код из ответа сервера
        code = result.get("test_code")
        
        # Уведомление (работает на Android и Desktop при наличии plyer)
        try:
            notification.notify(
                title='Код подтверждения',
                message=f'Ваш проверочный код: {code}',
                timeout=10
            )
        except Exception as e:
            print(f"Уведомление не сработало: {e}")

        # Сохраняем данные во временное хранилище приложения
        app = MDApp.get_running_app()
        app.temp_user_data = {
            "username": self.ids.username_field.text.strip(),
            "email": self.ids.mail_field.text.strip(),
            "password": self.ids.password_field.text.strip()
        }
        
        self.manager.current = "Verify"

    def _on_error(self, req, res):
        # res в случае ошибки часто является словарем или строкой
        print(f"DEBUG: Ошибка запроса на {req.url}")

class LoginScreen(BaseScreen):    
    def check_user(self):
        login_data = {
            "email": self.ids.email_field.text.strip(),
            "password": self.ids.password_field.text.strip()
        }
        
        UrlRequest(
            f"{self.app.base_url}/api/v1/auth/login",
            req_body=json.dumps(login_data),
            req_headers={'Content-Type': 'application/json'},
            on_success=self._on_login_success,
            on_failure=self._on_login_error,
            method='POST'
        )
    
    def _on_login_success(self, req, res):
        token = res.get("access_token")
        self.app.save_auth_token(token)
        self.manager.current = "Hello"
        
    def _on_login_error(self, req, res):
        error_msg = res.get("detail", "Ошибка входа")
        MDSnackbar(
            MDLabel(
                text=str(error_msg),
                theme_text_color="Custom",
                text_color="#ffffff",
            ),
            y="24dp",
            orientation="horizontal",
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()
            
class MainApp(MDApp):
    def __init__(self, **kw):
        super().__init__(**kw)
        
    
    edit_dialog = None  
    dialog = None   
    manager = None
    creating_chat = False
    base_url = StringProperty("")
    user_avatar_path = StringProperty("src/assets/avatar/standartAvatar.png")
    
    def on_start(self):
        ask_permissions()
        self.refresh_base_url()
        Clock.schedule_once(lambda dt: self.check_auth(), 1)

        saved_path = os.path.join(self.user_data_dir, "avatars", "user_avatar.jpg")
        
        if os.path.exists(saved_path):
            self.user_avatar_path = saved_path.replace("\\", "/")
        else:
            # Если своего нет, используем стандартный из папки проекта
            self.user_avatar_path = "src/assets/avatar/standartAvatar.png"
    user_avatar_path = StringProperty("src/assets/avatar/standartAvatar.png")
    bottom_menu_ref = None  # Ссылка на наше меню

    # Метод, который меню вызовет само при создании
    def register_bottom_menu(self, menu_instance):
        self.bottom_menu_ref = menu_instance
        print("Нижнее меню успешно зарегистрировано в системе!")    
        
    def choose_avatar(self):
        try:
            # Открываем системный диалог выбора файла
            filechooser.open_file(
                title="Выберите фото профиля",
                filters=[("Изображения", "*.png", "*.jpg", "*.jpeg")],
                on_selection=self._on_file_selection
            )
        except Exception as e:
            print(f"Ошибка открытия проводника: {e}")

    def _on_file_selection(self, selection):
        # selection возвращает список путей (даже если выбран один файл)
        if selection and len(selection) > 0:
            file_path = selection[0]
            self.update_avatar(file_path)


    def update_avatar(self, path):
        # 1. Извлекаем путь из filechooser
        src_path = path if isinstance(path, list) else path
        if not src_path or not os.path.exists(src_path): return

        # 2. Определяем путь в папке данных (универсально для Windows/Android)
        avatar_dir = os.path.join(self.user_data_dir, "avatars")
        os.makedirs(avatar_dir, exist_ok=True)
        save_path = os.path.join(avatar_dir, "user_avatar.jpg")

        try:
            # 3. Копируем файл
            import shutil
            shutil.copy2(src_path, save_path)
            
            # 4. Чистим кэш Kivy
            from kivy.cache import Cache
            Cache.remove('kv.image')
            Cache.remove('kv.texture')

            # 5. Обновляем путь в свойстве
            self.user_avatar_path = save_path.replace("\\", "/")
            
            # 6. Вызываем перерисовку через микро-паузу
            from kivy.clock import Clock
            Clock.schedule_once(self._finalize_avatar_update, 0.1)
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    def _finalize_avatar_update(self, dt=None):
        from kivy.factory import Factory
        from kivy.clock import Clock
        
        # 1. ОБНОВЛЯЕМ ЭКРАН ПРОФИЛЯ (это у вас работало)
        sm = self.root.ids.get('screen_manager')
        if sm and sm.has_screen('Profile'):
            screen = sm.get_screen('Profile')
            old_avatar = screen.ids.get('avatar')
            if old_avatar:
                container = old_avatar.parent
                container.clear_widgets()
                new_avatar = Factory.FitImage(source=self.user_avatar_path, nocache=True, radius=[20,])
                container.add_widget(new_avatar)
                screen.ids['avatar'] = new_avatar
                Clock.schedule_once(lambda x: new_avatar.reload(), 0.1)

        # 2. ОБНОВЛЯЕМ НИЖНЕЕ МЕНЮ (Через прямую ссылку)
        if self.bottom_menu_ref:
            # Ищем аватар внутри сохраненной ссылки на меню
            bottom_avatar_widget = self.bottom_menu_ref.ids.get('bottom_avatar')
            
            if bottom_avatar_widget:
                container = bottom_avatar_widget.parent
                container.clear_widgets()
                
                new_nav_avatar = Factory.FitImage(
                    source=self.user_avatar_path,
                    nocache=True,
                    radius=[25, ]
                )
                container.add_widget(new_nav_avatar)
                # Обновляем ID в словаре меню для следующей замены
                self.bottom_menu_ref.ids['bottom_avatar'] = new_nav_avatar
                
                Clock.schedule_once(lambda x: new_nav_avatar.reload(), 0.1)
                print("МЕНЮ: Аватар успешно обновлен через прямую ссылку")
        else:
            print("ОШИБКА: Нижнее меню еще не зарегистрировано!")
            
          
    def check_auth(self):   
        token = self.get_auth_token()
        if token:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
                
            UrlRequest(
                f"{self.base_url}/api/v1/auth/me",
                req_headers=headers,
                on_success=self._auto_login_success,
                on_error=self._auto_login_error,
                on_failure=self._auto_login_error
            )
        else:
            self.manager.current = "Login"
     
    def refresh_base_url(self):
        if self.store.exists('server'):
            self.base_url = self.store.get('server')['url']
        else:
            self.base_url = "http://192.168.1.5:8000"
            
             
    def _auto_login_success(self, req, res):
        print("Валидный токен, успех")
        self.manager.current = "Hello"

    def _auto_login_error(self, req, res):
        print("Токен не валиден")
        self.logout()
          
    def build(self):
        Window.softinput_mode = "below_target" 
        self.theme_cls.background_color = [0.91, 0.94, 0.95, 1]
        storage_path = os.path.join(
            self.user_data_dir, 
            "settings.json"
        )
        self.store = JsonStore(storage_path)
        self.root = Builder.load_file("src/kv/main.kv")
        self.manager = self.root.ids.screen_manager
        return self.root

    def save_settings(self, url):
        clean_url = url.rstrip('/')
        self.store.put('server', url=clean_url)
        self.base_url = clean_url
        
    def save_auth_token(self, token):
        self.store.put('auth', token=token)
        print(f"Токен сохранен {token[:10]}")
    
    def get_auth_token(self):
        if self.store.exists('auth'):
            return self.store.get('auth')['token']
        return None
    
    def logout(self):
        self.store.delete('auth')
        self.manager.current = "Login"
               
    def get_saved_url(self):
        if self.store.exists('server'):
            return self.store.get('server')['url']
        return "192.168.1.5:8000"

    def auto_check_saved_url(self):

        IpConnScreen = self.manager.get_screen("IPConn")
        IpConnScreen.start_check(self.get_saved_url())

    def check_response(self, req, res):
        if req.resp_status == 401:
            print("Сессия истекла")
            self.logout()
            return False
        return True

    def update_menu_visibility(self, screen_name):
        visible_screens = ["ChatList", "Tests", "Profile", "Diary", "Setting", "General"]
        menu = self.root.ids.bottom_nav
        
        if screen_name in visible_screens:
            menu.opacity = 1
            menu.disabled = False
        else:
            menu.opacity = 0
            menu.disabled = True 
       
    def load_chat_list(self):
        
        token = self.get_auth_token()
        
        headers = {'Authorization': f'Bearer {token}'}
        
        UrlRequest(
            f"{self.base_url}/api/v1/dialogs/",
            req_headers=headers,
            on_success=self._display_chats,
            on_failure=self.check_response
        )
        
    def _display_chats(self, req, res):
        chat_list_screen = self.manager.get_screen("ChatList")
        container = chat_list_screen.ids.chat_container
        container.clear_widgets()
        
        # res — это список словарей, которые прислал сервер
        for dialog in res:
            item = Factory.ChatListItem()
            item.chat_id = str(dialog.get('id', ''))
            
            # БЕРЕМ ДАННЫЕ ИЗ БАЗЫ: используем ключ 'title'
            # Если в базе title пустой, оставляем запасной вариант
            item.title = str(dialog.get('title') or f"Чат №{item.chat_id}")
            
            # Привязываем нажатие для открытия чата
            item.bind(on_release=lambda x: self.open_existing_chat(x.chat_id))
            
            container.add_widget(item)
            
    def create_and_open_new_chat(self):
        if self.creating_chat:
            return
        self.creating_chat = True
        
        token = self.get_auth_token()
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        } 
        data = {
            "title": "Новый чат",
            "user_promt": "",
            "model_answer": "",
            "emotions": ""
            }
        
        UrlRequest(
            f"{self.base_url}/api/v1/dialogs/",
            req_body=json.dumps(data),
            req_headers=headers,
            on_success=self._on_chat_created,
            on_failure=self._on_chat_failed,
            method='POST'
        )
    
    def _on_chat_created(self, req, res):
        self.creating_chat = False
        self.open_existing_chat(res['id'])
    
    def _on_chat_failed(self, req, res):
        self.creating_chat = False
    
    def open_existing_chat(self, chat_id):
        if not chat_id:
            print("Ошибка: попытка открыть чат без ID")
            return
        
        chat_screen = self.manager.get_screen("Chat")
        chat_screen.chat_id = str(chat_id)
        
        self.load_chat_history(chat_id)
        
        self.manager.current = "Chat"       
        print(f"Открыт чат с ID {chat_id}")
    
    def send_message(self, text):
        if not text.strip():
            return
        
        # 1. Добавляем сообщение пользователя
        self.add_message_to_view(text, is_user=True)
        
        # 2. Очищаем поле ввода
        self.manager.get_screen("Chat").ids.chat_input.text = ""
        
        # 3. Создаем НОВОЕ сообщение ИИ и СРАЗУ сохраняем ссылки на него
        # Это самое важное: теперь self.current_ai_label смотрит на СВЕЖИЙ виджет
        new_ai_bubble = self.add_message_to_view("", is_user=False)
        self.current_ai_msg = new_ai_bubble
        self.current_ai_label = new_ai_bubble.ids.label_text 
        
        # 4. Скроллим вниз перед началом генерации
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
        
        # 5. Запуск стрима
        threading.Thread(
            target=self.stream_request,
            args=(text,),
            daemon=True
        ).start()

    
    def stream_request(self, text):
        token = self.get_auth_token()
        chat_screen = self.root.ids.screen_manager.get_screen("Chat")
        chat_id = chat_screen.chat_id
            
        url = f"{self.base_url}/model?dialog_id={chat_id}"
        headers = {'Authorization': f'Bearer {token}'}
        
        try:
            with requests.post(url, data=text.encode('utf-8'), headers=headers, stream=True) as r:
                for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        Clock.schedule_once(lambda dt, c=chunk: self.update_ai_text(c))
        except Exception as e:
            print(f"Ошибка стриминга: {e}")

    def update_ai_text(self, chunk):
        # Проверяем, что ссылка актуальна и виджет существует
        if hasattr(self, 'current_ai_label') and self.current_ai_label.parent:
            try:
                # ОБНОВЛЯЕМ ТОЛЬКО ОДИН РАЗ (только лейбл)
                self.current_ai_label.text += chunk
                
                # Скроллим только если текст действительно добавился
                   
            except Exception as e:
                print(f"Ошибка обновления: {e}")
        else:
            # Если попали сюда, значит чанк пришел, а облако еще не готово
            print("Целевой лейбл не доступен")
        
    def scroll_to_bottom(self):
        chat_scroll = self.manager.get_screen("Chat").ids.chat_scroll
        chat_scroll.scroll_y = 0

    def on_send_button_pressed(self, text):
        # 1. Добавляем сообщение пользователя
        self.add_message_to_view(text, is_user=True)
        
        # 2. Создаем ПУСТОЕ сообщение ИИ и сохраняем ссылку на него
        # Именно этот вызов перезапишет self.current_ai_msg новым объектом
        ai_bubble = self.add_message_to_view("", is_user=False)
        self.current_ai_msg = ai_bubble 
        # Если внутри есть лейбл: self.current_ai_label = ai_bubble.ids.label_text
        
        # 3. Запускаем поток стриминга
        threading.Thread(target=self.stream_request, args=(text,)).start()

    def add_message_to_view(self, text, is_user=True):
        chat_history = self.manager.get_screen("Chat").ids.chat_history
        
        if is_user:
            bubble = Factory.UserBubble()
            bubble.text = text
            chat_history.add_widget(bubble)
            return bubble
        else:
            # Используем обновленный класс AiMessage
            bubble = Factory.AiMessage()
            # Текст записываем сразу в label_text.text (так как мы ищем его в stream_request)
            bubble.ids.label_text.text = text 
            chat_history.add_widget(bubble)
            return bubble
    
    def back_to_list(self):
        self.root.ids.screen_manager.transition.direction = "right"
        self.root.ids.screen_manager.current = "ChatList"
        # При возврате обновляем список, чтобы увидеть изменения
        self.load_chat_list()  
        
    def load_chat_history(self, chat_id):
        token = self.get_auth_token()
        base_url = self.get_saved_url()
        headers = {'Authorization': f'Bearer {token}'}
        
        UrlRequest(
            f"{base_url}/api/v1/dialogs/{chat_id}",
            req_headers=headers,
            on_success=self._on_history_success,
            on_failure=self.check_response,
            method='GET'
        )
    
    def _on_history_success(self, req, res):
        chat_screen = self.root.ids.screen_manager.get_screen("Chat")
        history_container = chat_screen.ids.chat_history
        history_container.clear_widgets()
        
        # 1. Получаем полные строки из БД
        user_prompts = res.get("user_prompt", "")
        model_answers = res.get("model_answer", "")

        # 2. Разбиваем строки на списки по символу \n
        # filter(None, ...) уберет пустые строки, если они есть
        user_list = list(filter(None, user_prompts.split('\n')))
        ai_list = list(filter(None, model_answers.split('\n')))

        # 3. Поочередно добавляем их в интерфейс
        # Используем zip_longest, если количество вопросов и ответов может не совпадать
        from itertools import zip_longest
        
        for user_msg, ai_msg in zip_longest(user_list, ai_list):
            if user_msg:
                self.add_message_to_view(user_msg.strip(), is_user=True)
            if ai_msg:
                self.add_message_to_view(ai_msg.strip(), is_user=False)
        
        # Скролл в самый низ после загрузки
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
    
    def show_edit_dialog(self, chat_id, current_title):
        # Создаем контент из KV (класс EditChatContent должен быть в main.kv)
        content = Factory.EditChatContent()
        content.ids.rename_field.text = current_title
        
        # Создаем сам диалог
        self.edit_dialog = MDDialog(
            title="Редактировать чат",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(
                    text="УДАЛИТЬ", 
                    theme_text_color="Custom", 
                    text_color="red",
                    on_release=lambda x: self.delete_chat(chat_id)
                ),
                MDRaisedButton(
                    text="СОХРАНИТЬ",
                    on_release=lambda x: self.rename_chat(chat_id, content.ids.rename_field.text)
                ),
            ],
        )
        self.edit_dialog.open()

    def delete_chat(self, chat_id):
        if self.edit_dialog:
            self.edit_dialog.dismiss()
        
        UrlRequest(
            f"{self.base_url}/api/v1/dialogs/{chat_id}",
            method='DELETE',
            req_headers={'Authorization': f'Bearer {self.get_auth_token()}'},
            on_success=lambda r, v: self.load_chat_list()
        )

    def rename_chat(self, chat_id, new_title):
        if self.edit_dialog:
            self.edit_dialog.dismiss()
            
        
        # Экранируем только название (пробелы станут %20, кириллица — кодами)
        safe_title = urllib.parse.quote(new_title)
        
        # Формируем итоговую строку
        request_url = f"{self.base_url}/api/v1/dialogs/{chat_id}/rename?title={safe_title}"
        
        UrlRequest(
            request_url,
            method='PATCH',
            req_headers={'Authorization': f'Bearer {self.get_auth_token()}'},
            on_success=lambda r, v: self.load_chat_list()
        )
    name_dialog = None

    def show_edit_name_dialog(self):
        if not self.name_dialog:
            # 1. Создаем контейнер для поля ввода
            content = Factory.MDBoxLayout(
                orientation="vertical",
                adaptive_height=True,
                padding=[0, "12dp", 0, "12dp"]
            )

            self.name_input = Factory.MDTextField(
                hint_text="Введите новое имя",
                mode="rectangle"
            )
            content.add_widget(self.name_input)

            # 2. Собираем диалог (БЕЗ лишних запятых после знака =)
            self.name_dialog = Factory.MDDialog(
                title="Редактировать профиль",
                type="custom",
                content_cls=content,
                buttons=[
                    Factory.MDFlatButton(
                        text="ОТМЕНА",
                        on_release=lambda x: self.name_dialog.dismiss()
                    ),
                    Factory.MDRaisedButton(
                        text="СОХРАНИТЬ",
                        md_bg_color=[0.44, 0.62, 0.75, 1],
                        on_release=lambda x: self.save_new_name()
                    )
                ]
            )

        # 3. Обновляем текст в поле перед каждым открытием
        current_name = self.root.ids.screen_manager.get_screen("Profile").ids.user_name_label.text
        self.name_input.text = current_name
        self.name_dialog.open()
    def save_new_name(self):
        # 1. Получаем текст из поля ввода
        new_name = self.name_input.text.strip()
        
        if new_name:
            # 2. Обновляем текст на экране профиля
            profile_screen = self.root.ids.screen_manager.get_screen("Profile")
            profile_screen.ids.user_name_label.text = new_name
            
            # 3. Закрываем диалог
            if self.name_dialog:
                self.name_dialog.dismiss()
            
            # 4. Отправляем на сервер (замени URL на свой)
            self._send_name_to_server(new_name)
            print(f"Имя изменено на: {new_name}")

    def _send_name_to_server(self, name):
        # 1. Получаем токен
        token = self.get_auth_token()
        if not token:
            print("Ошибка: Токен отсутствует")
            return

        # 2. Формируем данные и заголовки
        url = f"{self.base_url}/api/v1/users/update_me"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        params = json.dumps({"username": name})

        # 3. Отправляем асинхронный запрос
        def on_success(request, result):
            print(f"Успех! Имя обновлено: {result}")

        def on_failure(request, result):
            print(f"Ошибка сервера {request.resp_status}: {result}")

        def on_error(request, error):
            print(f"Ошибка сети: {error}")

        UrlRequest(
            url,
            req_body=params,
            req_headers=headers,
            method='PATCH',
            on_success=on_success,
            on_failure=on_failure,
            on_error=on_error
        )

    def show_section_dialog(self, button_text): 
        # Создаем сам диалог
        self.edit_dialog = MDDialog(
            title="Работа в процессе",
            text=f"Здесь будет раздел: {button_text}",
            buttons=[
                MDFlatButton(
                    text="Закрыть", 
                    theme_text_color="Custom", 
                    text_color="red",
                    on_release=lambda x: self.edit_dialog.dismiss()
                ),
            ],
        )
        self.edit_dialog.open()
    
    
class VerifyScreen(BaseScreen):
    def confirm_registration(self):
        base_url = self.app.base_url
        if not base_url.startswith("http"):
            base_url = f"http://{self.app.base_url}"

        code = self.ids.code_field.text.strip()
        user_data = getattr(self.app, 'temp_user_data', None)

        if not code or not user_data:
            return
        
        UrlRequest(
            f"{base_url}/api/v1/auth/verify-and-register?code={code}",
            req_body=json.dumps(user_data),
            req_headers={'Content-Type': 'application/json'},
            on_success=self._on_reg_success,
            on_failure=self._on_reg_error,
            method='POST'
        )
        
    def _on_reg_success(self, req, res):
        token = res.get("access_token")
        if token:
            self.app.save_auth_token(token)
            print("Успешная регистрация")
            self.manager.current = "Hello"
        
    def _on_reg_error(self, req, res):
        if not self.app.check_response(req, res):
            return
        
        print(f"Ошибка: {res}")
        MDSnackbar(
            MDLabel(
                text=str(f"Ошибка данных: {res.get('detail', '')}"),
                theme_text_color="Custom",
                text_color="#ffffff",
            ),
            size_hint_x=0.8,
            pos_hint={"center_x": 0.5},
            y="24dp",
        ).open()

class HelloScreen(BaseScreen):
    touch_start_y = NumericProperty(0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.touch_start_y = touch.y
            return super().on_touch_down(touch)
        return False

    def on_touch_up(self, touch):
        if touch.y - self.touch_start_y > 100: 
            self.manager.transition.direction="up"
            self.manager.current = 'General'
        return super().on_touch_up(touch) 
  
class GeneralScreen(BaseScreen):
    pass
 
class ChatListScreen(BaseScreen):
    def on_enter(self):
        self.app.load_chat_list()
 
class TestListScreen(BaseScreen):
    def on_enter(self):
        Clock.schedule_once(lambda dt: self.load_tests_from_server(), 0.5)

    def load_tests_from_server(self):
        if not self.app.base_url:
            print("Ошибка: base_url пуст, отмена запроса")
            return
        UrlRequest(
            url=f"{self.app.base_url}/api/v1/tests/", 
            on_success=self.on_request_success,
            on_failure=self.on_request_error,
            on_error=self.on_request_error,
            timeout=5
        )

    def on_request_success(self, request, result):
        self.display_tests(result)
        if isinstance(result, list):
            print(f"Данные от сервера {result}")
                  
        elif isinstance(result, dict) and "tests" in result:
            self.display_tests(result["tests"])

    def on_request_error(self, request, error):
        print(f"Ошибка сети: {error}")
        MDSnackbar(MDLabel(text="Ошибка загрузки тестов")).open()

    def display_tests(self, tests):
        grid = self.ids.tests_grid
        grid.clear_widgets() 
        for data in tests:
            card = Factory.TestCard()
            card.title = str(data.get("name", "Без названия") or data.get("title") or "Без названия")
            card.test_id = str(data.get("id", ""))
            card.description = str(data.get("desc", "Нет описания"))
            
            card.bind(on_release=lambda x, tid=card.test_id: self.open_selected_test(tid))
            grid.add_widget(card)
        print(f"Добавлено карточек: {len(grid.children)}") # Проверка в консоли

    def open_selected_test(self, test_id):
        test_screen = self.manager.get_screen("Test")
        test_screen.current_test_id = test_id
        self.manager.current = "Test"
        
class TestScreen(BaseScreen):
    current_test_id = StringProperty("")
    questions = []
    current_index = NumericProperty(0)
    
    user_scores = DictProperty({})
    
    def on_enter(self):
        self.user_scores = {}
        self.current_index = 0
        self.load_full_test()
    
    def load_full_test(self):
        UrlRequest(
            url=f"{self.app.base_url}/api/v1/tests/{self.current_test_id}",
            on_success=self._on_test_loaded,
            on_error=lambda r, e: print(f"Ошибка {e}")
        )
    
    def _on_test_loaded(self, request, result):
        self.questions = result.get("questions", [])
        self.current_index = 0
        self.display_question()
        
    def display_question(self):
        if self.current_index < len(self.questions):
            q_data = self.questions[self.current_index]
            self.ids.question_label.text = q_data['question_text']
            
            self.ids.options_box.clear_widgets() 
            
            for i, opt in enumerate(q_data.get("options", [])):
                # Создаем виджет одной строчкой через Factory
                card = Factory.OptionCard()
                card.option_text = opt
                
                # Назначаем действие при нажатии
                # Используем bind, так как в шаблоне on_release не определен жестко
                card.bind(on_release=lambda x, idx=i: self.process_answer(idx))
                
                self.ids.options_box.add_widget(card)
        else:
            self.show_result()
    
    def process_answer(self, option_index):
        q_data = self.questions[self.current_index]
        scores_list = q_data.get("scores_list", [])
        
        if not scores_list:
            # Если пришел старый формат {"Экстраверт": 10, ...}
            old_scores = q_data.get("scores", {})
            # Превращаем ключи словаря в список для совместимости с индексами
            scores_list = [{k: v} for k, v in old_scores.items()]

        # ПРОВЕРКА: есть ли баллы для этого индекса?
        if scores_list and option_index < len(scores_list):
            answer_scores = scores_list[option_index]
            
            # Суммируем баллы
            for category, value in answer_scores.items():
                self.user_scores[category] = self.user_scores.get(category, 0) + value
        else:
            print(f"WARN: Нет баллов для ответа №{option_index} в вопросе №{self.current_index}")

        self.current_index += 1
        self.display_question()
    


    def show_result(self):
        self.ids.question_label.text = "Ваш результат"
        self.ids.options_box.clear_widgets()
        
        # 1. Считаем победителя
        winner = max(self.user_scores, key=self.user_scores.get) if self.user_scores else "Не определен"
        
        # 2. Создаем карточку через Factory
        # Все параметры (winner_name, description_text) подставятся в шаблон автоматически
        result_card = Factory.ResultCard()
        result_card.winner_name = winner.upper()
        result_card.description_text = "Этот результат основан на ваших ответах в тесте..."
        
        # 3. Добавляем на экран
        self.ids.options_box.add_widget(result_card)

        # 4. Запускаем анимацию
        Animation(opacity=1, duration=0.8, t='out_quad').start(result_card)

    def back_to_tests(self):
        self.manager.current = "Tests"
        
class ProfileScreen(BaseScreen):
    def on_pre_enter(self, *args):
        # 1. Визуальный фидбек начала загрузки
        self.ids.user_name_label.text = "Загрузка..."
        # 2. Вызов метода загрузки
        self.load_user_data()
        if hasattr(self.app, 'user_avatar_path'):
            self.ids.avatar.source = self.app.user_avatar_path
            self.ids.avatar.reload()

    def load_user_data(self):
        # Получаем токен из вашего метода в App
        token = self.app.get_auth_token() 
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Эндпоинт из вашего FastAPI роутера
        url = f"{self.app.base_url}/api/v1/auth/me" 
        
        UrlRequest(
            url,
            req_headers=headers,
            on_success=self._on_profile_success,
            on_failure=self._on_profile_error,
            method='GET'
        )

    def _on_profile_success(self, req, res):
        # res содержит: {"id": 1, "username": "admin", "email": "test@test.com"}
        # Мапим данные на ваши ID в KV-файле
        self.ids.user_name_label.text = res.get("username", "Аноним")
        
        
        # Сохраняем username в глобальные данные приложения, если нужно
        self.app.user_name = res.get("username")

    def _on_profile_error(self, req, res):
        self.ids.user_name_label.text = "Ошибка"
        print(f"Ошибка сервера: {res}")

class DiaryScreen(BaseScreen):
    def on_enter(self):
        # Инициализируем хранилище
        self.store = JsonStore(os.path.join(self.app.user_data_dir, "diary.json"))
        self.load_diary()

    def load_diary(self):
        container = self.ids.diary_container
        container.clear_widgets()
        
        # Сортируем ключи (новые заметки сверху)
        keys = sorted(self.store.keys(), reverse=True)
        
        for key in keys:
            data = self.store.get(key)
            # Создаем элемент через Factory
            item = Factory.DiaryItem()
            
            item.date = str(data.get('date', ''))
            item.text = str(data.get('text', ''))
            item.note_id = key
            
            # Привязываем открытие заметки (срабатывает при клике на карточку)
            item.bind(on_release=lambda x, id=key: self.open_note(id))
            container.add_widget(item)

    def open_note(self, note_id):
        note_screen = self.manager.get_screen("DiaryNote")
        if self.store.exists(note_id):
            data = self.store.get(note_id)
            note_screen.mode = "view"
            note_screen.current_note_id = note_id
            note_screen.ids.note_text.text = str(data.get('text', ''))
            self.manager.current = "DiaryNote"

    # НОВЫЙ МЕТОД ДЛЯ УДАЛЕНИЯ
    def delete_note(self, note_id):
        if self.store.exists(note_id):
            self.store.delete(note_id)
            self.load_diary() # Перезагружаем список после удаления

class DiaryNoteScreen(BaseScreen):
    mode = StringProperty("create")
    current_note_id = StringProperty("")

    def back(self):
        self.manager.current = "Diary"
        self.ids.note_text.text = ""

    def save_and_back(self):
        text = self.ids.note_text.text.strip()
        if not text:
            self.back()
            return

        store = JsonStore(os.path.join(self.app.user_data_dir, "diary.json"))
        
        if self.mode == "create":
            note_id = str(uuid.uuid4())
            date_str = datetime.now().strftime("%d.%m.%Y")
            store.put(note_id, text=text, date=date_str)
        else:
            # Обновляем существующую, сохраняя старую дату
            old_data = store.get(self.current_note_id)
            store.put(self.current_note_id, text=text, date=old_data['date'])
        
        self.back()
            
class SettingScreen(BaseScreen):
    def on_enter(self):
        print("Настройки открыты")

class ChatScreen(BaseScreen):
    chat_id = StringProperty("")

class NotificationScreen(BaseScreen):
    pass

class SafetyScreen(BaseScreen):
    pass

class AboutScreen(BaseScreen):
    pass
          
  
if __name__ == "__main__":
    MainApp().run()