#cloud-config

package_update: true
package_upgrade: true

packages:
  - git
  - python3-pip
  - python3-venv
  - iptables-persistent

write_files:
  - path: /etc/systemd/system/santos-pegasus.service
    content: |
      [Unit]
      Description=Santos Pegasus AI Agent
      After=network.target

      [Service]
      User=ubuntu
      WorkingDirectory=/home/ubuntu/santos-pegasus
      ExecStart=/home/ubuntu/santos-pegasus/venv/bin/python -m streamlit run src/app.py --server.port ${app_port} --server.address 0.0.0.0
      Restart=always
      RestartSec=3

      [Install]
      WantedBy=multi-user.target

runcmd:
  # 1. Abrir puerto en el firewall interno de iptables
  - iptables -I INPUT -p tcp -m tcp --dport ${app_port} -j ACCEPT
  - netfilter-persistent save

  # 2. Clonar el repositorio
  - cd /home/ubuntu
  - git clone ${github_repo_url} santos-pegasus
  - chown -R ubuntu:ubuntu santos-pegasus

  # 3. Configurar entorno y dependencias
  - cd santos-pegasus
  - sudo -u ubuntu python3 -m venv venv
  - sudo -u ubuntu venv/bin/pip install -r requirements.txt

  # 4. Inyectar API Key de Google
  - echo "GOOGLE_API_KEY=${google_api_key}" > .env
  - chown ubuntu:ubuntu .env

  # 5. Construir base vectorial (FAISS)
  # Como puede tardar varios minutos, lo ejecutamos como usuario ubuntu
  - sudo -u ubuntu venv/bin/python src/build_vectorstore.py

  # 6. Activar e iniciar el servicio
  - systemctl daemon-reload
  - systemctl enable santos-pegasus.service
  - systemctl start santos-pegasus.service
