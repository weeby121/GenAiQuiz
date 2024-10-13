import os
from dotenv import load_dotenv
import pygame
import sys
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Access the Gemini API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY not found in environment variables.")
    sys.exit(1)

# Configure the Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Create the model configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 150,  
    "response_mime_type": "text/plain",
}

# Initialize the Generative Model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Start a chat session
chat_session = model.start_chat(
    history=[]
)

# Initialize Pygame
pygame.init()

# Display settings
WIDTH, HEIGHT = 800, 600
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("GenAI Quiz")

# Fonts
FONT = pygame.font.SysFont("Arial", 24)
BIG_FONT = pygame.font.SysFont("Arial", 40)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

def main_menu():
    input_box = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 20, 200, 40)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the user clicked on the input_box rect.
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        topic = text.strip()
                        if topic:
                            return topic
                        else:
                            # Optionally display a message to enter a valid topic
                            pass
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        WINDOW.fill(WHITE)
        # Render the input box
        txt_surface = FONT.render(text, True, color)
        width = max(200, txt_surface.get_width()+10)
        input_box.w = width
        WINDOW.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.draw.rect(WINDOW, color, input_box, 2)

        # Render instructions
        instruction = BIG_FONT.render("Enter Quiz Topic:", True, BLACK)
        WINDOW.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 - 80))

        pygame.display.flip()

def generate_quiz(topic, num_questions=5):
    questions = []
    prompt_template = (
        f"Generate a multiple-choice question about {topic} along with four options and indicate the correct answer. "
        f"Format strictly as follows:\n"
        f"Question: <question>\n"
        f"1. <option1>\n"
        f"2. <option2>\n"
        f"3. <option3>\n"
        f"4. <option4>\n"
        f"Answer: <correct_option_number>\n"
        f"Ensure there are no additional lines or text."
    )

    for i in range(num_questions):
        try:
            # Send the prompt to the chat session
            response = chat_session.send_message(prompt_template)
            generated_text = response.text.strip()
            
            # Print the generated text for debugging
            print(f"\n--- Generated Question {i+1} ---")
            print(generated_text)
            print("--- End of Generated Question ---\n")

            # Parse the generated text
            question, options, answer = parse_generated_text(generated_text)

            if question and options and answer:
                questions.append({
                    "question": question,
                    "options": options,
                    "answer": options[answer - 1]  # Convert to zero-based index
                })
            else:
                print(f"Failed to parse generated question {i+1}.")
        except Exception as e:
            print(f"Error generating question {i+1}: {e}")

    return questions


def parse_generated_text(text):
    """
    Parses the generated text to extract question, options, and the correct answer.
    Expects the format:
    Question: <question>
    1. <option1>
    2. <option2>
    3. <option3>
    4. <option4>
    Answer: <correct_option_number>
    """
    lines = text.split('\n')
    if len(lines) < 6:
        print("Generated text does not have enough lines.")
        return None, None, None

    try:
        question_line = lines[0]
        if not question_line.startswith("Question:"):
            print("Question line does not start with 'Question:'.")
            return None, None, None
        question = question_line.replace("Question:", "").strip()

        options = []
        for i in range(1, 5):
            option_line = lines[i]
            if not option_line.startswith(f"{i}."):
                print(f"Option {i} line does not start with '{i}.'")
                return None, None, None
            option = option_line.split('.', 1)[1].strip()
            options.append(option)

        answer_line = lines[5]
        if not answer_line.startswith("Answer:"):
            print("Answer line does not start with 'Answer:'.")
            return None, None, None
        answer_str = answer_line.replace("Answer:", "").strip()
        answer = int(answer_str)

        if answer < 1 or answer > 4:
            print("Answer number out of range.")
            return None, None, None

        return question, options, answer
    except Exception as e:
        print(f"Error parsing generated text: {e}")
        return None, None, None

def run_quiz(questions):
    current_question = 0
    score = 0
    selected_option = None

    while current_question < len(questions):
        question_data = questions[current_question]
        question_text = question_data["question"]
        options = question_data["options"]
        correct_answer = question_data["answer"]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, option in enumerate(options):
                    option_rect = pygame.Rect(100, 200 + idx*60, 600, 50)
                    if option_rect.collidepoint(event.pos):
                        selected_option = idx
                        if options[selected_option] == correct_answer:
                            score += 1
                        current_question += 1

        WINDOW.fill(WHITE)

        # Display question
        rendered_question = FONT.render(f"Q{current_question + 1}: {question_text}", True, BLACK)
        WINDOW.blit(rendered_question, (50, 50))

        # Display options
        for idx, option in enumerate(options):
            option_rect = pygame.Rect(100, 200 + idx*60, 600, 50)
            pygame.draw.rect(WINDOW, pygame.Color('lightgray'), option_rect)
            rendered_option = FONT.render(option, True, BLACK)
            WINDOW.blit(rendered_option, (option_rect.x + 10, option_rect.y + 10))

        pygame.display.flip()

    # Quiz End Screen
    end_quiz(score, len(questions))

def end_quiz(score, total):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                pygame.quit()
                sys.exit()

        WINDOW.fill(WHITE)
        result_text = BIG_FONT.render(f"Your Score: {score} / {total}", True, BLACK)
        WINDOW.blit(result_text, (WIDTH//2 - result_text.get_width()//2, HEIGHT//2 - 50))

        instruction = FONT.render("Press any key or click to exit.", True, BLACK)
        WINDOW.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 10))

        pygame.display.flip()

def main():
    topic = main_menu()
    print(f"Selected Topic: {topic}")
    questions = generate_quiz(topic, num_questions=5)
    if questions:
        run_quiz(questions)
    else:
        print("Failed to generate quiz questions.")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
