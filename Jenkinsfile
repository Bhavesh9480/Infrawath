pipeline {
agent any

```
stages {

    stage('Checkout') {
        steps {
            echo 'Checking out source code...'
            checkout scm
        }
    }

    stage('Verify Workspace') {
        steps {
            echo 'Current directory:'
            sh 'pwd'

            echo 'Workspace contents:'
            sh 'ls -la'

            echo 'Project structure:'
            sh 'find . -maxdepth 2 -type f | sort'
        }
    }
}

post {
    success {
        echo 'Pipeline executed successfully.'
    }

    failure {
        echo 'Pipeline failed.'
    }

    always {
        cleanWs()
    }
}
```

}
