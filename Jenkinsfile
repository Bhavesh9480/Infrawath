pipeline {
    agent any

    environment {
        COMPOSE_PROJECT_NAME = 'infrawatch'
    }

    stages {
        stage('Git Checkout') {
            steps {
                echo 'Checking out source code...'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Setting up Python virtual environment & installing dependencies...'
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements.txt
                '''
            }
        }

        stage('Run PyTest') {
            steps {
                echo 'Executing test suite...'
                sh '''
                    . venv/bin/activate
                    PYTHONPATH=. pytest backend/
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building backend Docker image...'
                sh 'docker compose build'
            }
        }

        stage('Stop Old Container') {
            steps {
                echo 'Stopping and removing old containers...'
                sh 'docker compose down'
            }
        }

        stage('Deploy New Container') {
            steps {
                echo 'Deploying new container...'
                sh 'docker compose up -d'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up workspace...'
            cleanWs()
        }
        success {
            echo 'InfraWatch pipeline completed successfully! Service deployed.'
        }
        failure {
            echo 'Pipeline failed. Check stages for error details.'
        }
    }
}
