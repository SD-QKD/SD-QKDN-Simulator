kill -9 $(ps aux | grep qne | grep -v grep | awk '{print $2}')
cd /home/qns/Desktop/QNE2
sudo ../qne -d
