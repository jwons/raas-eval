import os

ip_list = os.environ.get("IP_LIST").split(";")[0:2]

copy_command = "scp -i ~/.ssh/id_rsa ubuntu@HOST:/home/ubuntu/raas/db/app.db ../data/raas_dbs/NUMBER-app.db"

counter = 0
for ip_addr in ip_list:
    ip_command = copy_command.replace("HOST", ip_addr).replace("NUMBER", str(counter))
    counter += 1
    os.system(ip_command)