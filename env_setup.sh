#!/bin/bash -l

PROJECT_DIR_BASE=$(cd $(dirname $0); pwd -P)
echo "Project root path: $PROJECT_DIR_BASE"
SUBJECT_PROJECTS_PATH=$PROJECT_DIR_BASE/subject_projects
mkdir -p $SUBJECT_PROJECTS_PATH
cd $SUBJECT_PROJECTS_PATH
echo "Subject projects path: $(pwd -P)"

echo "Start clone the subject projects..."

git clone https://github.com/ansible/ansible.git
git clone https://github.com/psf/black.git
git clone https://github.com/cookiecutter/cookiecutter.git
git clone https://github.com/tiangolo/fastapi.git
git clone https://github.com/httpie/cli.git
git clone https://github.com/keras-team/keras.git
git clone https://github.com/spotify/luigi.git
git clone https://github.com/matplotlib/matplotlib.git
git clone https://github.com/pandas-dev/pandas.git
git clone https://github.com/cool-RR/PySnooper.git
git clone https://github.com/sanic-org/sanic.git
git clone https://github.com/scrapy/scrapy.git
git clone https://github.com/explosion/spaCy.git
git clone https://github.com/nvbn/thefuck.git
git clone https://github.com/tornadoweb/tornado.git
git clone https://github.com/tqdm/tqdm.git
git clone https://github.com/ytdl-org/youtube-dl.git

echo "Finish clone the subject projects!"