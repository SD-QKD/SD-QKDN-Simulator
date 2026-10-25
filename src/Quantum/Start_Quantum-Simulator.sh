kill -9 $(ps aux | grep qqc.py | grep -v grep | awk '{print $2}')
#cd /home/csg/Repository/MAQAN/Products/trunk/Software/Simulation/QUANTUM
#python3 /home/csg/Repository/MAQAN/Products/trunk/Software/Simulation/QUANTUM/qqc.py
cd /home/qns/QNS/conf
sudo /home/qns/QNS/bin/qqc.py 
