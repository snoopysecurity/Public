async function loadQuestions() {
    const response = await fetch('/api/questions');
    const questions = await response.json();
    return questions;
}

function renderQuiz(questions) {
    const quizContainer = document.getElementById('quiz-container');
    quizContainer.innerHTML = '';

    questions.forEach((question, index) => {
        const questionContainer = document.createElement('div');
        questionContainer.classList.add('bg-gray-50', 'p-4', 'rounded-lg', 'shadow', 'border', 'border-gray-200', 'mb-6'); // Improved styling

        const questionTitle = document.createElement('h3');
        questionTitle.textContent = `Question ${index + 1}: ${question.question}`;
        questionTitle.classList.add('font-semibold', 'text-lg', 'mb-4'); // Styling for question title
        questionContainer.appendChild(questionTitle);

        question.choices.forEach((choice) => {
            const choiceLabel = document.createElement('label');
            choiceLabel.classList.add('block', 'cursor-pointer', 'p-2', 'rounded', 'hover:bg-blue-100', 'mb-2'); // Styling for choice labels
            
            const choiceInput = document.createElement('input');
            choiceInput.type = 'radio';
            choiceInput.name = `question${index}`;
            choiceInput.value = choice; // Keep choice value as is
            choiceInput.classList.add('mr-2'); // Space between radio and label text

            choiceLabel.appendChild(choiceInput);
            choiceLabel.appendChild(document.createTextNode(choice));
            questionContainer.appendChild(choiceLabel);
        });

        const submitButton = document.createElement('button');
        submitButton.textContent = 'Submit Answer';
        submitButton.classList.add('mt-4', 'bg-blue-500', 'text-white', 'py-2', 'px-6', 'rounded', 'hover:bg-blue-600', 'transition', 'duration-200'); // Improved styling
        submitButton.addEventListener('click', () => checkAnswer(index, question.answer.correct)); // Pass the correct answer
        questionContainer.appendChild(submitButton);

        const resultDiv = document.createElement('div');
        resultDiv.classList.add('result', 'mt-2', 'font-semibold'); // Added margin for spacing
        questionContainer.appendChild(resultDiv);

        quizContainer.appendChild(questionContainer);
    });
}

function checkAnswer(questionIndex, correctAnswer) {
    const selectedOption = document.querySelector(`input[name="question${questionIndex}"]:checked`);
    const resultDiv = document.querySelectorAll('.result')[questionIndex];

    if (!selectedOption) {
        resultDiv.textContent = 'Please select an answer!';
        resultDiv.style.color = 'orange';
    } else if (selectedOption.value === correctAnswer) {
        resultDiv.textContent = 'Correct!';
        resultDiv.style.color = 'green';
    } else {
        resultDiv.textContent = 'Incorrect. Try again!';
        resultDiv.style.color = 'red';
    }
}

loadQuestions().then(renderQuiz).catch(error => console.error('Error loading questions:', error));
