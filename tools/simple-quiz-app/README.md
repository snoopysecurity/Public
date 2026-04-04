# simple-quiz-app


A basic nodejs quiz application that can take JSON data as quiz data and display them locally for a user to complete. Example of a JSON data can be seen here: https://github.com/snoopysecurity/simple-quiz-app/blob/main/data/questions.json

Useful when studying for a topic and need to practice what you learned by leveraging LLM chat .e.g Generate questions and answers in JSON format using a LLM, and give the app a format such as the below and use the application to practice.



```
[
  {
      "question": "What is the gcloud command to set default zone for compute engine server using gcloud cli?",
      "choices": [
          "A. gcloud config set compute/zone us-east-1",
          "B. gcloud config configurations set compute/zone us-east-1a",
          "C. gcloud config set compute/zone us-east1-a",
          "D. gcloud defaults set compute/zone us-east-1"
      ],
      "answer": {
          "correct": "C. gcloud config set compute/zone us-east1-a",
          "explanation": "The gcloud command to set the default zone for compute engine is gcloud config set compute/zone us-east1-a. Hence, C is the correct answer."
      }
  }
]
```
