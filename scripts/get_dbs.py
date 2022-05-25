import os

ip_list = os.environ.get("IP_LIST").split(";")

copy_db_command = "scp -i ~/.ssh/id_rsa ubuntu@HOST:/home/ubuntu/raas/db/app.db ../data/raas_dbs/NUMBER-app.db"
copy_timeouts_command = "scp -i ~/.ssh/id_rsa ubuntu@HOST:/home/ubuntu/raas/eval/raas_timeout_dois.txt ../data/raas_timeouts/NUMBER-timeout-dois.txt"

counter = 0
for ip_addr in ip_list:
    ip_db_command = copy_db_command.replace("HOST", ip_addr).replace("NUMBER", str(counter))
    ip_timeout_command = copy_timeouts_command.replace("HOST", ip_addr).replace("NUMBER", str(counter))

    counter += 1
    os.system(ip_db_command)
    os.system(ip_timeout_command)
