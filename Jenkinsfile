pipeline {
    agent {
        docker {
            image 'python:3.8'
            args '-u root:sudo -v $HOME/workspace/myproject:/myproject'
        }
    }
    stages {
        stage('build') {
            steps {
                sh 'su root'
                sh 'apt-get update -y'
                sh 'apt-get upgrade -y'
                sh 'apt-get install -y sqlcipher'
                sh 'apt-get install -y libsqlcipher-dev'
                sh 'python3 --version'
                sh 'pip3 install -r requirements.txt'
            }
        }
        stage("test") {
            steps {
                sh 'python3 -m pytest tests'
            }
        }
    }
}