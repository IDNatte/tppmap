# TPPMAP

### Development

- pastikan python terinstal (python versi `>= 3.10, < 3.12`) menggunakan python
- fork repository dan clone ke local machine
- buat python environment dengan perintan `python -m venv .venv --upgrade-deps`
- lalu masuk ke python environment lokal yang sudah di buat
- install dependencies dengan mengetikkan `pip install -r scrip/requirement.txt`
- untuk menjalankan dev server ketikkan terlebih dahulu jalankan perintah
  - `$env:FLASK_APP = "app:init_app"; $env:FLASK_ENV = "development"` untuk windows powershell,
  - `export FLASK_APP=app:init_app && export FLASK_ENV=development` untuk linux dan wsl.
- sebelum migrasi server, pastikan database `tppmap / database yang mau di buat` sudah anda buat pada mysql, atau mariadb
- setting username & password database pada file `app/config/config.py`
  - SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://<username>:<passwword>@localhost/<tppmap / atau database yang sudah baru di buat>'
- migrasi server terlebih dahulu
  - jalankan perintah `flask db upgrade` untuk membuat migrasi server untuk membangun table.
- jalankan aplikasi dengan perintah `flask run`
