# Deployment Guide

Guia completo para deployar a aplicação Controle Financeiro em produção.

## 📋 Pré-requisitos

- Docker & Docker Compose (v1.29+)
- Servidor com mínimo 2GB RAM
- 10GB espaço em disco
- HTTPS/TLS certificate (recomendado)

## 🚀 Deployment com Docker Compose

### 1. Prepare o servidor

```bash
# SSH no servidor
ssh user@your-server.com

# Clone repositório
git clone <repo> controle-financeiro
cd controle-financeiro

# Configure permissões
mkdir -p backend/data
chmod 755 backend/data
```

### 2. Configure variáveis de ambiente

```bash
# Copy template
cp .env.example .env

# Edit com valores de produção
nano .env
```

**Valores críticos a alterar**:
```env
ENVIRONMENT=production
JWT_SECRET_KEY=<gerar-chave-aleatoria-32-chars>
CORS_ORIGINS=https://seu-dominio.com
DATABASE_URL=sqlite:////data/controle_financeiro.db
VITE_API_BASE_URL=https://seu-dominio.com/api
```

### 3. Gerar JWT Secret seguro

```bash
# Opção 1: Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Opção 2: OpenSSL
openssl rand -base64 32

# Copiar valor e colocar em .env
JWT_SECRET_KEY=<valor-gerado>
```

### 4. Build e deploy

```bash
# Build images
docker-compose build

# Start serviços (background)
docker-compose up -d

# Verificar status
docker-compose ps

# Ver logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Verificar saúde

```bash
# Health check backend
curl http://localhost:8000/health

# Health check frontend
curl http://localhost/health.html

# API documentation
curl http://localhost:8000/docs
```

## 🔐 HTTPS/TLS Setup

### Com Nginx Reverse Proxy

Criar arquivo `nginx-prod.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name seu-dominio.com;
    return 301 https://$server_name$request_uri;
}
```

### Usar Certbot para Let's Encrypt

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d seu-dominio.com

# Auto-renew (cron job)
sudo certbot renew --quiet
```

## 📊 Backup & Restore

### Backup Automático

Criar script `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/controle-financeiro"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup banco de dados
docker cp controle-financeiro-backend:/data/controle_financeiro.db \
    $BACKUP_DIR/controle_financeiro_$TIMESTAMP.db

# Manter últimos 30 dias
find $BACKUP_DIR -name "*.db" -mtime +30 -delete

echo "Backup criado: $BACKUP_DIR/controle_financeiro_$TIMESTAMP.db"
```

Agendar com crontab:

```bash
# Backup diário às 2AM
0 2 * * * /home/user/controle-financeiro/backup.sh >> /var/log/controle-backup.log 2>&1
```

### Restore

```bash
# Stop aplicação
docker-compose down

# Restore banco
docker cp /backups/controle-financeiro/controle_financeiro_20240101_020000.db \
    controle-financeiro-backend:/data/controle_financeiro.db

# Start aplicação
docker-compose up -d
```

## 🐛 Monitoring & Logs

### Healthcheck automático

```bash
# Monitorar status dos containers
watch docker-compose ps

# Ver logs em tempo real
docker-compose logs -f

# Filtrar por serviço
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Usando ELK Stack (opcional)

Configure filebeat para enviar logs para ElasticSearch:

```yaml
# docker-compose.yml - adicionar ELK services
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"
```

## 🔄 Updates & Patches

### Atualizar aplicação

```bash
# Pull últimas mudanças
git pull origin main

# Rebuild images
docker-compose build --no-cache

# Restart serviços (zero-downtime possível com load balancer)
docker-compose up -d --no-deps --build backend
docker-compose up -d --no-deps --build frontend
```

### Atualizar dependências

```bash
# Backend
cd backend
pip install --upgrade -r requirements.txt

# Frontend
cd frontend
npm update
```

## 📈 Performance Tuning

### Nginx caching

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=100m inactive=60m;

location /api/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_bypass $http_cache_control;
}
```

### Database optimization

```bash
# Verificar índices
docker exec controle-financeiro-backend sqlite3 /data/controle_financeiro.db \
    "SELECT name FROM sqlite_master WHERE type='index';"

# Analyze queries
docker exec controle-financeiro-backend sqlite3 /data/controle_financeiro.db \
    "EXPLAIN QUERY PLAN SELECT * FROM payments WHERE user_id=1;"
```

### Memory limits

Editar `docker-compose.yml`:

```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 1G
      reservations:
        memory: 512M

frontend:
  deploy:
    resources:
      limits:
        memory: 512M
      reservations:
        memory: 256M
```

## 🚨 Troubleshooting

### Backend não inicia

```bash
# Ver logs detalhados
docker logs controle-financeiro-backend

# Verificar database
docker exec controle-financeiro-backend sqlite3 /data/controle_financeiro.db ".tables"

# Rebuild
docker-compose build --no-cache backend
```

### Frontend não carrega

```bash
# Verificar nginx config
docker exec controle-financeiro-frontend nginx -t

# Reload nginx
docker exec controle-financeiro-frontend nginx -s reload

# Ver logs
docker logs controle-financeiro-frontend
```

### Conexão entre serviços

```bash
# Testar conectividade
docker exec controle-financeiro-frontend curl http://backend:8000/health

# Verificar rede
docker network inspect controle-financeiro_app-network
```

## 📋 Checklist de Produção

- [ ] HTTPS/TLS configurado
- [ ] JWT_SECRET_KEY alterado
- [ ] CORS_ORIGINS configurado para domínio
- [ ] Backup automático agendado
- [ ] Monitoramento/alertas configurado
- [ ] Rate limiting habilitado
- [ ] CSRF protection ativo
- [ ] WAF (Web Application Firewall) em front
- [ ] Firewall permite apenas ports 80/443
- [ ] SELinux/AppArmor configurado
- [ ] Logs centralizados
- [ ] Disaster recovery plan

## 🔒 Security Hardening

### Firewall rules

```bash
# Allow SSH, HTTP, HTTPS only
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Rate limiting (Nginx)

```nginx
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/auth/login {
    limit_req zone=login burst=3 nodelay;
    proxy_pass http://backend:8000;
}
```

### Security headers

```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
```

## 📞 Support

Para issues em produção:
1. Verificar logs: `docker-compose logs -f`
2. Verificar recursos: `docker stats`
3. Verificar connectivity: `docker network inspect`
4. Verificar database: `sqlite3 /path/to/db ".schema"`

---

**Última atualização**: Junho 2024
**Versão**: 1.0.0
