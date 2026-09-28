#!/data/data/com.termux/files/usr/bin/bash
cd ~/nexus
termux-wake-lock
pkill -f "uvicorn core.api" 2>/dev/null
pkill -f "cloudflared tunnel" 2>/dev/null
sleep 1
nohup uvicorn core.api:app --host 127.0.0.1 --port 8000 > logs_api.txt 2>&1 &
nohup cloudflared tunnel --url http://localhost:8000 > logs_tunnel.txt 2>&1 &
sleep 12
URL=$(grep -o "https://[a-z0-9-]*\.trycloudflare\.com" logs_tunnel.txt | head -1)
echo "NEXUS PUBLIC URL: ${URL:-still starting, check logs_tunnel.txt}"
