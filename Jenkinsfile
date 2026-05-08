pipeline {
    agent any

    options {
        disableConcurrentBuilds()
    }

    environment {
        APP_URL = 'http://localhost:8081'
        TEST_APP_URL = 'http://assignment-store-app:8000'
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
                docker run --rm \
                  -v "$PWD:/workspace" \
                  -w /workspace \
                  alpine:3.20 \
                  sh -c "rm -rf selenium-tests"
                git clone "$TEST_REPO_URL" selenium-tests
                docker run --rm \
                  --network "$COMPOSE_PROJECT_NAME"_default \
                  curlimages/curl:8.10.1 \
                  -fsS "$TEST_APP_URL/health"
                docker run --rm \
                  --shm-size=2g \
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
            script {
                def pushedByEmail = sh(
                    script: 'git log -1 --pretty=format:%ae',
                    returnStdout: true
                ).trim()

                if (pushedByEmail) {
                    emailext(
                        to: pushedByEmail,
                        subject: "Selenium test results: ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                        body: """
Build result: ${currentBuild.currentResult}
Job: ${env.JOB_NAME} #${env.BUILD_NUMBER}
Commit: ${env.GIT_COMMIT}
Application URL: ${env.APP_URL}

Selenium test results are attached and published in Jenkins.
""",
                        attachmentsPattern: 'selenium-tests/target/surefire-reports/*.xml',
                        attachLog: true
                    )
                } else {
                    echo 'No commit author email found; skipping test result email.'
                }
            }
        }
    }
}
