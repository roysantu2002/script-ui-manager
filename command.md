# redis-server

-- python3 -m venv env

# sudo -i -u postgres

# sudo nano /etc/postgresql/15/main/postgresql.conf 

listen_addresses = '*'

sudo service postgresql restart

sudo ufw allow 5432/tcp

# lsof -i :8000

# ps aux | grep 'python manage.py runserver'

# redis-cli -h 192.168.1.103 -p 6379 

# gunicorn --bind 0.0.0.0:8000 backend.wsgi


/etc/nginx/sites-available/myproject
-bash: /etc/nginx/sites-available/myproject: No such file or directory
(env) santu@santu-HP-Compaq-Elite-8300-USDT:~/script-manager$ sudo vim /etc/nginx/sites-available/scriptmanager
(env) santu@santu-HP-Compaq-Elite-8300-USDT:~/script-manager$ sudo ln -s /etc/nginx/sites-available/scriptmanager /etc/nginx/sites-enabled/





