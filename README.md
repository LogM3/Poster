### Описание проекта:

Данный проект представляет собой социальную сеть, в которой возможно создание/просмотр/редактирование постов, авторизация.
Также этот проект покрыт тестами и имеет собственный API.

### Как запустить проект:

Клонировать проект

```
git clone https://https://github.com/LogM3/poster.git
```

Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
```

```
source env/bin/activate
```

Установить зависимости из файла requirements.txt:

```
python3 -m pip install --upgrade pip
```

```
pip install -r requirements.txt
```

Выполнить миграции:

```
python3 manage.py migrate
```

Запустить проект:

```
python3 manage.py runserver
```