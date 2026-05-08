pipeline {
    agent any

    environment {
        APP_URL = 'http://localhost:8081'
        TEST_REPO_URL = 'https://github.com/alishakeel007-afk/store-app-selenium-tests.git'
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
                docker compose down || true
                docker compose up -d --build
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
                docker compose logs
                exit 1
                '''
            }
        }

        stage('Run Selenium Tests') {
            steps {
                sh '''
                rm -rf selenium-tests
                git clone "$TEST_REPO_URL" selenium-tests
                docker run --rm --network host \
                  -e APP_URL="$APP_URL" \
                  -v "$PWD/selenium-tests:/tests" \
                  -w /tests \
                  markhobson/maven-chrome:maven-3.9.9-eclipse-temurin-21 \
                  mvn test
                '''
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'selenium-tests/target/surefire-reports/*.xml'
            sh 'docker compose ps || true'
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
