
Мобильное приложение Сопрано
Инструкция по сборке

открыть google colab https://colab.research.google.com/
создать блокнот указать и выполнить команды
!pip install buildozer
!pip install --upgrade "Cython<3.0"
!sudo apt-get install -y \
    python3-pip \
    build-essential \
    git \
    python3 \
    python3-dev \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev

!sudo apt-get install -y \
    libgstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good

!sudo apt-get install build-essential libsqlite3-dev sqlite3 bzip2 libbz2-dev zlib1g-dev libssl-dev openssl libgdbm-dev libgdbm-compat-dev liblzma-dev libreadline-dev libncursesw5-dev libffi-dev uuid-dev libffi6

!sudo apt-get install libffi-dev

!apt-get install -y autoconf automake libtool pkg-config

!buildozer init

После выполнения этой команды "!buildozer init" заменить файл на мой


перед выполнением сборки отчистить стандартные файлы окружения и перенести все файлы Client в окружение
!buildozer -v android debug


После сборки нужно запустить сервер будет показано в ролике в презентации

Предварительно для сервера нужно установить зависимости(requirements.txt) в случае ошибок установить reqB.txt
