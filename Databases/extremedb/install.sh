mkdir dstree/out
sudo chmod 777 dstree/out

echo "Create account on https://www.mcobject.com/software_eval/"
echo "Once you get an email, please copy paste the link here:"
read line

wget "$line"
mv index.html extremedb.tar.gz
tar xvzf extremedb.tar.gz
rm extremedb.tar.gz

cd eXtremeDB/
make all
cd target/python/
python setup.py install --user