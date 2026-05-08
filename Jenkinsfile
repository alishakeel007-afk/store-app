pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        APP_URL = 'http://localhost:8081'
        TEST_APP_URL = 'http://app:8000'
        TEST_REPO_URL = 'https://github.com/alishakeel007-afk/store-app-selenium-tests.git'
        COMPOSE_PROJECT_NAME = 'store-app'
    }

    stages {
        stage('Checkout Application') {
            steps {
                checkout scm
            }
        }

        stage('Start Application') {
            steps {
                sh '''
                docker compose -p "$COMPOSE_PROJECT_NAME" down --remove-orphans || true
                docker compose -p "$COMPOSE_PROJECT_NAME" up -d --build
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                for i in $(seq 1 30); do
                  if curl -fsS "$APP_URL/health"; then
                    exit 0
                  fi
                  sleep 2
                done
                docker compose -p "$COMPOSE_PROJECT_NAME" logs
                exit 1
                '''
            }
        }

        stage('Run Selenium Tests') {
            steps {
                sh '''
                rm -rf selenium-tests
                git clone "$TEST_REPO_URL" selenium-tests
                docker run --rm \
                  -e APP_URL="$TEST_APP_URL" \
                  -e MANAGER_PASSWORD="admin123" \
                  -v "$PWD/selenium-tests:/tests" \
                  -w /tests \
                  --network "$COMPOSE_PROJECT_NAME"_default \
                  markhobson/maven-chrome:jdk-17 \
                  mvn test
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'selenium-tests/target/surefire-reports/*.xml'
            sh 'docker compose -p "$COMPOSE_PROJECT_NAME" ps || true'
        }
        success {
            emailext(
                subject: "Selenium tests passed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build passed. Application URL: ${env.APP_URL}",
                recipientProviders: [developers(), requestor()]
            )
        }
        failure {
            emailext(
                subject: "Selenium tests failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: "Build failed. Check Jenkins console output and test report.",
                recipientProviders: [developers(), requestor()]
            )
        }
    }
}
